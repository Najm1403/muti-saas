# tests/test_subscription_lifecycle.py
#
# The automatic (evaluate_and_sync) + manual (extend_grace, waive) non-payment
# lifecycle, and its two consumers: the POS device guard (PAST_DUE allowed,
# SUSPENDED blocked) and GET /auth/me's tenant-dashboard billing banner.

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from core.exceptions import ForbiddenError, ValidationError
from core.security import hash_password
from db.session import get_db
from models.branch import Branch
from models.business import Business
from models.device import Device, DeviceStatus
from models.plan import Plan
from models.platform_admin import PlatformAdmin
from models.subscription import BillingCycle, SubscriptionStatus
from repositories.subscription_repository import SubscriptionRepository
from schemas.subscription import SubscriptionExtendGraceRequest, SubscriptionWaiveRequest
from services.subscription_service import SubscriptionService
from api.v1.pos._guards import _load_device


def _plan(**kw) -> Plan:
    defaults = dict(
        id=uuid4(), name="P", description=None,
        price_monthly=Decimal("1000.00"), price_yearly=Decimal("10000.00"),
        discount_monthly_pct=Decimal("0"), discount_yearly_pct=Decimal("0"),
        max_restaurants=1, max_branches=1, max_users=5, max_devices=2, is_active=True,
    )
    defaults.update(kw)
    return Plan(**defaults)


@pytest_asyncio.fixture
async def lifecycle_setup(db, two_tenants):
    admin = PlatformAdmin(
        id=uuid4(), email="ops2@platform.test", full_name="Ops",
        password_hash=hash_password("x" * 10), is_active=True, is_super=True,
    )
    plan = _plan()
    db.add_all([admin, plan])
    await db.flush()
    return dict(admin=admin, plan=plan, **two_tenants)


async def _create_with_grace(db, tenant_id, plan_id, expires_at, status, grace_period_days=5):
    now = datetime.now(timezone.utc)
    sub = await SubscriptionRepository(db).create(
        tenant_id=tenant_id, plan_id=plan_id, billing_cycle=BillingCycle.MONTHLY,
        status=status, started_at=now, expires_at=expires_at,
    )
    sub.grace_period_days = grace_period_days
    await db.flush()
    return sub


# ── evaluate_and_sync ────────────────────────────────────────────

class TestEvaluateAndSync:
    @pytest.mark.asyncio
    async def test_active_past_expiry_within_grace_becomes_past_due(self, db, lifecycle_setup):
        sub = await _create_with_grace(
            db, lifecycle_setup["tenant_a"].id, lifecycle_setup["plan"].id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=2),
            status=SubscriptionStatus.ACTIVE, grace_period_days=5,
        )
        sub = await SubscriptionService(db).evaluate_and_sync(sub)
        assert sub.status == SubscriptionStatus.PAST_DUE

    @pytest.mark.asyncio
    async def test_past_due_beyond_grace_becomes_suspended(self, db, lifecycle_setup):
        sub = await _create_with_grace(
            db, lifecycle_setup["tenant_a"].id, lifecycle_setup["plan"].id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=10),
            status=SubscriptionStatus.PAST_DUE, grace_period_days=5,
        )
        sub = await SubscriptionService(db).evaluate_and_sync(sub)
        assert sub.status == SubscriptionStatus.SUSPENDED

    @pytest.mark.asyncio
    async def test_active_far_past_grace_jumps_straight_to_suspended(self, db, lifecycle_setup):
        """A subscription that was never re-evaluated during PAST_DUE (e.g.
        no one touched it for weeks) must still land on SUSPENDED, not get
        stuck at PAST_DUE forever just because it skipped that intermediate read."""
        sub = await _create_with_grace(
            db, lifecycle_setup["tenant_a"].id, lifecycle_setup["plan"].id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=30),
            status=SubscriptionStatus.ACTIVE, grace_period_days=5,
        )
        sub = await SubscriptionService(db).evaluate_and_sync(sub)
        assert sub.status == SubscriptionStatus.SUSPENDED

    @pytest.mark.asyncio
    async def test_suspended_never_auto_reactivates(self, db, lifecycle_setup):
        """A platform admin's manual suspend must never be silently undone by
        the timer, even long after expires_at — only a human action (waive,
        record payment, reactivate) may move it out of SUSPENDED."""
        sub = await _create_with_grace(
            db, lifecycle_setup["tenant_a"].id, lifecycle_setup["plan"].id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            status=SubscriptionStatus.SUSPENDED, grace_period_days=5,
        )
        sub = await SubscriptionService(db).evaluate_and_sync(sub)
        assert sub.status == SubscriptionStatus.SUSPENDED

    @pytest.mark.asyncio
    async def test_cancelled_never_auto_changes(self, db, lifecycle_setup):
        sub = await _create_with_grace(
            db, lifecycle_setup["tenant_a"].id, lifecycle_setup["plan"].id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=100),
            status=SubscriptionStatus.CANCELLED, grace_period_days=5,
        )
        sub = await SubscriptionService(db).evaluate_and_sync(sub)
        assert sub.status == SubscriptionStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_within_expiry_stays_active(self, db, lifecycle_setup):
        sub = await _create_with_grace(
            db, lifecycle_setup["tenant_a"].id, lifecycle_setup["plan"].id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=10),
            status=SubscriptionStatus.ACTIVE, grace_period_days=5,
        )
        sub = await SubscriptionService(db).evaluate_and_sync(sub)
        assert sub.status == SubscriptionStatus.ACTIVE


