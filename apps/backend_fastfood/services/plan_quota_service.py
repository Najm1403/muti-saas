"""Authoritative subscription-plan quota checks for tenant-owned resources."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError
from models.branch import Branch
from models.business import Business
from models.tenant import Tenant
from repositories.subscription_repository import SubscriptionRepository


_NO_PLAN_BRANCH_ALLOWANCE = 1


async def enforce_branch_creation_quota(db: AsyncSession, tenant_id: UUID) -> None:
    """Reject creation when the tenant already consumes its branch allowance.

    Every non-deleted branch consumes a slot, including inactive branches. The
    tenant row is locked until commit so tenant and platform creation requests
    cannot race each other past the limit.
    """
    tenant = await db.scalar(
        select(Tenant)
        .where(Tenant.id == tenant_id, Tenant.deleted_at.is_(None))
        .with_for_update()
    )
    if not tenant:
        raise NotFoundError("Tenant not found.")

    subscription = await SubscriptionRepository(db).get_active_for_tenant(tenant_id)
    limit = (
        subscription.plan.max_branches
        if subscription and subscription.plan
        else _NO_PLAN_BRANCH_ALLOWANCE
    )
    if limit == -1:
        return

    used = await db.scalar(
        select(func.count(Branch.id))
        .join(Business, Branch.business_id == Business.id)
        .where(
            Business.tenant_id == tenant_id,
            Business.deleted_at.is_(None),
            Branch.deleted_at.is_(None),
        )
    ) or 0
    if used >= limit:
        raise ConflictError(
            f"Branch limit reached ({limit}). Upgrade the plan or delete an "
            "unused branch before adding another."
        )
