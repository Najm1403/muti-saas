# services/subscription_service.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError, ValidationError
from models.plan import Plan
from models.subscription import BillingCycle, Subscription, SubscriptionStatus
from repositories.plan_repository import PlanRepository
from repositories.subscription_payment_repository import SubscriptionPaymentRepository
from repositories.subscription_repository import SubscriptionRepository
from repositories.tenant_repository import TenantRepository
from schemas.subscription import (
    BillingPreviewResponse,
    PaymentResponse,
    RecordPaymentRequest,
    SubscriptionCreate,
    SubscriptionExtendGraceRequest,
    SubscriptionExtendTrialRequest,
    SubscriptionResponse,
    SubscriptionUpdate,
    SubscriptionWaiveRequest,
)

# Statuses evaluate_and_sync() will never move away from automatically — a
# platform admin put the subscription there on purpose (suspension for a
# policy violation, or a final cancellation), so a lapse timer must never
# silently override that decision.
_MANUAL_STATUSES = frozenset({SubscriptionStatus.SUSPENDED, SubscriptionStatus.CANCELLED})


class SubscriptionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SubscriptionRepository(db)
        self.payment_repo = SubscriptionPaymentRepository(db)
        self.plan_repo = PlanRepository(db)
        self.tenant_repo = TenantRepository(db)

    # ----------------------------------------------------------------
    # CREATE — assign plan to tenant
    # ----------------------------------------------------------------

    async def create(self, data: SubscriptionCreate) -> SubscriptionResponse:
        """Start a new subscription for a tenant.

        Raises ConflictError if the tenant already has an active/trial subscription.
        """
        tenant = await self.tenant_repo.get_by_id(data.tenant_id)
        if not tenant:
            raise NotFoundError("Tenant not found.")

        plan = await self.plan_repo.get_by_id(data.plan_id)
        if not plan or not plan.is_active:
            raise NotFoundError("Plan not found or inactive.")

        existing = await self.repo.get_active_for_tenant(data.tenant_id)
        if existing:
            raise ConflictError("Tenant already has an active subscription. Cancel it first.")

        now = datetime.now(timezone.utc)
        trial_ends_at = None

        if data.status == SubscriptionStatus.TRIAL and data.trial_days > 0:
            trial_ends_at = now + timedelta(days=data.trial_days)
            expires_at = trial_ends_at
        else:
            expires_at = _next_expiry(now, data.billing_cycle)

        sub = await self.repo.create(
            tenant_id=data.tenant_id,
            plan_id=data.plan_id,
            billing_cycle=data.billing_cycle,
            status=data.status,
            started_at=now,
            expires_at=expires_at,
            trial_ends_at=trial_ends_at,
            discount_pct=data.discount_pct,
        )
        await self.db.commit()
        return SubscriptionResponse.model_validate(sub)

    # ----------------------------------------------------------------
    # READ
    # ----------------------------------------------------------------

    async def get(self, id: UUID) -> SubscriptionResponse:
        sub = await self.repo.get_by_id(id)
        if not sub:
            raise NotFoundError("Subscription not found.")
        sub = await self.evaluate_and_sync(sub)
        return SubscriptionResponse.model_validate(sub)

    async def list(
        self,
        status: SubscriptionStatus | None = None,
        tenant_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SubscriptionResponse]:
        subs = await self.repo.list(status=status, tenant_id=tenant_id, skip=skip, limit=limit)
        subs = [await self.evaluate_and_sync(s) for s in subs]
        return [SubscriptionResponse.model_validate(s) for s in subs]

    # ----------------------------------------------------------------
    # AUTOMATIC LIFECYCLE — evaluated on read, no scheduler required
    # ----------------------------------------------------------------

    async def evaluate_and_sync(self, sub: Subscription) -> Subscription:
        """Advance `sub.status` to reflect elapsed time, if needed.

        This is the entire "automatic" half of the non-payment lifecycle —
        there is no cron/scheduled job in this app, so instead every read
        path that touches a subscription (this service's get()/list(), the
        POS device-auth guard, and GET /auth/me for the tenant dashboard
        banner) calls this first. In practice a tenant's subscription is
        touched constantly (every POS heartbeat, every dashboard login), so
        the transition happens within moments of actually crossing a
        threshold — not "eventually, next time a cron runs."

        ACTIVE/TRIAL, past expires_at, within grace_period_days -> PAST_DUE
            (a warning stage only — nothing else in the app restricts access
            for PAST_DUE; see api/v1/pos/_guards.py)
        PAST_DUE (or ACTIVE/TRIAL that skipped straight past grace), past
        expires_at + grace_period_days -> SUSPENDED (blocks POS)

        SUSPENDED and CANCELLED are never touched here — those are decisions
        a human made (suspend / cancel / waive / record-payment), not a
        timer, and a timer must never quietly reverse a human decision.
        Committed immediately: this is a monotonic, idempotent transition
        driven only by wall-clock time, so there's nothing to roll back.
        """
        if sub.status in _MANUAL_STATUSES:
            return sub
        now = datetime.now(timezone.utc)
        grace_end = sub.expires_at + timedelta(days=sub.grace_period_days)
        new_status = sub.status
        if now > grace_end:
            new_status = SubscriptionStatus.SUSPENDED
        elif now > sub.expires_at:
            new_status = SubscriptionStatus.PAST_DUE
        elif sub.status == SubscriptionStatus.PAST_DUE:
            # expires_at was pushed back out (e.g. a manual edit) without an
            # explicit status change — no longer overdue.
            new_status = SubscriptionStatus.ACTIVE
        if new_status != sub.status:
            sub.status = new_status
            await self.db.commit()
            await self.db.refresh(sub)
        return sub

    # ----------------------------------------------------------------
    # STATUS TRANSITIONS
    # ----------------------------------------------------------------

    async def suspend(self, id: UUID) -> SubscriptionResponse:
        sub = await _get_or_404(self.repo, id)
        if sub.status == SubscriptionStatus.CANCELLED:
            raise ValidationError("Cannot suspend a cancelled subscription.")
        sub = await self.repo.update(id, status=SubscriptionStatus.SUSPENDED)
        await self.db.commit()
        return SubscriptionResponse.model_validate(sub)

    async def reactivate(self, id: UUID) -> SubscriptionResponse:
        sub = await _get_or_404(self.repo, id)
        if sub.status not in (SubscriptionStatus.SUSPENDED, SubscriptionStatus.EXPIRED):
            raise ValidationError("Only suspended or expired subscriptions can be reactivated.")
        sub = await self.repo.update(id, status=SubscriptionStatus.ACTIVE)
        await self.db.commit()
        return SubscriptionResponse.model_validate(sub)

    async def cancel(self, id: UUID) -> SubscriptionResponse:
        sub = await _get_or_404(self.repo, id)
        if sub.status == SubscriptionStatus.CANCELLED:
            raise ValidationError("Subscription is already cancelled.")
        sub = await self.repo.update(
            id,
            status=SubscriptionStatus.CANCELLED,
            cancelled_at=datetime.now(timezone.utc),
        )
        await self.db.commit()
        return SubscriptionResponse.model_validate(sub)

    async def extend_grace(self, id: UUID, data: SubscriptionExtendGraceRequest) -> SubscriptionResponse:
        """Adds `data.extend_days` to this subscription's grace_period_days.

        The manual half of the grace period, alongside evaluate_and_sync()'s
        automatic countdown — a platform admin can give one specific tenant
        more breathing room (e.g. "their bank transfer is in transit") without
        touching the default every other tenant gets, and without needing to
        first know whether the tenant is currently ACTIVE or already PAST_DUE
        (the extension applies to the grace window itself, which affects both
        cases identically once evaluate_and_sync next runs). Cannot be used on
        a CANCELLED subscription — extend_days would have no expiry to attach
        to that still means anything.
        """
        sub = await _get_or_404(self.repo, id)
        if sub.status == SubscriptionStatus.CANCELLED:
            raise ValidationError("Cannot extend the grace period of a cancelled subscription.")
        sub = await self.repo.update(id, grace_period_days=sub.grace_period_days + data.extend_days)
        await self.db.commit()
        sub = await self.evaluate_and_sync(sub)
        return SubscriptionResponse.model_validate(sub)

    async def waive(self, id: UUID, data: SubscriptionWaiveRequest, recorded_by: UUID) -> PaymentResponse:
        """Forgives the current due period without requiring payment.

        Behaves exactly like record_payment() — extends expires_at by one
        billing_cycle and sets status -> ACTIVE, so a waived tenant is
        indistinguishable from a paid one in every other part of the app
        (POS access, reports, the tenant's own billing view) — except the
        payment-history row this creates has amount=0 and waived=True, so
        the distinction is never lost for accounting/audit purposes. Valid
        from any non-cancelled status, not just PAST_DUE/SUSPENDED — an admin
        may also waive a period that's still ACTIVE (e.g. a goodwill gesture)
        rather than only ever reacting to actual non-payment.
        """
        sub = await _get_or_404(self.repo, id)
        if sub.status == SubscriptionStatus.CANCELLED:
            raise ValidationError("Cannot waive a due period on a cancelled subscription.")

        period_start = sub.expires_at
        period_end = _next_expiry(period_start, sub.billing_cycle)
        b = compute_billing(sub.plan, sub.billing_cycle, sub.discount_pct)

        payment = await self.payment_repo.create(
            subscription_id=id,
            tenant_id=sub.tenant_id,
            amount=Decimal("0.00"),
            list_price=b["list_price"],
            discount_pct=b["discount_pct"],
            billing_cycle=sub.billing_cycle,
            period_start=period_start,
            period_end=period_end,
            payment_method="Waived",
            reference_number=None,
            notes=data.note,
            paid_at=datetime.now(timezone.utc),
            recorded_by=recorded_by,
            waived=True,
        )
        await self.repo.update(id, status=SubscriptionStatus.ACTIVE, expires_at=period_end)
        await self.db.commit()
        return PaymentResponse.model_validate(payment)

    async def extend_trial(self, id: UUID, data: SubscriptionExtendTrialRequest) -> SubscriptionResponse:
        """Adds `data.extend_days` to the trial end and expiry dates.

        Restricted to super admins at the route level (this method doesn't
        check that itself — see api/platform/subscriptions.py). Only valid
        while status == TRIAL: an ACTIVE subscription's period is extended
        via record_payment() instead, and a SUSPENDED/CANCELLED one must be
        reactivated first — extending a trial that isn't running doesn't
        have a sensible meaning, so this stays a narrow, single-purpose
        action rather than trying to cover every status.
        """
        sub = await _get_or_404(self.repo, id)
        if sub.status != SubscriptionStatus.TRIAL:
            raise ValidationError(
                "Only a subscription currently in TRIAL status can have its trial extended. "
                "Use Record Payment to extend an active subscription, or Reactivate first."
            )
        base = sub.trial_ends_at or datetime.now(timezone.utc)
        new_trial_ends_at = base + timedelta(days=data.extend_days)
        # Shift expires_at by the same delta, preserving whatever buffer it
        # already had past trial_ends_at (0 on the generic create() path,
        # 30 days on the onboarding path — see services/onboarding_service.py).
        new_expires_at = sub.expires_at + timedelta(days=data.extend_days)
        sub = await self.repo.update(id, trial_ends_at=new_trial_ends_at, expires_at=new_expires_at)
        await self.db.commit()
        return SubscriptionResponse.model_validate(sub)

    async def update(self, id: UUID, data: SubscriptionUpdate) -> SubscriptionResponse:
        """Update editable subscription fields (currently the per-tenant discount)."""
        sub = await _get_or_404(self.repo, id)
        if sub.status == SubscriptionStatus.CANCELLED:
            raise ValidationError("Cannot modify a cancelled subscription.")
        fields = data.model_dump(exclude_unset=True)
        if "plan_id" in fields:
            plan = await self.plan_repo.get_by_id(fields["plan_id"])
            if plan is None or not plan.is_active:
                raise NotFoundError("Plan not found or inactive.")
        if "billing_cycle" in fields and fields["billing_cycle"] is None:
            raise ValidationError("Billing cycle is required.")
        if fields:
            sub = await self.repo.update(id, **fields)
            await self.db.commit()
        return SubscriptionResponse.model_validate(sub)

    # ----------------------------------------------------------------
    # BILLING PREVIEW  (computed price for the current plan + cycle)
    # ----------------------------------------------------------------

    async def get_billing_preview(self, id: UUID) -> BillingPreviewResponse:
        sub = await _get_or_404(self.repo, id)
        b = compute_billing(sub.plan, sub.billing_cycle, sub.discount_pct)
        return BillingPreviewResponse(billing_cycle=sub.billing_cycle, **b)

    # ----------------------------------------------------------------
    # RECORD PAYMENT  (extends subscription period)
    # ----------------------------------------------------------------

    async def record_payment(
        self,
        subscription_id: UUID,
        data: RecordPaymentRequest,
        recorded_by: UUID,
    ) -> PaymentResponse:
        """Record a manual payment and extend the subscription by one billing period.

        Sets status → ACTIVE if it was TRIAL, SUSPENDED, or EXPIRED.
        """
        sub = await _get_or_404(self.repo, subscription_id)

        if sub.status == SubscriptionStatus.CANCELLED:
            raise ValidationError("Cannot record payment for a cancelled subscription.")

        period_start = sub.expires_at
        period_end = _next_expiry(period_start, sub.billing_cycle)

        # Fill the discount context from the plan + subscription when not supplied.
        if data.list_price is not None and data.discount_pct is not None:
            list_price = data.list_price
            discount_pct = data.discount_pct
        else:
            b = compute_billing(sub.plan, sub.billing_cycle, sub.discount_pct)
            list_price = data.list_price if data.list_price is not None else b["list_price"]
            discount_pct = data.discount_pct if data.discount_pct is not None else b["discount_pct"]

        payment = await self.payment_repo.create(
            subscription_id=subscription_id,
            tenant_id=sub.tenant_id,
            amount=data.amount,
            list_price=list_price,
            discount_pct=discount_pct,
            billing_cycle=sub.billing_cycle,
            period_start=period_start,
            period_end=period_end,
            payment_method=data.payment_method,
            reference_number=data.reference_number,
            notes=data.notes,
            paid_at=data.paid_at,
            recorded_by=recorded_by,
        )

        # Extend the subscription period and activate it.
        await self.repo.update(
            subscription_id,
            status=SubscriptionStatus.ACTIVE,
            expires_at=period_end,
        )
        await self.db.commit()
        return PaymentResponse.model_validate(payment)

    # ----------------------------------------------------------------
    # PAYMENT HISTORY
    # ----------------------------------------------------------------

    async def list_payments(
        self, subscription_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[PaymentResponse]:
        await _get_or_404(self.repo, subscription_id)
        payments = await self.payment_repo.list_for_subscription(subscription_id, skip, limit)
        return [PaymentResponse.model_validate(p) for p in payments]


# ── Helpers ───────────────────────────────────────────────────

def compute_billing(
    plan: Plan,
    billing_cycle: BillingCycle,
    sub_discount_pct: Decimal | None = None,
) -> dict:
    """Resolve the effective price for a plan + billing cycle.

    A per-subscription ``sub_discount_pct`` (when not None) REPLACES the plan's
    cycle-level discount. The percentage is clamped to 0–100 and money is
    quantized to 2 decimal places.
    """
    list_price: Decimal = (
        plan.price_yearly if billing_cycle == BillingCycle.YEARLY else plan.price_monthly
    )
    if sub_discount_pct is not None:
        pct = sub_discount_pct
    else:
        pct = (
            plan.discount_yearly_pct
            if billing_cycle == BillingCycle.YEARLY
            else plan.discount_monthly_pct
        )
    pct = max(Decimal("0"), min(Decimal("100"), pct or Decimal("0")))
    discount_amount = (list_price * pct / Decimal("100")).quantize(Decimal("0.01"))
    net_price = (list_price - discount_amount).quantize(Decimal("0.01"))
    return {
        "list_price": list_price,
        "discount_pct": pct,
        "discount_amount": discount_amount,
        "net_price": net_price,
    }


def _next_expiry(from_dt: datetime, cycle: BillingCycle) -> datetime:
    """Calculate the next expiry date from a given datetime."""
    if cycle == BillingCycle.MONTHLY:
        return from_dt + relativedelta(months=1)
    return from_dt + relativedelta(years=1)


async def _get_or_404(repo: SubscriptionRepository, id: UUID):
    sub = await repo.get_by_id(id)
    if not sub:
        raise NotFoundError("Subscription not found.")
    return sub