# ── extend_grace ─────────────────────────────────────────────────

class TestExtendGrace:
    @pytest.mark.asyncio
    async def test_extends_grace_and_keeps_past_due_instead_of_suspended(self, db, lifecycle_setup):
        svc = SubscriptionService(db)
        sub = await _create_with_grace(
            db, lifecycle_setup["tenant_a"].id, lifecycle_setup["plan"].id,
            # 4 days overdue, default 5-day grace would already show PAST_DUE
            # and be only 1 day from SUSPENDED.
            expires_at=datetime.now(timezone.utc) - timedelta(days=4),
            status=SubscriptionStatus.ACTIVE, grace_period_days=5,
        )
        updated = await svc.extend_grace(sub.id, SubscriptionExtendGraceRequest(extend_days=10))
        assert updated.grace_period_days == 15
        assert updated.status == SubscriptionStatus.PAST_DUE  # not SUSPENDED

    @pytest.mark.asyncio
    async def test_rejects_cancelled(self, db, lifecycle_setup):
        svc = SubscriptionService(db)
        sub = await _create_with_grace(
            db, lifecycle_setup["tenant_a"].id, lifecycle_setup["plan"].id,
            expires_at=datetime.now(timezone.utc), status=SubscriptionStatus.CANCELLED,
        )
        with pytest.raises(ValidationError):
            await svc.extend_grace(sub.id, SubscriptionExtendGraceRequest(extend_days=5))


# ── waive ────────────────────────────────────────────────────────

class TestWaive:
    @pytest.mark.asyncio
    async def test_waive_extends_period_and_reactivates(self, db, lifecycle_setup):
        svc = SubscriptionService(db)
        old_expiry = datetime.now(timezone.utc) - timedelta(days=20)
        sub = await _create_with_grace(
            db, lifecycle_setup["tenant_a"].id, lifecycle_setup["plan"].id,
            expires_at=old_expiry, status=SubscriptionStatus.SUSPENDED,
        )
        payment = await svc.waive(
            sub.id, SubscriptionWaiveRequest(note="Goodwill — bank transfer delayed"),
            recorded_by=lifecycle_setup["admin"].id,
        )
        assert payment.amount == Decimal("0.00")
        assert payment.waived is True
        assert payment.period_start == old_expiry

        refreshed = await svc.get(sub.id)
        assert refreshed.status == SubscriptionStatus.ACTIVE
        assert refreshed.expires_at > old_expiry

    @pytest.mark.asyncio
    async def test_rejects_cancelled(self, db, lifecycle_setup):
        svc = SubscriptionService(db)
        sub = await _create_with_grace(
            db, lifecycle_setup["tenant_a"].id, lifecycle_setup["plan"].id,
            expires_at=datetime.now(timezone.utc), status=SubscriptionStatus.CANCELLED,
        )
        with pytest.raises(ValidationError):
            await svc.waive(sub.id, SubscriptionWaiveRequest(), recorded_by=lifecycle_setup["admin"].id)


