from __future__ import annotations
# repositories/refund_repository.py

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.branch import Branch
from models.refund import Refund
from models.refund_item import RefundItem
from models.business import Business
from schemas.refund import RefundCreate


class RefundRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _scoped(self, tenant_id: UUID):
        """Base stmt scoped to tenant via Refund → Branch → Business join."""
        return (
            select(Refund)
            .join(Branch, Refund.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                Branch.deleted_at.is_(None),
                Refund.deleted_at.is_(None),
            )
        )

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> Refund | None:
        result = await self.db.execute(
            self._scoped(tenant_id)
            .where(Refund.id == id)
            .options(selectinload(Refund.items))
        )
        return result.scalar_one_or_none()

    async def get_by_sale(self, sale_id: UUID, tenant_id: UUID) -> list[Refund]:
        result = await self.db.execute(
            self._scoped(tenant_id).where(Refund.sale_id == sale_id)
        )
        return list(result.scalars().all())

    async def list(
        self, branch_id: UUID, tenant_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[Refund]:
        stmt = (
            self._scoped(tenant_id)
            .where(Refund.branch_id == branch_id)
            .order_by(Refund.refunded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, data: RefundCreate) -> Refund:
        refund = Refund(
            id=data.id or uuid4(),
            sale_id=data.sale_id,
            branch_id=data.branch_id,
            device_id=data.device_id,
            refund_number=data.refund_number,
            refunded_at=data.refunded_at,
            amount=data.amount,
            refund_method=data.refund_method,
            reason=data.reason,
        )
        self.db.add(refund)
        await self.db.flush()

        for item_data in data.items:
            self.db.add(RefundItem(
                id=uuid4(),
                refund_id=refund.id,
                sale_item_id=item_data.sale_item_id,
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                amount=item_data.amount,
            ))

        await self.db.flush()
        await self.db.refresh(refund)
        return refund
