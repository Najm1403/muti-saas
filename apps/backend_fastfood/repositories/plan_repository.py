# repositories/plan_repository.py

from __future__ import annotations

from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.plan import Plan


class PlanRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: UUID) -> Plan | None:
        result = await self.db.execute(
            select(Plan).where(Plan.id == id, Plan.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Plan | None:
        result = await self.db.execute(
            select(Plan).where(Plan.name == name, Plan.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list(self, include_inactive: bool = False, skip: int = 0, limit: int = 50) -> list[Plan]:
        stmt = select(Plan).where(Plan.deleted_at.is_(None))
        if not include_inactive:
            stmt = stmt.where(Plan.is_active.is_(True))
        stmt = stmt.order_by(Plan.price_monthly).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        name: str,
        price_monthly: Decimal,
        price_yearly: Decimal,
        max_restaurants: int,
        max_branches: int,
        max_users: int,
        max_devices: int,
        description: str | None = None,
        discount_monthly_pct: Decimal = Decimal("0"),
        discount_yearly_pct: Decimal = Decimal("0"),
    ) -> Plan:
        plan = Plan(
            id=uuid4(),
            name=name,
            description=description,
            price_monthly=price_monthly,
            price_yearly=price_yearly,
            discount_monthly_pct=discount_monthly_pct,
            discount_yearly_pct=discount_yearly_pct,
            max_restaurants=max_restaurants,
            max_branches=max_branches,
            max_users=max_users,
            max_devices=max_devices,
        )
        self.db.add(plan)
        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    async def update(self, id: UUID, **fields) -> Plan | None:
        plan = await self.get_by_id(id)
        if not plan:
            return None
        for key, value in fields.items():
            setattr(plan, key, value)
        await self.db.flush()
        await self.db.refresh(plan)
        return plan
