# tests/test_device_lifecycle.py
#
# Covers the tenant-owned device flow:
#   1. quota vs plan.max_devices (no plan → 1 allowed)
#   2. activation code: one-time, expiry, tenant/branch binding, revoked device
#   3. lifecycle: tenant suspend/reactivate, platform suspend overrides, revoke terminal
#   4. tenant isolation
#   5. online guard blocks suspended / revoked devices

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio

from core.exceptions import (
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from models.branch import Branch
from models.business import Business
from models.device import Device, DeviceStatus, SuspendScope
from models.plan import Plan
from models.subscription import BillingCycle, SubscriptionStatus
from repositories.subscription_repository import SubscriptionRepository
from schemas.device import DeviceCreate
from services.device_service import DeviceService, activate_device_with_code
from services.platform_device_service import PlatformDeviceService
from api.v1.pos._guards import _load_device


@pytest_asyncio.fixture
async def env(db, two_tenants):
    """tenant_a/tenant_b each with a business + one branch."""
    a, b = two_tenants["tenant_a"], two_tenants["tenant_b"]
    biz_a = Business(id=uuid4(), tenant_id=a.id, name="Biz A", is_active=True)
    biz_b = Business(id=uuid4(), tenant_id=b.id, name="Biz B", is_active=True)
    br_a = Branch(id=uuid4(), business_id=biz_a.id, branch_code="BA", name="Main A", is_active=True)
    br_b = Branch(id=uuid4(), business_id=biz_b.id, branch_code="BB", name="Main B", is_active=True)
    db.add_all([biz_a, biz_b, br_a, br_b])
    await db.flush()
    return dict(db=db, tenant_a=a, tenant_b=b, branch_a=br_a, branch_b=br_b)


async def _give_plan(db, tenant_id, max_devices: int) -> None:
    plan = Plan(
        id=uuid4(), name=f"P{max_devices}-{uuid4().hex[:4]}", description=None,
        price_monthly=1, price_yearly=10,
        max_restaurants=1, max_branches=1, max_users=5, max_devices=max_devices, is_active=True,
    )
    db.add(plan)
    await db.flush()
    now = datetime.now(timezone.utc)
    await SubscriptionRepository(db).create(
        tenant_id=tenant_id, plan_id=plan.id, billing_cycle=BillingCycle.MONTHLY,
        status=SubscriptionStatus.ACTIVE, started_at=now, expires_at=now + timedelta(days=30),
    )
    await db.flush()


def _mk(branch_id, name="POS 1"):
    return DeviceCreate(name=name, branch_id=branch_id, device_type="POS")


# ── 1. quota ──────────────────────────────────────────────────

class TestQuota:
    @pytest.mark.asyncio
    async def test_no_plan_allows_exactly_one(self, env):
        svc = DeviceService(env["db"])
        await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, "A"))
        with pytest.raises(ConflictError):
            await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, "B"))

    @pytest.mark.asyncio
    async def test_plan_limit_enforced(self, env):
        await _give_plan(env["db"], env["tenant_a"].id, max_devices=2)
        svc = DeviceService(env["db"])
        await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, "A"))
        await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, "B"))
        with pytest.raises(ConflictError):
            await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, "C"))

    @pytest.mark.asyncio
    async def test_unlimited(self, env):
        await _give_plan(env["db"], env["tenant_a"].id, max_devices=-1)
        svc = DeviceService(env["db"])
        for i in range(4):
            await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, f"D{i}"))

    @pytest.mark.asyncio
    async def test_revoked_does_not_count(self, env):
        await _give_plan(env["db"], env["tenant_a"].id, max_devices=1)
        svc = DeviceService(env["db"])
        d = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, "A"))
        await svc.revoke(d.id, env["tenant_a"].id)
        # revoked frees the slot
        await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, "B"))


# ── 1b. device letters ───────────────────────────────────────

