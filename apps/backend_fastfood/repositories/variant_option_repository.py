from __future__ import annotations
# repositories/variant_option_repository.py

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.business import Business
from models.variant_option import VariantOption
from models.variant_option_group import VariantOptionGroup


class VariantOptionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _scoped(self, tenant_id: UUID):
        """Base stmt scoped to tenant via VariantOption → VariantOptionGroup → Business."""
        return (
            select(VariantOption)
            .join(VariantOptionGroup, VariantOption.option_group_id == VariantOptionGroup.id)
            .join(Business, VariantOptionGroup.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                VariantOptionGroup.deleted_at.is_(None),
                VariantOption.deleted_at.is_(None),
            )
        )

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> VariantOption | None:
        result = await self.db.execute(
            self._scoped(tenant_id).where(VariantOption.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, option_group_id: UUID, tenant_id: UUID) -> list[VariantOption]:
        stmt = (
            self._scoped(tenant_id)
            .where(VariantOption.option_group_id == option_group_id)
            .order_by(VariantOption.display_order)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        option_group_id: UUID,
        name: str,
        display_order: int = 0,
    ) -> VariantOption:
        option = VariantOption(
            id=uuid4(),
            option_group_id=option_group_id,
            name=name,
            display_order=display_order,
        )
        self.db.add(option)
        await self.db.flush()
        await self.db.refresh(option)
        return option

    async def update(self, id: UUID, tenant_id: UUID, **fields) -> VariantOption | None:
        option = await self.get_by_id(id, tenant_id)
        if not option:
            return None
        for key, value in fields.items():
            setattr(option, key, value)
        await self.db.flush()
        await self.db.refresh(option)
        return option

    async def soft_delete(self, id: UUID, tenant_id: UUID) -> bool:
        option = await self.get_by_id(id, tenant_id)
        if not option:
            return False
        option.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True
