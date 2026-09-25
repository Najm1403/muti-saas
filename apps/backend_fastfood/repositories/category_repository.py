from __future__ import annotations
# repositories/category_repository.py

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.category import Category
from models.business import Business


class CategoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _scoped(self, tenant_id: UUID):
        """Base stmt scoped to tenant via Category → Business join."""
        return (
            select(Category)
            .join(Business, Category.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                Category.deleted_at.is_(None),
            )
        )

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> Category | None:
        result = await self.db.execute(
            self._scoped(tenant_id).where(Category.id == id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        business_id: UUID,
        tenant_id: UUID,
        include_inactive: bool = False,
    ) -> list[Category]:
        stmt = self._scoped(tenant_id).where(Category.business_id == business_id)
        if not include_inactive:
            stmt = stmt.where(Category.is_active.is_(True))
        stmt = stmt.order_by(Category.display_order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        business_id: UUID,
        name: str,
        description: str | None = None,
        display_order: int = 0,
    ) -> Category:
        category = Category(
            id=uuid4(),
            business_id=business_id,
            name=name,
            description=description,
            display_order=display_order,
        )
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def update(self, id: UUID, tenant_id: UUID, **fields) -> Category | None:
        category = await self.get_by_id(id, tenant_id)
        if not category:
            return None
        for key, value in fields.items():
            setattr(category, key, value)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def soft_delete(self, id: UUID, tenant_id: UUID) -> bool:
        category = await self.get_by_id(id, tenant_id)
        if not category:
            return False
        category.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True
