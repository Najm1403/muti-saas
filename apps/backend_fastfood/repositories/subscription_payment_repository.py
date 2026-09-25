# repositories/subscription_payment_repository.py

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.subscription import BillingCycle
from models.subscription_payment import SubscriptionPayment


class SubscriptionPaymentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: UUID) -> SubscriptionPayment | None:
        result = await self.db.execute(
            select(SubscriptionPayment).where(SubscriptionPayment.id == id)
        )
        return result.scalar_one_or_none()

    async def list_for_subscription(
        self, subscription_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[SubscriptionPayment]:
        result = await self.db.execute(
            select(SubscriptionPayment)
            .where(SubscriptionPayment.subscription_id == subscription_id)
            .order_by(SubscriptionPayment.paid_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_for_tenant(
        self, tenant_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[SubscriptionPayment]:
        result = await self.db.execute(
            select(SubscriptionPayment)
            .where(SubscriptionPayment.tenant_id == tenant_id)
            .order_by(SubscriptionPayment.paid_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self,
        subscription_id: UUID,
        tenant_id: UUID,
        amount: Decimal,
        billing_cycle: BillingCycle,
        period_start: datetime,
        period_end: datetime,
        payment_method: str,
        paid_at: datetime,
        recorded_by: UUID,
        reference_number: str | None = None,
        notes: str | None = None,
        list_price: Decimal | None = None,
        discount_pct: Decimal | None = None,
        waived: bool = False,
    ) -> SubscriptionPayment:
        payment = SubscriptionPayment(
            id=uuid4(),
            subscription_id=subscription_id,
            tenant_id=tenant_id,
            amount=amount,
            list_price=list_price,
            discount_pct=discount_pct,
            billing_cycle=billing_cycle,
            period_start=period_start,
            period_end=period_end,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes,
            paid_at=paid_at,
            recorded_by=recorded_by,
            waived=waived,
        )
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)
        return payment
