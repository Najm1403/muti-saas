from __future__ import annotations
# repositories/product_repository.py

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.category import Category
from models.product import Product
from models.business import Business


class ProductRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _scoped(self, tenant_id: UUID):
        """Base stmt scoped to tenant via Product → Category → Business join."""
        return (
            select(Product)
            .join(Category, Product.category_id == Category.id)
            .join(Business, Category.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                Category.deleted_at.is_(None),
                Product.deleted_at.is_(None),
            )
        )

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> Product | None:
        result = await self.db.execute(
            self._scoped(tenant_id)
            .where(Product.id == id)
            .options(
                selectinload(Product.variant_option_groups),
                selectinload(Product.addon_groups),
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        category_id: UUID,
        tenant_id: UUID,
        include_inactive: bool = False,
    ) -> list[Product]:
        stmt = self._scoped(tenant_id).where(Product.category_id == category_id)
        if not include_inactive:
            stmt = stmt.where(Product.is_active.is_(True))
        stmt = stmt.order_by(Product.display_order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_business(
        self,
        business_id: UUID,
        tenant_id: UUID,
        include_inactive: bool = False,
    ) -> list[Product]:
        stmt = self._scoped(tenant_id).where(Category.business_id == business_id)
        if not include_inactive:
            stmt = stmt.where(Product.is_active.is_(True), Category.is_active.is_(True))
        stmt = stmt.order_by(Product.display_order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        category_id: UUID,
        product_code: str,
        name: str,
        **kwargs,
    ) -> Product:
        product = Product(
            id=uuid4(),
            category_id=category_id,
            product_code=product_code,
            name=name,
            **kwargs,
        )
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def update(self, id: UUID, tenant_id: UUID, **fields) -> Product | None:
        product = await self.get_by_id(id, tenant_id)
        if not product:
            return None
        for key, value in fields.items():
            setattr(product, key, value)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def soft_delete(self, id: UUID, tenant_id: UUID) -> bool:
        product = await self.get_by_id(id, tenant_id)
        if not product:
            return False
        product.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True
