from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio

from core.exceptions import ConflictError
from models.branch import Branch
from models.business import Business
from models.plan import Plan
from models.subscription import BillingCycle, SubscriptionStatus
from repositories.subscription_repository import SubscriptionRepository
from schemas.branch import BranchCreate
from schemas.onboarding import BranchPlatformCreate
from services.branch_service import BranchService
from services.onboarding_service import OnboardingService


@pytest_asyncio.fixture
async def branch_env(db, two_tenants):
    tenant = two_tenants["tenant_a"]
    business = Business(
        id=uuid4(), tenant_id=tenant.id, name="Quota Shop", is_active=True
    )
    initial = Branch(
        id=uuid4(), business_id=business.id, branch_code="MAIN",
        name="Main", is_active=True,
    )
    db.add_all([business, initial])
    await db.flush()
    return {"db": db, "tenant": tenant, "business": business, "initial": initial}


async def give_plan(env, max_branches: int) -> None:
    plan = Plan(
        id=uuid4(), name=f"Branch-{max_branches}-{uuid4().hex[:6]}",
        price_monthly=1, price_yearly=10,
        max_restaurants=1, max_branches=max_branches,
        max_users=5, max_devices=2, is_active=True,
    )
    env["db"].add(plan)
    await env["db"].flush()
    now = datetime.now(timezone.utc)
    await SubscriptionRepository(env["db"]).create(
        tenant_id=env["tenant"].id,
        plan_id=plan.id,
        billing_cycle=BillingCycle.MONTHLY,
        status=SubscriptionStatus.ACTIVE,
        started_at=now,
        expires_at=now + timedelta(days=30),
    )
    await env["db"].flush()


def branch_data(code: str) -> BranchCreate:
    return BranchCreate(branch_code=code, name=f"Branch {code}")


class TestBranchQuota:
    @pytest.mark.asyncio
    async def test_no_plan_allows_only_initial_branch(self, branch_env):
        with pytest.raises(ConflictError, match="Branch limit reached \\(1\\)"):
            await BranchService(branch_env["db"]).create(
                branch_env["business"].id,
                branch_env["tenant"].id,
                branch_data("SECOND"),
            )

    @pytest.mark.asyncio
    async def test_plan_limit_is_enforced(self, branch_env):
        await give_plan(branch_env, max_branches=2)
        service = BranchService(branch_env["db"])
        await service.create(
            branch_env["business"].id,
            branch_env["tenant"].id,
            branch_data("SECOND"),
        )
        with pytest.raises(ConflictError, match="Branch limit reached \\(2\\)"):
            await service.create(
                branch_env["business"].id,
                branch_env["tenant"].id,
                branch_data("THIRD"),
            )

    @pytest.mark.asyncio
    async def test_unlimited_plan_allows_more_branches(self, branch_env):
        await give_plan(branch_env, max_branches=-1)
        service = BranchService(branch_env["db"])
        for number in range(3):
            await service.create(
                branch_env["business"].id,
                branch_env["tenant"].id,
                branch_data(f"EXTRA{number}"),
            )

    @pytest.mark.asyncio
    async def test_inactive_branch_still_consumes_slot(self, branch_env):
        branch_env["initial"].is_active = False
        await branch_env["db"].flush()
        with pytest.raises(ConflictError):
            await BranchService(branch_env["db"]).create(
                branch_env["business"].id,
                branch_env["tenant"].id,
                branch_data("SECOND"),
            )

    @pytest.mark.asyncio
    async def test_deleted_branch_frees_slot(self, branch_env):
        await BranchService(branch_env["db"]).delete(
            branch_env["initial"].id, branch_env["tenant"].id
        )
        created = await BranchService(branch_env["db"]).create(
            branch_env["business"].id,
            branch_env["tenant"].id,
            branch_data("REPLACEMENT"),
        )
        assert created.branch_code == "REPLACEMENT"

    @pytest.mark.asyncio
    async def test_platform_creation_cannot_bypass_limit(self, branch_env):
        with pytest.raises(ConflictError, match="Branch limit reached \\(1\\)"):
            await OnboardingService(branch_env["db"]).create_tenant_branch(
                branch_env["tenant"].id,
                BranchPlatformCreate(name="Platform branch", branch_code="PLATFORM"),
            )
