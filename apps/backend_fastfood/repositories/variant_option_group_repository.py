from __future__ import annotations
# repositories/variant_option_group_repository.py

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.business import Business
from models.variant_option_group import VariantOptionGroup


class VariantOptionGroupRepository:
    """
    Variant Option Groups are shared at the Business level (spec Part B) —
    scoped directly via Business, not through any single product.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _scoped(self, tenant_id: UUID):
        return (
            select(VariantOptionGroup)
            .join(Business, VariantOptionGroup.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                VariantOptionGroup.deleted_at.is_(None),
            )
        )

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> VariantOptionGroup | None:
        result = await self.db.execute(
            self._scoped(tenant_id).where(VariantOptionGroup.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, business_id: UUID, tenant_id: UUID) -> list[VariantOptionGroup]:
        stmt = self._scoped(tenant_id).where(VariantOptionGroup.business_id == business_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        business_id: UUID,
        name: str,
        description: str | None = None,
    ) -> VariantOptionGroup:
        group = VariantOptionGroup(
            id=uuid4(),
            business_id=business_id,
            name=name,
            description=description,
        )
        self.db.add(group)
        await self.db.flush()
        await self.db.refresh(group)
        return group

    async def update(self, id: UUID, tenant_id: UUID, **fields) -> VariantOptionGroup | None:
        group = await self.get_by_id(id, tenant_id)
        if not group:
            return None
        for key, value in fields.items():
            setattr(group, key, value)
        await self.db.flush()
        await self.db.refresh(group)
        return group

    async def soft_delete(self, id: UUID, tenant_id: UUID) -> bool:
        group = await self.get_by_id(id, tenant_id)
        if not group:
            return False
        group.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True