class TestDeviceLetters:
    @pytest.mark.asyncio
    async def test_letters_assigned_sequentially_per_branch(self, env):
        await _give_plan(env["db"], env["tenant_a"].id, max_devices=5)
        svc = DeviceService(env["db"])
        d1 = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, "Counter 1"))
        d2 = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, "Counter 2"))
        d3 = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, "Counter 3"))
        assert (d1.letter, d2.letter, d3.letter) == ("A", "B", "C")

    @pytest.mark.asyncio
    async def test_letters_independent_per_branch(self, env):
        await _give_plan(env["db"], env["tenant_a"].id, max_devices=5)
        # A second branch under the SAME tenant (branch_b belongs to tenant_b
        # — a different tenant entirely — and would 404 here).
        second_branch = Branch(
            id=uuid4(), business_id=env["branch_a"].business_id,
            branch_code="BA2", name="Second A Branch", is_active=True,
        )
        env["db"].add(second_branch)
        await env["db"].flush()

        svc = DeviceService(env["db"])
        a1 = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, "A-side"))
        b1 = await svc.create(env["tenant_a"].id, _mk(second_branch.id, "B-side"))
        assert a1.letter == "A"
        assert b1.letter == "A"  # separate branch, own sequence

    @pytest.mark.asyncio
    async def test_letter_never_reused_after_delete(self, env):
        await _give_plan(env["db"], env["tenant_a"].id, max_devices=5)
        svc = DeviceService(env["db"])
        d1 = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, "First"))
        assert d1.letter == "A"
        await svc.delete(d1.id, env["tenant_a"].id)
        d2 = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id, "Second"))
        assert d2.letter == "B"  # not "A" again


# ── 2. activation ─────────────────────────────────────────────

class TestActivation:
    @pytest.mark.asyncio
    async def test_activate_then_code_is_single_use(self, env):
        svc = DeviceService(env["db"])
        created = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        code = created.activation_code

        device, branch, business, tenant = await activate_device_with_code(env["db"], f"{code[:2]} {code[2:]}")
        assert device.status == DeviceStatus.ACTIVE
        assert device.activated_at is not None
        assert branch.id == env["branch_a"].id
        assert tenant.id == env["tenant_a"].id

        with pytest.raises(ValidationError):
            await activate_device_with_code(env["db"], code)

    @pytest.mark.asyncio
    async def test_wrong_code(self, env):
        with pytest.raises(ValidationError):
            await activate_device_with_code(env["db"], "0000")

    @pytest.mark.asyncio
    async def test_expired_code(self, env):
        svc = DeviceService(env["db"])
        created = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        row = await svc.repo.get_by_id(created.id, env["tenant_a"].id)
        row.activation_code_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await env["db"].flush()
        with pytest.raises(ValidationError):
            await activate_device_with_code(env["db"], created.activation_code)

    @pytest.mark.asyncio
    async def test_revoked_device_cannot_activate(self, env):
        svc = DeviceService(env["db"])
        created = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        code = created.activation_code
        await svc.revoke(created.id, env["tenant_a"].id)
        with pytest.raises(ValidationError):
            await activate_device_with_code(env["db"], code)

    @pytest.mark.asyncio
    async def test_regenerate_replaces_code(self, env):
        svc = DeviceService(env["db"])
        created = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        again = await svc.regenerate_code(created.id, env["tenant_a"].id)
        assert again.activation_code != created.activation_code
        with pytest.raises(ValidationError):
            await activate_device_with_code(env["db"], created.activation_code)
        device, *_ = await activate_device_with_code(env["db"], again.activation_code)
        assert device.status == DeviceStatus.ACTIVE


# ── 2b. show code / regenerate guard / reset ──────────────────

