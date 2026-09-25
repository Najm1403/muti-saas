# services/category_service.py

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError
from repositories.category_repository import CategoryRepository
from repositories.business_repository import BusinessRepository
from schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate


class CategoryService:
    """
    Manages categories under a business, scoped to a tenant.

    Hierarchy enforced:
        tenant_id → business_id → category
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = CategoryRepository(db)
        self.business_repo = BusinessRepository(db)

    async def _verify_business(self, business_id: UUID, tenant_id: UUID) -> None:
        if not await self.business_repo.get_by_id(business_id, tenant_id):
            raise NotFoundError("Business not found.")

    async def create(
        self, business_id: UUID, tenant_id: UUID, data: CategoryCreate
    ) -> CategoryResponse:
        await self._verify_business(business_id, tenant_id)
        category = await self.repo.create(
            business_id=business_id,
            name=data.name,
            description=data.description,
            display_order=data.display_order,
        )
        await self.db.commit()
        return CategoryResponse.model_validate(category)

    async def get(self, id: UUID, tenant_id: UUID) -> CategoryResponse:
        category = await self.repo.get_by_id(id, tenant_id)
        if not category:
            raise NotFoundError("Category not found.")
        return CategoryResponse.model_validate(category)

    async def list(
        self,
        business_id: UUID,
        tenant_id: UUID,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CategoryResponse]:
        await self._verify_business(business_id, tenant_id)
        categories = await self.repo.list(
            business_id=business_id,
            tenant_id=tenant_id,
            include_inactive=include_inactive,
        )
        return [CategoryResponse.model_validate(c) for c in categories[skip : skip + limit]]

    async def update(
        self, id: UUID, tenant_id: UUID, data: CategoryUpdate
    ) -> CategoryResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Category not found.")
        category = await self.repo.update(id, tenant_id, **data.model_dump(exclude_unset=True))
        await self.db.commit()
        return CategoryResponse.model_validate(category)

    async def activate(self, id: UUID, tenant_id: UUID) -> CategoryResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Category not found.")
        category = await self.repo.update(id, tenant_id, is_active=True)
        await self.db.commit()
        return CategoryResponse.model_validate(category)

    async def deactivate(self, id: UUID, tenant_id: UUID) -> CategoryResponse:
        if not await self.repo.get_by_id(id, tenant_id):
            raise NotFoundError("Category not found.")
        category = await self.repo.update(id, tenant_id, is_active=False)
        await self.db.commit()
        return CategoryResponse.model_validate(category)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        if not await self.repo.soft_delete(id, tenant_id):
            raise NotFoundError("Category not found.")
        await self.db.commit()
