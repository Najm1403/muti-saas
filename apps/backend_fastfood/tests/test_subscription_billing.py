# tests/test_subscription_billing.py
#
# Covers the billing-discount layer:
#   1. compute_billing()          — pure pricing maths
#   2. record_payment()           — stores list_price / discount_pct, honours overrides
#   3. TenantSubscriptionService  — tenant isolation + no cross-tenant identifiers leak

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

from core.exceptions import ValidationError
from core.security import hash_password
from models.plan import Plan
from models.platform_admin import PlatformAdmin
from models.subscription import BillingCycle, SubscriptionStatus
from repositories.subscription_repository import SubscriptionRepository
from schemas.subscription import RecordPaymentRequest, SubscriptionExtendTrialRequest
from services.subscription_service import SubscriptionService, compute_billing
from services.tenant_dashboard_service import TenantDashboardService
from services.tenant_subscription_service import TenantSubscriptionService


# ================================================================
# 1. compute_billing — pure function
# ================================================================

def _plan(**kw) -> Plan:
    defaults = dict(
        id=uuid4(), name="P", description=None,
        price_monthly=Decimal("1000.00"), price_yearly=Decimal("10000.00"),
        discount_monthly_pct=Decimal("0"), discount_yearly_pct=Decimal("0"),
        max_restaurants=1, max_branches=1, max_users=5, max_devices=2, is_active=True,
    )
    defaults.update(kw)
    return Plan(**defaults)


class TestComputeBilling:
    def test_no_discount(self):
        b = compute_billing(_plan(), BillingCycle.MONTHLY)
        assert b["list_price"] == Decimal("1000.00")
        assert b["discount_pct"] == Decimal("0")
        assert b["net_price"] == Decimal("1000.00")

    def test_plan_level_monthly_vs_yearly(self):
        p = _plan(discount_monthly_pct=Decimal("10"), discount_yearly_pct=Decimal("20"))
        m = compute_billing(p, BillingCycle.MONTHLY)
        y = compute_billing(p, BillingCycle.YEARLY)
        assert m["discount_pct"] == Decimal("10")
        assert m["net_price"] == Decimal("900.00")
        assert y["discount_pct"] == Decimal("20")
        assert y["net_price"] == Decimal("8000.00")

    def test_subscription_override_replaces_plan_discount(self):
        p = _plan(discount_yearly_pct=Decimal("20"))
        b = compute_billing(p, BillingCycle.YEARLY, sub_discount_pct=Decimal("15"))
        assert b["discount_pct"] == Decimal("15")
        assert b["net_price"] == Decimal("8500.00")

    def test_zero_override_is_respected(self):
        p = _plan(discount_monthly_pct=Decimal("10"))
        b = compute_billing(p, BillingCycle.MONTHLY, sub_discount_pct=Decimal("0"))
        assert b["discount_pct"] == Decimal("0")
        assert b["net_price"] == Decimal("1000.00")

    def test_pct_clamped_and_net_never_negative(self):
        b = compute_billing(_plan(), BillingCycle.MONTHLY, sub_discount_pct=Decimal("150"))
        assert b["discount_pct"] == Decimal("100")
        assert b["net_price"] == Decimal("0.00")


# ================================================================
# DB fixtures
# ================================================================

@pytest_asyncio.fixture
async def billing_setup(db, two_tenants):
    """A plan + an ACTIVE subscription for tenant_a, plus a platform admin."""
    admin = PlatformAdmin(
        id=uuid4(), email="ops@platform.test", full_name="Ops",
        password_hash=hash_password("x" * 10), is_active=True, is_super=True,
    )
    plan = _plan(
        name="Pro", price_monthly=Decimal("2000.00"), price_yearly=Decimal("20000.00"),
        discount_monthly_pct=Decimal("0"), discount_yearly_pct=Decimal("10"),
    )
    db.add_all([admin, plan])
    await db.flush()

    repo = SubscriptionRepository(db)
    now = datetime.now(timezone.utc)
    sub_a = await repo.create(
        tenant_id=two_tenants["tenant_a"].id, plan_id=plan.id,
        billing_cycle=BillingCycle.YEARLY, status=SubscriptionStatus.ACTIVE,
        started_at=now, expires_at=now, discount_pct=Decimal("15"),
    )
    await db.flush()
    return dict(admin=admin, plan=plan, sub_a=sub_a, **two_tenants)


# ================================================================
# 2. record_payment
# ================================================================