class TestActivationCodeVisibility:
    @pytest.mark.asyncio
    async def test_show_code_while_valid(self, env):
        svc = DeviceService(env["db"])
        created = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        view = await svc.get_code(created.id, env["tenant_a"].id)
        assert view.activation_code == created.activation_code
        assert view.expired is False and view.used is False and view.can_regenerate is True

    @pytest.mark.asyncio
    async def test_show_code_expired(self, env):
        svc = DeviceService(env["db"])
        created = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        row = await svc.repo.get_by_id(created.id, env["tenant_a"].id)
        row.activation_code_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await env["db"].flush()
        view = await svc.get_code(created.id, env["tenant_a"].id)
        assert view.expired is True
        assert view.activation_code is None
        assert view.can_regenerate is True

    @pytest.mark.asyncio
    async def test_show_code_used_after_activation(self, env):
        svc = DeviceService(env["db"])
        created = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        await activate_device_with_code(env["db"], created.activation_code)
        view = await svc.get_code(created.id, env["tenant_a"].id)
        assert view.used is True
        assert view.activation_code is None
        assert view.can_regenerate is False

    @pytest.mark.asyncio
    async def test_regenerate_blocked_after_activation(self, env):
        svc = DeviceService(env["db"])
        created = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        await activate_device_with_code(env["db"], created.activation_code)
        with pytest.raises(ConflictError):
            await svc.regenerate_code(created.id, env["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_reset_deactivates_and_reissues(self, env):
        svc = DeviceService(env["db"])
        created = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        old_code = created.activation_code
        device, *_ = await activate_device_with_code(env["db"], old_code)
        assert device.status == DeviceStatus.ACTIVE

        reset = await svc.reset(created.id, env["tenant_a"].id)
        assert reset.status == DeviceStatus.PENDING
        assert reset.activated_at is None
        assert reset.activation_code and reset.activation_code != old_code

        # old code is dead, new code pairs the device again
        with pytest.raises(ValidationError):
            await activate_device_with_code(env["db"], old_code)
        again, *_ = await activate_device_with_code(env["db"], reset.activation_code)
        assert again.status == DeviceStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_reset_requires_activation(self, env):
        svc = DeviceService(env["db"])
        created = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        with pytest.raises(ValidationError):
            await svc.reset(created.id, env["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_reset_rejected_for_other_tenant(self, env):
        svc = DeviceService(env["db"])
        created = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        await activate_device_with_code(env["db"], created.activation_code)
        with pytest.raises(NotFoundError):
            await svc.reset(created.id, env["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_activation_state_labels(self, env):
        svc = DeviceService(env["db"])
        created = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        row = await svc.repo.get_by_id(created.id, env["tenant_a"].id)
        assert row.activation_state == "not_activated"

        row.activation_code_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await env["db"].flush()
        assert row.activation_state == "code_expired"

        fresh = await svc.regenerate_code(created.id, env["tenant_a"].id)
        await activate_device_with_code(env["db"], fresh.activation_code)
        row = await svc.repo.get_by_id(created.id, env["tenant_a"].id)
        assert row.activation_state == "activated"


# ── 3. lifecycle ──────────────────────────────────────────────

class TestLifecycle:
    @pytest.mark.asyncio
    async def test_tenant_suspend_reactivate(self, env):
        svc = DeviceService(env["db"])
        d = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        await activate_device_with_code(env["db"], d.activation_code)
        s = await svc.suspend(d.id, env["tenant_a"].id)
        assert s.status == DeviceStatus.SUSPENDED and s.suspended_scope == SuspendScope.TENANT
        r = await svc.reactivate(d.id, env["tenant_a"].id)
        assert r.status == DeviceStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_platform_suspension_blocks_tenant_reactivate(self, env):
        svc = DeviceService(env["db"])
        d = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        await activate_device_with_code(env["db"], d.activation_code)

        await PlatformDeviceService(env["db"]).suspend(d.id)
        with pytest.raises(ValidationError):
            await svc.reactivate(d.id, env["tenant_a"].id)
        # platform can lift it
        r = await PlatformDeviceService(env["db"]).reactivate(d.id)
        assert r.status == DeviceStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_revoke_is_terminal(self, env):
        svc = DeviceService(env["db"])
        d = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        await svc.revoke(d.id, env["tenant_a"].id)
        with pytest.raises(ValidationError):
            await svc.reactivate(d.id, env["tenant_a"].id)


# ── 4. isolation ──────────────────────────────────────────────

class TestIsolation:
    @pytest.mark.asyncio
    async def test_other_tenant_cannot_touch_device(self, env):
        svc = DeviceService(env["db"])
        d = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        with pytest.raises(NotFoundError):
            await svc.get(d.id, env["tenant_b"].id)
        with pytest.raises(NotFoundError):
            await svc.suspend(d.id, env["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_create_on_foreign_branch_rejected(self, env):
        svc = DeviceService(env["db"])
        with pytest.raises(NotFoundError):
            await svc.create(env["tenant_a"].id, _mk(env["branch_b"].id))


# ── 5. online guard ───────────────────────────────────────────

class TestOnlineGuard:
    @pytest.mark.asyncio
    async def test_missing_device_has_reactivation_code(self, env):
        with pytest.raises(AuthenticationError) as exc:
            await _load_device(
                env["db"], uuid4(), env["branch_a"].id, env["tenant_a"].id
            )
        assert exc.value.code == "DEVICE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_guard_blocks_suspended_and_revoked(self, env):
        svc = DeviceService(env["db"])
        created = await svc.create(env["tenant_a"].id, _mk(env["branch_a"].id))
        device, branch, business, tenant = await activate_device_with_code(env["db"], created.activation_code)

        # healthy
        await _load_device(env["db"], device.id, branch.id, tenant.id)

        await svc.suspend(created.id, env["tenant_a"].id)
        with pytest.raises(ForbiddenError) as ei:
            await _load_device(env["db"], device.id, branch.id, tenant.id)
        assert ei.value.code == "DEVICE_SUSPENDED"

        await svc.revoke(created.id, env["tenant_a"].id)
        with pytest.raises(ForbiddenError) as ei:
            await _load_device(env["db"], device.id, branch.id, tenant.id)
        assert ei.value.code == "DEVICE_REVOKED"
