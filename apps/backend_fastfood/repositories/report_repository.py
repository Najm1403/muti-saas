from __future__ import annotations
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from models.payment import Payment
from models.product import Product
from models.sale import Sale
from models.sale_item import SaleItem
from models.user import User


_COMPLETED = "COMPLETED"


class ReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_sale_conditions(self, branch_id: UUID, date_from: datetime, date_to: datetime):
        return [
            Sale.branch_id == branch_id,
            Sale.status == _COMPLETED,
            Sale.deleted_at.is_(None),
            Sale.sold_at >= date_from,
            Sale.sold_at <= date_to,
        ]

    async def sales_summary(
        self, branch_id: UUID, date_from: datetime, date_to: datetime
    ) -> dict:
        conditions = self._base_sale_conditions(branch_id, date_from, date_to)
        stmt = select(
            func.count(Sale.id).label("total_transactions"),
            func.coalesce(func.sum(Sale.subtotal), 0).label("total_subtotal"),
            func.coalesce(func.sum(Sale.discount), 0).label("total_discount"),
            func.coalesce(func.sum(Sale.total), 0).label("total_revenue"),
        ).where(*conditions)
        result = await self.db.execute(stmt)
        row = result.one()
        return {
            "total_transactions": row.total_transactions,
            "total_subtotal": row.total_subtotal,
            "total_discount": row.total_discount,
            "total_revenue": row.total_revenue,
        }

    async def daily_sales(
        self, branch_id: UUID, date_from: datetime, date_to: datetime
    ) -> list[dict]:
        conditions = self._base_sale_conditions(branch_id, date_from, date_to)
        sale_date = func.date(Sale.sold_at).label("sale_date")
        stmt = (
            select(
                sale_date,
                func.count(Sale.id).label("total_transactions"),
                func.coalesce(func.sum(Sale.total), 0).label("total_revenue"),
            )
            .where(*conditions)
            .group_by(func.date(Sale.sold_at))
            .order_by(func.date(Sale.sold_at))
        )
        result = await self.db.execute(stmt)
        return [
            {
                "sale_date": row.sale_date,
                "total_transactions": row.total_transactions,
                "total_revenue": row.total_revenue,
            }
            for row in result.all()
        ]

    async def top_products(
        self, branch_id: UUID, date_from: datetime, date_to: datetime, limit: int = 10
    ) -> list[dict]:
        conditions = self._base_sale_conditions(branch_id, date_from, date_to)
        stmt = (
            select(
                SaleItem.product_id,
                SaleItem.product_name,
                func.sum(SaleItem.quantity).label("total_quantity"),
                func.sum(SaleItem.total).label("total_revenue"),
            )
            .join(Sale, SaleItem.sale_id == Sale.id)
            .where(*conditions, SaleItem.deleted_at.is_(None))
            .group_by(SaleItem.product_id, SaleItem.product_name)
            .order_by(func.sum(SaleItem.total).desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return [
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "total_quantity": row.total_quantity,
                "total_revenue": row.total_revenue,
            }
            for row in result.all()
        ]

    async def cashier_sales(
        self, branch_id: UUID, date_from: datetime, date_to: datetime
    ) -> list[dict]:
        conditions = self._base_sale_conditions(branch_id, date_from, date_to)
        stmt = (
            select(
                Sale.user_id,
                User.full_name.label("cashier_name"),
                func.count(Sale.id).label("total_transactions"),
                func.coalesce(func.sum(Sale.total), 0).label("total_revenue"),
            )
            .join(User, Sale.user_id == User.id)
            .where(*conditions)
            .group_by(Sale.user_id, User.full_name)
            .order_by(func.sum(Sale.total).desc())
        )
        result = await self.db.execute(stmt)
        return [
            {
                "user_id": row.user_id,
                "cashier_name": row.cashier_name,
                "total_transactions": row.total_transactions,
                "total_revenue": row.total_revenue,
            }
            for row in result.all()
        ]

    async def payment_methods(
        self, branch_id: UUID, date_from: datetime, date_to: datetime
    ) -> list[dict]:
        conditions = self._base_sale_conditions(branch_id, date_from, date_to)
        stmt = (
            select(
                Payment.payment_method,
                func.count(Payment.id).label("total_transactions"),
                func.coalesce(func.sum(Payment.amount), 0).label("total_amount"),
            )
            .join(Sale, Payment.sale_id == Sale.id)
            .where(*conditions, Payment.deleted_at.is_(None))
            .group_by(Payment.payment_method)
            .order_by(func.sum(Payment.amount).desc())
        )
        result = await self.db.execute(stmt)
        return [
            {
                "payment_method": row.payment_method,
                "total_transactions": row.total_transactions,
                "total_amount": row.total_amount,
            }
            for row in result.all()
        ]
