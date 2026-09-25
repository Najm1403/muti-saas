from __future__ import annotations
# repositories/addon_item_repository.py

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.addon_group import AddonGroup
from models.addon_item import AddonItem
from models.business import Business


class AddonItemRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _scoped(self, tenant_id: UUID):
        return (
            select(AddonItem)
            .join(AddonGroup, AddonItem.addon_group_id == AddonGroup.id)
            .join(Business, AddonGroup.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                AddonGroup.deleted_at.is_(None),
                AddonItem.deleted_at.is_(None),
            )
        )

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> AddonItem | None:
        result = await self.db.execute(
            self._scoped(tenant_id).where(AddonItem.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, addon_group_id: UUID, tenant_id: UUID) -> list[AddonItem]:
        stmt = (
            self._scoped(tenant_id)
            .where(AddonItem.addon_group_id == addon_group_id)
            .order_by(AddonItem.display_order)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        addon_group_id: UUID,
        name: str,
        price_delta: Decimal = Decimal("0.00"),
        default_selected: bool = False,
        display_order: int = 0,
    ) -> AddonItem:
        item = AddonItem(
            id=uuid4(),
            addon_group_id=addon_group_id,
            name=name,
            price_delta=price_delta,
            default_selected=default_selected,
            display_order=display_order,
        )
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update(self, id: UUID, tenant_id: UUID, **fields) -> AddonItem | None:
        item = await self.get_by_id(id, tenant_id)
        if not item:
            return None
        for key, value in fields.items():
            setattr(item, key, value)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def soft_delete(self, id: UUID, tenant_id: UUID) -> bool:
        item = await self.get_by_id(id, tenant_id)
        if not item:
            return False
        item.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True
