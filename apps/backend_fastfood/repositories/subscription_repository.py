# repositories/subscription_repository.py

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.subscription import BillingCycle, Subscription, SubscriptionStatus


class SubscriptionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _with_relations(self):
        return selectinload(Subscription.plan), selectinload(Subscription.tenant)

    async def get_by_id(self, id: UUID) -> Subscription | None:
        result = await self.db.execute(
            select(Subscription)
            .where(Subscription.id == id)
            .options(*self._with_relations())
        )
        return result.scalar_one_or_none()

    async def get_active_for_tenant(self, tenant_id: UUID) -> Subscription | None:
        """Return the current ACTIVE/TRIAL/PAST_DUE subscription for a tenant.

        PAST_DUE is a deliberate warning-only stage (see SubscriptionService.
        evaluate_and_sync()) — access is not restricted, so everywhere this
        method's callers treat "has an active subscription" as true for
        ACTIVE/TRIAL must also treat PAST_DUE the same way, or a tenant in
        their grace period would wrongly appear to have no subscription at
        all (e.g. device activation, their own subscription-summary view).
        SUSPENDED/CANCELLED are intentionally excluded — those ARE meant to
        read as "no current subscription" to callers using this method.
        """
        result = await self.db.execute(
            select(Subscription)
            .where(
                Subscription.tenant_id == tenant_id,
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIAL,
                    SubscriptionStatus.PAST_DUE,
                ]),
            )
            .options(selectinload(Subscription.plan))
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        status: SubscriptionStatus | None = None,
        tenant_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Subscription]:
        stmt = select(Subscription).options(*self._with_relations())
        if status:
            stmt = stmt.where(Subscription.status == status)
        if tenant_id:
            stmt = stmt.where(Subscription.tenant_id == tenant_id)
        stmt = stmt.order_by(Subscription.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        tenant_id: UUID,
        plan_id: UUID,
        billing_cycle: BillingCycle,
        status: SubscriptionStatus,
        started_at: datetime,
        expires_at: datetime,
        trial_ends_at: datetime | None = None,
        discount_pct: Decimal | None = None,
    ) -> Subscription:
        sub = Subscription(
            id=uuid4(),
            tenant_id=tenant_id,
            plan_id=plan_id,
            billing_cycle=billing_cycle,
            status=status,
            started_at=started_at,
            expires_at=expires_at,
            trial_ends_at=trial_ends_at,
            discount_pct=discount_pct,
        )
        self.db.add(sub)
        await self.db.flush()
        await self.db.refresh(sub)
        return sub

    async def update(self, id: UUID, **fields) -> Subscription | None:
        sub = await self.get_by_id(id)
        if not sub:
            return None
        for key, value in fields.items():
            setattr(sub, key, value)
        await self.db.flush()
        await self.db.refresh(sub)
        return sub