# ── POS guard: PAST_DUE allowed, SUSPENDED blocked ─────────────────

@pytest_asyncio.fixture
async def pos_env(db, two_tenants, lifecycle_setup):
    tenant = two_tenants["tenant_a"]
    biz = Business(id=uuid4(), tenant_id=tenant.id, name="Biz", is_active=True)
    branch = Branch(id=uuid4(), business_id=biz.id, branch_code="BA", name="Main", is_active=True)
    device = Device(id=uuid4(), branch_id=branch.id, device_code="DEV1", letter="A", name="POS 1",
                     device_type="POS", status=DeviceStatus.ACTIVE,
                     activated_at=datetime.now(timezone.utc))
    db.add_all([biz, branch, device])
    await db.flush()
    return dict(tenant=tenant, branch=branch, device=device, plan=lifecycle_setup["plan"])


class TestPosGuard:
    @pytest.mark.asyncio
    async def test_past_due_still_allowed(self, db, pos_env):
        await _create_with_grace(
            db, pos_env["tenant"].id, pos_env["plan"].id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=2),
            status=SubscriptionStatus.ACTIVE, grace_period_days=5,
        )
        # Should not raise — PAST_DUE is a warning stage only.
        await _load_device(db, pos_env["device"].id, pos_env["branch"].id, pos_env["tenant"].id)

    @pytest.mark.asyncio
    async def test_suspended_blocks_pos(self, db, pos_env):
        await _create_with_grace(
            db, pos_env["tenant"].id, pos_env["plan"].id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=30),
            status=SubscriptionStatus.SUSPENDED, grace_period_days=5,
        )
        with pytest.raises(ForbiddenError):
            await _load_device(db, pos_env["device"].id, pos_env["branch"].id, pos_env["tenant"].id)

    @pytest.mark.asyncio
    async def test_lapsed_active_auto_suspends_and_blocks(self, db, pos_env):
        """The automatic transition itself must be what blocks POS, not just
        a pre-suspended row — proves evaluate_and_sync is actually wired into
        the guard, not bypassed."""
        await _create_with_grace(
            db, pos_env["tenant"].id, pos_env["plan"].id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=30),
            status=SubscriptionStatus.ACTIVE, grace_period_days=5,
        )
        with pytest.raises(ForbiddenError):
            await _load_device(db, pos_env["device"].id, pos_env["branch"].id, pos_env["tenant"].id)


# ── GET /auth/me billing banner ────────────────────────────────────

async def _me(db, user_id, tenant_id):
    from core.security import create_access_token
    async def override():
        yield db
    app.dependency_overrides[get_db] = override
    try:
        token = create_access_token(user_id, tenant_id)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test.local") as client:
            return await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer " + token})
    finally:
        app.dependency_overrides.clear()


class TestMeBillingBanner:
    @pytest.mark.asyncio
    async def test_past_due_shown_on_me(self, db, lifecycle_setup):
        tenant = lifecycle_setup["tenant_a"]
        await _create_with_grace(
            db, tenant.id, lifecycle_setup["plan"].id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            status=SubscriptionStatus.ACTIVE, grace_period_days=5,
        )
        resp = await _me(db, lifecycle_setup["user_a"].id, tenant.id)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["subscription"]["status"] == "PAST_DUE"
        assert body["subscription"]["days_overdue"] == 1

    @pytest.mark.asyncio
    async def test_admin_message_shown_on_me(self, db, lifecycle_setup):
        tenant = lifecycle_setup["tenant_a"]
        tenant.admin_message = "Please update your billing contact email."
        tenant.admin_message_set_at = datetime.now(timezone.utc)
        await db.flush()
        resp = await _me(db, lifecycle_setup["user_a"].id, tenant.id)
        assert resp.status_code == 200, resp.text
        assert resp.json()["admin_message"] == "Please update your billing contact email."

    @pytest.mark.asyncio
    async def test_no_subscription_no_banner(self, db, lifecycle_setup):
        resp = await _me(db, lifecycle_setup["user_a"].id, lifecycle_setup["tenant_a"].id)
        assert resp.status_code == 200, resp.text
        assert resp.json()["subscription"] is None
