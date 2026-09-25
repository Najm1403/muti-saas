from __future__ import annotations
# repositories/addon_group_repository.py

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.addon_group import AddonGroup
from models.business import Business


class AddonGroupRepository:
    """Add-on Groups are shared at the Business level, same as Variant Option Groups."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _scoped(self, tenant_id: UUID):
        return (
            select(AddonGroup)
            .join(Business, AddonGroup.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                AddonGroup.deleted_at.is_(None),
            )
        )

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> AddonGroup | None:
        result = await self.db.execute(
            self._scoped(tenant_id).where(AddonGroup.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, business_id: UUID, tenant_id: UUID) -> list[AddonGroup]:
        stmt = self._scoped(tenant_id).where(AddonGroup.business_id == business_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        business_id: UUID,
        name: str,
        selection_type: str = "multiple",
        min_select: int = 0,
        max_select: int | None = None,
    ) -> AddonGroup:
        group = AddonGroup(
            id=uuid4(),
            business_id=business_id,
            name=name,
            selection_type=selection_type,
            min_select=min_select,
            max_select=max_select,
        )
        self.db.add(group)
        await self.db.flush()
        await self.db.refresh(group)
        return group

    async def update(self, id: UUID, tenant_id: UUID, **fields) -> AddonGroup | None:
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
