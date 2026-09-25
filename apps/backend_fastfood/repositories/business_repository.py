from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.business import Business


class BusinessRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> Business | None:
        stmt = select(Business).where(
            Business.id == id,
            Business.tenant_id == tenant_id,
            Business.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_tenant_id(self, tenant_id: UUID) -> Business | None:
        """The primary lookup — a tenant has exactly one Business (spec A2)."""
        stmt = select(Business).where(
            Business.tenant_id == tenant_id,
            Business.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        tenant_id: UUID,
        name: str,
        is_active: bool = True,
        currency: str = "Rs.",
    ) -> Business:
        business = Business(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            is_active=is_active,
            currency=currency,
        )
        self.db.add(business)
        await self.db.flush()
        await self.db.refresh(business)
        return business

    async def update(self, id: UUID, tenant_id: UUID, **fields) -> Business | None:
        business = await self.get_by_id(id, tenant_id)
        if not business:
            return None
        for key, value in fields.items():
            setattr(business, key, value)
        await self.db.flush()
        await self.db.refresh(business)
        return business

    async def soft_delete(self, id: UUID, tenant_id: UUID) -> bool:
        business = await self.get_by_id(id, tenant_id)
        if not business:
            return False
        business.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True
