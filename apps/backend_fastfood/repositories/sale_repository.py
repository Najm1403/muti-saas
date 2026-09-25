from __future__ import annotations
# repositories/sale_repository.py

import uuid
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.branch import Branch
from models.product import Product
from models.business import Business
from models.sale import Sale
from models.sale_item import SaleItem
from models.sale_item_option import SaleItemOption
from schemas.sale import SaleCreate


class SaleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _scoped(self, tenant_id: UUID):
        """Base stmt scoped to tenant via Sale → Branch → Business join."""
        return (
            select(Sale)
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                Branch.deleted_at.is_(None),
                Sale.deleted_at.is_(None),
            )
        )

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> Sale | None:
        result = await self.db.execute(
            self._scoped(tenant_id)
            .where(Sale.id == id)
            .options(
                selectinload(Sale.user),
                selectinload(Sale.items).selectinload(SaleItem.options),
                selectinload(Sale.payments),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_number(
        self, branch_id: UUID, sale_number: str, tenant_id: UUID
    ) -> Sale | None:
        result = await self.db.execute(
            self._scoped(tenant_id).where(
                Sale.branch_id == branch_id,
                Sale.sale_number == sale_number,
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        branch_id: UUID,
        tenant_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        status: str | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Sale]:
        stmt = (
            self._scoped(tenant_id)
            .where(Sale.branch_id == branch_id)
            .options(selectinload(Sale.user))
        )
        if date_from:
            stmt = stmt.where(Sale.sold_at >= date_from)
        if date_to:
            stmt = stmt.where(Sale.sold_at <= date_to)
        if status:
            stmt = stmt.where(Sale.status == status)
        if user_id:
            stmt = stmt.where(Sale.user_id == user_id)
        if session_id:
            stmt = stmt.where(Sale.session_id == session_id)
        stmt = stmt.order_by(Sale.sold_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _station_map(self, product_ids: list[uuid.UUID]) -> dict[uuid.UUID, uuid.UUID | None]:
        """Batch-fetch preparation_station_id for each product to avoid N+1 queries."""
        if not product_ids:
            return {}
        result = await self.db.execute(
            select(Product.id, Product.preparation_station_id).where(
                Product.id.in_(product_ids)
            )
        )
        return {row[0]: row[1] for row in result.all()}

    async def create(self, data: SaleCreate) -> Sale:
        sale = Sale(
            id=data.id or uuid4(),
            branch_id=data.branch_id,
            device_id=data.device_id,
            user_id=data.user_id,
            sale_number=data.sale_number,
            sold_at=data.sold_at,
            subtotal=data.subtotal,
            discount=data.discount,
            tax_amount=data.tax_amount,
            tax_rate=data.tax_rate,
            total=data.total,
            status=data.status,
            order_status=data.order_status,
            promotion_id=data.promotion_id,
            deal_id=data.deal_id,
        )
        self.db.add(sale)
        await self.db.flush()

        station_map = await self._station_map([i.product_id for i in data.items])

        for item_data in data.items:
            item = SaleItem(
                id=item_data.id or uuid4(),
                sale_id=sale.id,
                product_id=item_data.product_id,
                variant_id=item_data.variant_id,
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                discount=item_data.discount,
                total=item_data.total,
                preparation_status="PENDING" if station_map.get(item_data.product_id) else None,
                kitchen_station_id=station_map.get(item_data.product_id),
            )
            self.db.add(item)
            await self.db.flush()

            for opt_data in item_data.options:
                self.db.add(SaleItemOption(
                    id=opt_data.id or uuid4(),
                    sale_item_id=item.id,
                    variant_option_id=opt_data.variant_option_id,
                    option_name=opt_data.option_name,
                ))

        await self.db.flush()
        await self.db.refresh(sale)
        return sale

    async def update_status(
        self, id: UUID, tenant_id: UUID, status: str
    ) -> Sale | None:
        sale = await self.get_by_id(id, tenant_id)
        if not sale:
            return None
        sale.status = status
        await self.db.flush()
        await self.db.refresh(sale)
        return sale

    async def soft_delete(self, id: UUID, tenant_id: UUID) -> bool:
        sale = await self.get_by_id(id, tenant_id)
        if not sale:
            return False
        sale.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True