class TestRecordPayment:
    @pytest.mark.asyncio
    async def test_fills_discount_context_from_subscription(self, db, billing_setup):
        svc = SubscriptionService(db)
        req = RecordPaymentRequest(
            amount=Decimal("17000.00"), payment_method="Bank Transfer",
            paid_at=datetime.now(timezone.utc),
        )
        out = await svc.record_payment(
            subscription_id=billing_setup["sub_a"].id, data=req,
            recorded_by=billing_setup["admin"].id,
        )
        # yearly list 20000, subscription override 15% -> net 17000
        assert out.list_price == Decimal("20000.00")
        assert out.discount_pct == Decimal("15.00")
        assert out.amount == Decimal("17000.00")

    @pytest.mark.asyncio
    async def test_admin_amount_override_is_kept(self, db, billing_setup):
        svc = SubscriptionService(db)
        req = RecordPaymentRequest(
            amount=Decimal("12345.00"), payment_method="Cash",
            paid_at=datetime.now(timezone.utc),
        )
        out = await svc.record_payment(
            subscription_id=billing_setup["sub_a"].id, data=req,
            recorded_by=billing_setup["admin"].id,
        )
        assert out.amount == Decimal("12345.00")
        assert out.list_price == Decimal("20000.00")

    @pytest.mark.asyncio
    async def test_billing_preview_matches(self, db, billing_setup):
        svc = SubscriptionService(db)
        preview = await svc.get_billing_preview(billing_setup["sub_a"].id)
        assert preview.list_price == Decimal("20000.00")
        assert preview.discount_pct == Decimal("15")
        assert preview.net_price == Decimal("17000.00")


# ================================================================
# 3. Tenant isolation
# ================================================================

class TestTenantSubscriptionIsolation:
    @pytest.mark.asyncio
    async def test_tenant_sees_only_own_subscription(self, db, billing_setup):
        svc = TenantSubscriptionService(db)
        view = await svc.get_current(tenant_id=billing_setup["tenant_a"].id)
        assert view.plan_name == "Pro"
        assert view.net_price == Decimal("17000.00")
        assert view.max_branches == 1
        assert view.max_devices == 2
        assert view.max_users == 5

    @pytest.mark.asyncio
    async def test_dashboard_includes_plan_allowances(self, db, billing_setup):
        stats = await TenantDashboardService(db).get_stats(
            tenant_id=billing_setup["tenant_a"].id
        )
        assert stats.max_branches == 1
        assert stats.max_devices == 2
        assert stats.max_users == 5


# ================================================================
# 4. extend_trial — super-admin-only trial extension
# ================================================================

@pytest_asyncio.fixture
async def trial_setup(db, two_tenants):
    """A plan + a TRIAL subscription for tenant_a."""
    plan = _plan(name="Starter")
    db.add(plan)
    await db.flush()

    repo = SubscriptionRepository(db)
    now = datetime.now(timezone.utc)
    trial_ends_at = now + timedelta(days=14)
    sub = await repo.create(
        tenant_id=two_tenants["tenant_a"].id, plan_id=plan.id,
        billing_cycle=BillingCycle.MONTHLY, status=SubscriptionStatus.TRIAL,
        started_at=now, expires_at=trial_ends_at + timedelta(days=30),
        trial_ends_at=trial_ends_at,
    )
    await db.flush()
    return dict(plan=plan, sub=sub, trial_ends_at=trial_ends_at, **two_tenants)


class TestExtendTrial:
    @pytest.mark.asyncio
    async def test_extends_trial_end_and_expiry_by_same_amount(self, db, trial_setup):
        svc = SubscriptionService(db)
        before_expires_at = trial_setup["sub"].expires_at
        out = await svc.extend_trial(
            trial_setup["sub"].id, SubscriptionExtendTrialRequest(extend_days=10)
        )
        assert out.trial_ends_at == trial_setup["trial_ends_at"] + timedelta(days=10)
        assert out.expires_at == before_expires_at + timedelta(days=10)
        assert out.status == SubscriptionStatus.TRIAL

    @pytest.mark.asyncio
    async def test_rejects_when_not_in_trial(self, db, billing_setup):
        """billing_setup's subscription is ACTIVE, not TRIAL."""
        svc = SubscriptionService(db)
        with pytest.raises(ValidationError, match="currently in TRIAL status"):
            await svc.extend_trial(
                billing_setup["sub_a"].id, SubscriptionExtendTrialRequest(extend_days=10)
            )

    @pytest.mark.asyncio
    async def test_extend_days_must_be_positive(self):
        with pytest.raises(Exception):  # pydantic ValidationError — gt=0
            SubscriptionExtendTrialRequest(extend_days=0)

    @pytest.mark.asyncio
    async def test_other_tenant_has_no_subscription(self, db, billing_setup):
        from core.exceptions import NotFoundError

        svc = TenantSubscriptionService(db)
        with pytest.raises(NotFoundError):
            await svc.get_current(tenant_id=billing_setup["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_payment_history_scoped_and_sanitised(self, db, billing_setup):
        sub_svc = SubscriptionService(db)
        await sub_svc.record_payment(
            subscription_id=billing_setup["sub_a"].id,
            data=RecordPaymentRequest(
                amount=Decimal("17000.00"), payment_method="Cash",
                paid_at=datetime.now(timezone.utc),
            ),
            recorded_by=billing_setup["admin"].id,
        )

        tsvc = TenantSubscriptionService(db)
        mine = await tsvc.list_payments(tenant_id=billing_setup["tenant_a"].id)
        assert len(mine) == 1
        dumped = mine[0].model_dump()
        assert "recorded_by" not in dumped
        assert "subscription_id" not in dumped
        assert "tenant_id" not in dumped

        others = await tsvc.list_payments(tenant_id=billing_setup["tenant_b"].id)
        assert others == []
