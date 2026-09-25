# services/tenant_subscription_service.py
#
# Read-only billing view for a tenant admin.
#
# ISOLATION: every method takes the caller's tenant_id (from their JWT) and
# scopes every query to it. There is no code path that accepts a subscription_id
# or another tenant_id from the client — a tenant can only ever see its own
# subscription and its own payments.

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError
from repositories.subscription_payment_repository import SubscriptionPaymentRepository
from repositories.subscription_repository import SubscriptionRepository
from schemas.subscription import TenantPaymentView, TenantSubscriptionView
from services.subscription_service import SubscriptionService, compute_billing


class TenantSubscriptionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.sub_repo = SubscriptionRepository(db)
        self.payment_repo = SubscriptionPaymentRepository(db)

    async def get_current(self, tenant_id: UUID) -> TenantSubscriptionView:
        """Return the caller tenant's active/trial/past-due subscription summary."""
        sub = await self.sub_repo.get_active_for_tenant(tenant_id)
        if not sub:
            raise NotFoundError("No active subscription for this tenant.")
        # A tenant checking their own billing page must see PAST_DUE/SUSPENDED
        # the moment it's true, same as every other reader of subscription
        # state — not whatever the row happened to say before this request.
        sub = await SubscriptionService(self.db).evaluate_and_sync(sub)

        b = compute_billing(sub.plan, sub.billing_cycle, sub.discount_pct)
        return TenantSubscriptionView(
            plan_name=sub.plan.name,
            max_branches=sub.plan.max_branches,
            max_devices=sub.plan.max_devices,
            max_users=sub.plan.max_users,
            billing_cycle=sub.billing_cycle,
            status=sub.status,
            started_at=sub.started_at,
            expires_at=sub.expires_at,
            trial_ends_at=sub.trial_ends_at,
            grace_period_days=sub.grace_period_days,
            list_price=b["list_price"],
            discount_pct=b["discount_pct"],
            discount_amount=b["discount_amount"],
            net_price=b["net_price"],
        )

    async def list_payments(
        self, tenant_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[TenantPaymentView]:
        """Return the caller tenant's own payment history (newest first)."""
        payments = await self.payment_repo.list_for_tenant(tenant_id, skip=skip, limit=limit)
        return [TenantPaymentView.model_validate(p) for p in payments]
