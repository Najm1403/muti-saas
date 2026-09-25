# services/addon_item_service.py

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError
from repositories.addon_group_repository import AddonGroupRepository
from repositories.addon_item_repository import AddonItemRepository
from schemas.addon_item import AddonItemCreate, AddonItemResponse, AddonItemUpdate


class AddonItemService:
    """
    Manages items under an Add-on Group, scoped to a tenant.

    Hierarchy enforced:
        tenant_id → business → addon_group → addon_item
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AddonItemRepository(db)
        self.group_repo = AddonGroupRepository(db)

    async def _verify_group(self, addon_group_id: UUID, tenant_id: UUID) -> None:
        if not await self.group_repo.get_by_id(addon_group_id, tenant_id):
            raise NotFoundError("Add-on group not found.")

    async def create(
        self, addon_group_id: UUID, tenant_id: UUID, data: AddonItemCreate
    ) -> AddonItemResponse:
        await self._verify_group(addon_group_id, tenant_id)
        item = await self.repo.create(
            addon_group_id=addon_group_id,
            name=data.name,
            price_delta=data.price_delta,
            default_selected=data.default_selected,
            display_order=data.display_order,
        )
        await self.db.commit()
        return AddonItemResponse.model_validate(item)

    async def get(self, id: UUID, tenant_id: UUID) -> AddonItemResponse:
        item = await self.repo.get_by_id(id, tenant_id)
        if not item:
            raise NotFoundError("Add-on item not found.")
        return AddonItemResponse.model_validate(item)

    async def list(
        self, addon_group_id: UUID, tenant_id: UUID
    ) -> list[AddonItemResponse]:
        await self._verify_group(addon_group_id, tenant_id)
        items = await self.repo.list(addon_group_id=addon_group_id, tenant_id=tenant_id)
        return [AddonItemResponse.model_validate(i) for i in items]

    async def update(
        self, id: UUID, tenant_id: UUID, data: AddonItemUpdate
    ) -> AddonItemResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Add-on item not found.")
        item = await self.repo.update(id, tenant_id, **data.model_dump(exclude_unset=True))
        await self.db.commit()
        return AddonItemResponse.model_validate(item)

    async def activate(self, id: UUID, tenant_id: UUID) -> AddonItemResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Add-on item not found.")
        item = await self.repo.update(id, tenant_id, is_active=True)
        await self.db.commit()
        return AddonItemResponse.model_validate(item)

    async def deactivate(self, id: UUID, tenant_id: UUID) -> AddonItemResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Add-on item not found.")
        item = await self.repo.update(id, tenant_id, is_active=False)
        await self.db.commit()
        return AddonItemResponse.model_validate(item)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        if not await self.repo.soft_delete(id, tenant_id):
            raise NotFoundError("Add-on item not found.")
        await self.db.commit()
