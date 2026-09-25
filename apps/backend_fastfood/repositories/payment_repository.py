from __future__ import annotations
# repositories/payment_repository.py

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.branch import Branch
from models.payment import Payment
from models.business import Business
from models.sale import Sale
from schemas.payment import PaymentCreate


class PaymentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _scoped(self, tenant_id: UUID):
        """Base stmt scoped to tenant via Payment → Sale → Branch → Business join."""
        return (
            select(Payment)
            .join(Sale, Payment.sale_id == Sale.id)
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                Business.deleted_at.is_(None),
                Branch.deleted_at.is_(None),
                Sale.deleted_at.is_(None),
                Payment.deleted_at.is_(None),
            )
        )

    async def get_by_id(self, id: UUID, tenant_id: UUID) -> Payment | None:
        result = await self.db.execute(
            self._scoped(tenant_id).where(Payment.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_sale(self, sale_id: UUID, tenant_id: UUID) -> list[Payment]:
        result = await self.db.execute(
            self._scoped(tenant_id).where(Payment.sale_id == sale_id)
        )
        return list(result.scalars().all())

    async def create(self, data: PaymentCreate) -> Payment:
        payment = Payment(
            id=data.id or uuid4(),
            sale_id=data.sale_id,
            payment_method=data.payment_method,
            amount=data.amount,
            reference=data.reference,
        )
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment
