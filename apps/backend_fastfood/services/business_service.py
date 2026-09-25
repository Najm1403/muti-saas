# services/business_service.py

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError
from repositories.business_repository import BusinessRepository
from schemas.business import BusinessResponse, BusinessUpdate


class BusinessService:
    """
    Manages the tenant's single Business (spec A2 — exactly one per tenant).

    There is deliberately no create() here reachable from the tenant-facing
    API: a Business is created exactly once, during onboarding
    (services/onboarding_service.py).
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = BusinessRepository(db)

    async def get(self, id: UUID, tenant_id: UUID) -> BusinessResponse:
        business = await self.repo.get_by_id(id, tenant_id)
        if not business:
            raise NotFoundError("Business not found.")
        return BusinessResponse.model_validate(business)

    async def get_for_tenant(self, tenant_id: UUID) -> BusinessResponse:
        business = await self.repo.get_by_tenant_id(tenant_id)
        if not business:
            raise NotFoundError("Business not found.")
        return BusinessResponse.model_validate(business)

    async def update(
        self, id: UUID, tenant_id: UUID, data: BusinessUpdate
    ) -> BusinessResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Business not found.")
        business = await self.repo.update(id, tenant_id, **data.model_dump(exclude_unset=True))
        await self.db.commit()
        return BusinessResponse.model_validate(business)

    async def update_logo(self, id: UUID, tenant_id: UUID, logo_path: str) -> BusinessResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Business not found.")
        business = await self.repo.update(id, tenant_id, logo_path=logo_path)
        await self.db.commit()
        return BusinessResponse.model_validate(business)
