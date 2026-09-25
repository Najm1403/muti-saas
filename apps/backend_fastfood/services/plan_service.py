# services/plan_service.py

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError
from repositories.plan_repository import PlanRepository
from schemas.plan import PlanCreate, PlanResponse, PlanUpdate


class PlanService:
    """CRUD for subscription plans. Plans are platform-global — no tenant scoping."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PlanRepository(db)

    async def create(self, data: PlanCreate) -> PlanResponse:
        if await self.repo.get_by_name(data.name):
            raise ConflictError(f"A plan named '{data.name}' already exists.")
        plan = await self.repo.create(
            name=data.name,
            description=data.description,
            price_monthly=data.price_monthly,
            price_yearly=data.price_yearly,
            discount_monthly_pct=data.discount_monthly_pct,
            discount_yearly_pct=data.discount_yearly_pct,
            max_restaurants=data.max_restaurants,
            max_branches=data.max_branches,
            max_users=data.max_users,
            max_devices=data.max_devices,
        )
        await self.db.commit()
        return PlanResponse.model_validate(plan)

    async def get(self, id: UUID) -> PlanResponse:
        plan = await self.repo.get_by_id(id)
        if not plan:
            raise NotFoundError("Plan not found.")
        return PlanResponse.model_validate(plan)

    async def list(self, include_inactive: bool = False, skip: int = 0, limit: int = 50) -> list[PlanResponse]:
        plans = await self.repo.list(include_inactive=include_inactive, skip=skip, limit=limit)
        return [PlanResponse.model_validate(p) for p in plans]

    async def update(self, id: UUID, data: PlanUpdate) -> PlanResponse:
        plan = await self.repo.get_by_id(id)
        if not plan:
            raise NotFoundError("Plan not found.")
        if data.name and data.name != plan.name:
            if await self.repo.get_by_name(data.name):
                raise ConflictError(f"A plan named '{data.name}' already exists.")
        fields = data.model_dump(exclude_unset=True)
        plan = await self.repo.update(id, **fields)
        await self.db.commit()
        return PlanResponse.model_validate(plan)

    async def delete(self, id: UUID) -> None:
        plan = await self.repo.get_by_id(id)
        if not plan:
            raise NotFoundError("Plan not found.")
        await self.repo.update(id, deleted_at=datetime.now(timezone.utc), is_active=False)
        await self.db.commit()
