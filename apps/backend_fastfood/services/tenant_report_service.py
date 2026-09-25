# services/tenant_report_service.py
#
# Async SQLAlchemy service for tenant-level sales analytics.
# All queries are scoped to a tenant via the Branch → Business → Tenant chain.
# Revenue figures only include COMPLETED sales; other statuses are counted separately.

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Integer, func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from core.payment_methods import PAYMENT_METHODS, label_lenient
from models.branch import Branch
from models.payment import Payment
from models.business import Business
from models.refund import Refund
from models.refund_item import RefundItem
from models.sale import Sale
from models.sale_item import SaleItem
from models.user import User
from schemas.tenant_report import (
    BranchSalesItem,
    CashierSalesItem,
    DailySalesPoint,
    MonthlySalesPoint,
    PaymentMethodBreakdownItem,
    PaymentMethodPoint,
    RefundsSummary,
    ReturnedProductItem,
    SalesSummary,
    TopProductItem,
    YearComparisonMonthPoint,
    YearComparisonPoint,
    YearlySalesPoint,
)

# Sale statuses
_COMPLETED = "COMPLETED"
_CANCELLED = "CANCELLED"
_REFUNDED = "REFUNDED"


def _branch_tenant_joins():
    """
    Return the join conditions used to link Sale → Branch → Business
    so that tenant_id filtering is possible.
    """
    return (
        Branch,
        Sale.branch_id == Branch.id,
        Business,
        Branch.business_id == Business.id,
    )


class TenantReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ──────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────

    def _revenue_expr(self):
        """A COMPLETED sale's revenue, net of any COMPLETED refunds/returns
        against it. A partial return leaves Sale.status == 'COMPLETED'
        (services/pos_return_service.py) and never adjusts Sale.total, so
        summing the raw column overstates revenue by the returned amount
        until a sale is 100% returned (which flips it to REFUNDED and is
        already excluded by the COMPLETED filter below). Returns a single
        case() expression object — callers must reuse the SAME object in
        both SELECT and any ORDER BY/GROUP BY that repeats it, the same
        convention already used for month_col/period_expr in this file, or
        Postgres will treat two structurally-identical scalar-subquery calls
        as distinct bound parameters.
        """
        refunded = (
            select(func.coalesce(func.sum(Refund.amount), Decimal("0.00")))
            .where(
                Refund.sale_id == Sale.id,
                Refund.status == "COMPLETED",
                Refund.deleted_at.is_(None),
            )
            .correlate(Sale)
            .scalar_subquery()
        )
        return case((Sale.status == _COMPLETED, Sale.total - refunded), else_=Decimal("0.00"))

    def _base_filters(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        branch_id: UUID | None,
        allowed_branch_ids: set[UUID] | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ):
        """Build the common WHERE clauses shared by all report queries."""
        filters = [
            Business.tenant_id == tenant_id,
            Business.deleted_at.is_(None),
            Branch.deleted_at.is_(None),
            Sale.deleted_at.is_(None),
        ]
        if date_from is not None:
            filters.append(Sale.sold_at >= date_from)
        if date_to is not None:
            filters.append(Sale.sold_at <= date_to)
        if branch_id is not None:
            filters.append(Sale.branch_id == branch_id)
        if allowed_branch_ids is not None:
            filters.append(Sale.branch_id.in_(allowed_branch_ids))
        if user_id is not None:
            filters.append(Sale.user_id == user_id)
        if session_id is not None:
            filters.append(Sale.session_id == session_id)
        return filters

    # ──────────────────────────────────────────────────────────────
    # 1. Summary
    # ──────────────────────────────────────────────────────────────

    async def get_summary(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        branch_id: UUID | None,
        allowed_branch_ids: set[UUID] | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> SalesSummary:
        filters = self._base_filters(tenant_id, date_from, date_to, branch_id, allowed_branch_ids, user_id, session_id)
        revenue_expr = self._revenue_expr()

        q = await self.db.execute(
            select(
                func.count(Sale.id).label("total_sales"),
                func.count(
                    case((Sale.status == _COMPLETED, Sale.id))
                ).label("completed_sales"),
                func.count(
                    case((Sale.status == _CANCELLED, Sale.id))
                ).label("cancelled_sales"),
                func.count(
                    case((Sale.status == _REFUNDED, Sale.id))
                ).label("refunded_sales"),
                func.coalesce(
                    func.sum(revenue_expr),
                    Decimal("0.00"),
                ).label("total_revenue"),
                func.coalesce(
                    func.sum(case((Sale.status == _COMPLETED, Sale.discount), else_=Decimal("0.00"))),
                    Decimal("0.00"),
                ).label("total_discount"),
                func.coalesce(
                    func.sum(case((Sale.status == _COMPLETED, Sale.tax_amount), else_=Decimal("0.00"))),
                    Decimal("0.00"),
                ).label("total_tax"),
            )
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(*filters)
        )
        row = q.one()

        total_revenue = Decimal(str(row.total_revenue or "0.00"))
        completed = row.completed_sales or 0
        avg = (total_revenue / completed) if completed else Decimal("0.00")

        refunds = await self.get_refunds_summary(
            tenant_id, date_from, date_to, branch_id, allowed_branch_ids, user_id, session_id,
        )

        return SalesSummary(
            date_from=date_from.date().isoformat() if date_from else None,
            date_to=date_to.date().isoformat() if date_to else None,
            branch_id=branch_id,
            total_sales=row.total_sales or 0,
            completed_sales=completed,
            cancelled_sales=row.cancelled_sales or 0,
            refunded_sales=row.refunded_sales or 0,
            total_revenue=total_revenue,
            total_discount=Decimal(str(row.total_discount or "0.00")),
            total_tax=Decimal(str(row.total_tax or "0.00")),
            avg_order_value=avg,
            refund_total=refunds.refund_total,
            cancellation_total=refunds.cancellation_total,
        )

    # ──────────────────────────────────────────────────────────────
    # 2. Daily breakdown
    # ──────────────────────────────────────────────────────────────

    async def get_daily(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        branch_id: UUID | None,
        allowed_branch_ids: set[UUID] | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> list[DailySalesPoint]:
        filters = self._base_filters(tenant_id, date_from, date_to, branch_id, allowed_branch_ids, user_id, session_id)

        day_col = func.date(Sale.sold_at).label("sale_date")
        revenue_expr = self._revenue_expr()

        q = await self.db.execute(
            select(
                day_col,
                func.count(Sale.id).label("sales_count"),
                func.count(
                    case((Sale.status == _COMPLETED, Sale.id))
                ).label("completed_count"),
                func.coalesce(
                    func.sum(revenue_expr),
                    Decimal("0.00"),
                ).label("revenue"),
            )
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(*filters)
            .group_by(func.date(Sale.sold_at))
            .order_by(func.date(Sale.sold_at).asc())
        )

        return [
            DailySalesPoint(
                date=str(row.sale_date),
                sales_count=row.sales_count,
                completed_count=row.completed_count,
                revenue=Decimal(str(row.revenue or "0.00")),
            )
            for row in q.all()
        ]

    # ──────────────────────────────────────────────────────────────
    # 3. Top products
    # ──────────────────────────────────────────────────────────────

    async def get_top_products(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        branch_id: UUID | None,
        limit: int = 20,
        allowed_branch_ids: set[UUID] | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> list[TopProductItem]:
        # Base filters applied to Sale; COMPLETED only for revenue/quantity
        filters = self._base_filters(tenant_id, date_from, date_to, branch_id, allowed_branch_ids, user_id, session_id)
        filters.append(Sale.status == _COMPLETED)

        q = await self.db.execute(
            select(
                SaleItem.product_name,
                func.coalesce(func.sum(SaleItem.quantity), Decimal("0")).label("quantity_sold"),
                func.coalesce(func.sum(SaleItem.total), Decimal("0.00")).label("revenue"),
                func.count(Sale.id.distinct()).label("order_count"),
            )
            .join(Sale, SaleItem.sale_id == Sale.id)
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(*filters)
            .group_by(SaleItem.product_name)
            .order_by(func.sum(SaleItem.total).desc())
            .limit(limit)
        )

        return [
            TopProductItem(
                product_name=row.product_name,
                quantity_sold=Decimal(str(row.quantity_sold or "0")),
                revenue=Decimal(str(row.revenue or "0.00")),
                order_count=row.order_count,
            )
            for row in q.all()
        ]

    # ──────────────────────────────────────────────────────────────
    # 4. By cashier
    # ──────────────────────────────────────────────────────────────

    async def get_by_cashier(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        branch_id: UUID | None,
        allowed_branch_ids: set[UUID] | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> list[CashierSalesItem]:
        filters = self._base_filters(tenant_id, date_from, date_to, branch_id, allowed_branch_ids, user_id, session_id)
        revenue_expr = self._revenue_expr()

        q = await self.db.execute(
            select(
                Sale.user_id,
                User.full_name,
                User.username,
                func.count(Sale.id).label("sales_count"),
                func.count(
                    case((Sale.status == _COMPLETED, Sale.id))
                ).label("completed_count"),
                func.coalesce(
                    func.sum(revenue_expr),
                    Decimal("0.00"),
                ).label("revenue"),
            )
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .join(User, Sale.user_id == User.id)
            .where(*filters)
            .group_by(Sale.user_id, User.full_name, User.username)
            .order_by(func.sum(revenue_expr).desc())
        )

        return [
            CashierSalesItem(
                user_id=row.user_id,
                user_name=row.full_name or row.username,
                sales_count=row.sales_count,
                completed_count=row.completed_count,
                revenue=Decimal(str(row.revenue or "0.00")),
            )
            for row in q.all()
        ]

    # ──────────────────────────────────────────────────────────────
    # 5. By branch
    # ──────────────────────────────────────────────────────────────

    async def get_by_branch(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        branch_id: UUID | None = None,
        allowed_branch_ids: set[UUID] | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> list[BranchSalesItem]:
        filters = self._base_filters(
            tenant_id, date_from, date_to, branch_id, allowed_branch_ids, user_id, session_id,
        )
        revenue_expr = self._revenue_expr()

        q = await self.db.execute(
            select(
                Sale.branch_id,
                Branch.name.label("branch_name"),
                Branch.branch_code,
                func.count(Sale.id).label("sales_count"),
                func.count(
                    case((Sale.status == _COMPLETED, Sale.id))
                ).label("completed_count"),
                func.coalesce(
                    func.sum(revenue_expr),
                    Decimal("0.00"),
                ).label("revenue"),
            )
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(*filters)
            .group_by(Sale.branch_id, Branch.name, Branch.branch_code)
            .order_by(func.sum(revenue_expr).desc())
        )

        return [
            BranchSalesItem(
                branch_id=row.branch_id,
                branch_name=row.branch_name,
                branch_code=row.branch_code,
                sales_count=row.sales_count,
                completed_count=row.completed_count,
                revenue=Decimal(str(row.revenue or "0.00")),
            )
            for row in q.all()
        ]

    # ──────────────────────────────────────────────────────────────
    # 6. Monthly
    # ──────────────────────────────────────────────────────────────

    async def get_monthly(
        self,
        tenant_id: UUID,
        year: int | None,
        branch_id: UUID | None,
        allowed_branch_ids: set[UUID] | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> list[MonthlySalesPoint]:
        filters = [
            Business.tenant_id == tenant_id,
            Business.deleted_at.is_(None),
            Branch.deleted_at.is_(None),
            Sale.deleted_at.is_(None),
        ]

        if year is not None:
            filters.append(
                func.extract("year", Sale.sold_at) == year
            )
        else:
            # Default: last 24 months
            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=730)
            filters.append(Sale.sold_at >= cutoff)

        if branch_id is not None:
            filters.append(Sale.branch_id == branch_id)
        if allowed_branch_ids is not None:
            filters.append(Sale.branch_id.in_(allowed_branch_ids))
        if user_id is not None:
            filters.append(Sale.user_id == user_id)
        if session_id is not None:
            filters.append(Sale.session_id == session_id)

        month_col = func.to_char(Sale.sold_at, "YYYY-MM").label("month")
        revenue_expr = self._revenue_expr()

        q = await self.db.execute(
            select(
                month_col,
                func.count(Sale.id).label("sales_count"),
                func.coalesce(
                    func.sum(revenue_expr),
                    Decimal("0.00"),
                ).label("revenue"),
            )
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(*filters)
            # Reuse the exact expression object. PostgreSQL otherwise receives
            # three separately-bound format parameters and rejects the SELECT
            # expression as absent from GROUP BY.
            .group_by(month_col)
            .order_by(month_col.asc())
        )

        return [
            MonthlySalesPoint(
                month=row.month,
                sales_count=row.sales_count,
                revenue=Decimal(str(row.revenue or "0.00")),
            )
            for row in q.all()
        ]

    # ──────────────────────────────────────────────────────────────
    # 7. Yearly
    # ──────────────────────────────────────────────────────────────

    async def get_yearly(
        self,
        tenant_id: UUID,
        branch_id: UUID | None,
        allowed_branch_ids: set[UUID] | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> list[YearlySalesPoint]:
        filters = [
            Business.tenant_id == tenant_id,
            Business.deleted_at.is_(None),
            Branch.deleted_at.is_(None),
            Sale.deleted_at.is_(None),
        ]
        if branch_id is not None:
            filters.append(Sale.branch_id == branch_id)
        if allowed_branch_ids is not None:
            filters.append(Sale.branch_id.in_(allowed_branch_ids))
        if user_id is not None:
            filters.append(Sale.user_id == user_id)
        if session_id is not None:
            filters.append(Sale.session_id == session_id)

        year_col = func.extract("year", Sale.sold_at).cast(Integer).label("year")
        revenue_expr = self._revenue_expr()

        q = await self.db.execute(
            select(
                year_col,
                func.count(Sale.id).label("sales_count"),
                func.coalesce(
                    func.sum(revenue_expr),
                    Decimal("0.00"),
                ).label("revenue"),
            )
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(*filters)
            .group_by(func.extract("year", Sale.sold_at).cast(Integer))
            .order_by(func.extract("year", Sale.sold_at).cast(Integer).asc())
        )

        return [
            YearlySalesPoint(
                year=row.year,
                sales_count=row.sales_count,
                revenue=Decimal(str(row.revenue or "0.00")),
            )
            for row in q.all()
        ]

    # ──────────────────────────────────────────────────────────────
    # 8. By payment method (Cash / JazzCash / EasyPaisa / Online Transfer /
    #    Credit Card) — optionally bucketed by day/week/month/year, matching
    #    the same breakdown the POS shift-close screen shows per session.
    # ──────────────────────────────────────────────────────────────

    _PERIOD_COLS = {
        "day": lambda: func.to_char(Sale.sold_at, "YYYY-MM-DD"),
        "week": lambda: func.to_char(func.date_trunc("week", Sale.sold_at), "YYYY-MM-DD"),
        "month": lambda: func.to_char(Sale.sold_at, "YYYY-MM"),
        "year": lambda: func.to_char(Sale.sold_at, "YYYY"),
    }

    async def get_by_payment_method(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        branch_id: UUID | None,
        group_by: str | None = None,
        allowed_branch_ids: set[UUID] | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> list[PaymentMethodPoint]:
        """Revenue collected per payment method — COMPLETED sales only.

        group_by: None/"none" for one overall total, or "day"/"week"/"month"/"year"
        for one point per period (each carrying its own method breakdown).
        """
        filters = self._base_filters(tenant_id, date_from, date_to, branch_id, allowed_branch_ids, user_id, session_id)
        filters.append(Sale.status == _COMPLETED)
        filters.append(Payment.deleted_at.is_(None))

        period_fn = self._PERIOD_COLS.get((group_by or "none").lower())
        # Build the period expression exactly once and reuse the same object in
        # both SELECT and GROUP BY — two separately-constructed (but identical)
        # to_char(...) calls bind their literal args as distinct parameters,
        # which Postgres then refuses to recognise as the same GROUP BY term.
        period_expr = period_fn() if period_fn is not None else None
        cols = [
            Payment.payment_method,
            func.count(Payment.id).label("transactions"),
            func.coalesce(func.sum(Payment.amount), Decimal("0.00")).label("amount"),
        ]
        group_cols = [Payment.payment_method]
        if period_expr is not None:
            cols.insert(0, period_expr.label("period"))
            group_cols.insert(0, period_expr)

        q = await self.db.execute(
            select(*cols)
            .select_from(Payment)
            .join(Sale, Payment.sale_id == Sale.id)
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(*filters)
            .group_by(*group_cols)
        )
        rows = q.all()

        # Pivot flat (period, method, transactions, amount) rows into one
        # PaymentMethodPoint per period, folding legacy free-text method
        # strings onto their canonical label.
        points: dict[str | None, dict[str, tuple[int, Decimal]]] = {}
        for row in rows:
            period = row.period if period_expr is not None else None
            label = label_lenient(row.payment_method)
            bucket = points.setdefault(period, {})
            tx, amt = bucket.get(label, (0, Decimal("0.00")))
            bucket[label] = (tx + row.transactions, amt + Decimal(str(row.amount or "0.00")))

        result = [
            PaymentMethodPoint(
                period=period,
                total_amount=sum((amt for _tx, amt in methods.values()), Decimal("0.00")),
                breakdown=[
                    PaymentMethodBreakdownItem(payment_method=label, transactions=tx, amount=amt)
                    for label, (tx, amt) in sorted(methods.items())
                ],
            )
            for period, methods in points.items()
        ]
        result.sort(key=lambda p: (p.period is None, p.period or ""))
        return result

    # ──────────────────────────────────────────────────────────────
    # 9. Refunds & cancellations
    # ──────────────────────────────────────────────────────────────

    def _refund_filters(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        branch_id: UUID | None,
        refund_type: str,
        allowed_branch_ids: set[UUID] | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ):
        """WHERE clauses for a COMPLETED Refund/RefundItem query, scoped the
        same way _base_filters() scopes a Sale query. refunded_at (when the
        refund was actually processed on the POS device) is the date-range
        anchor here, not the original sale's sold_at — a return processed
        today against a sale from last week belongs to today's report."""
        filters = [
            Business.tenant_id == tenant_id,
            Business.deleted_at.is_(None),
            Branch.deleted_at.is_(None),
            Refund.deleted_at.is_(None),
            Refund.status == "COMPLETED",
            Refund.refund_type == refund_type,
        ]
        if date_from is not None:
            filters.append(Refund.refunded_at >= date_from)
        if date_to is not None:
            filters.append(Refund.refunded_at <= date_to)
        if branch_id is not None:
            filters.append(Refund.branch_id == branch_id)
        if allowed_branch_ids is not None:
            filters.append(Refund.branch_id.in_(allowed_branch_ids))
        if user_id is not None:
            filters.append(Refund.processed_by_user_id == user_id)
        if session_id is not None:
            filters.append(Refund.session_id == session_id)
        return filters

    async def _refund_totals(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        branch_id: UUID | None,
        refund_type: str,
        allowed_branch_ids: set[UUID] | None,
        user_id: UUID | None,
        session_id: UUID | None,
    ) -> tuple[int, Decimal, dict[str, Decimal]]:
        filters = self._refund_filters(
            tenant_id, date_from, date_to, branch_id, refund_type,
            allowed_branch_ids, user_id, session_id,
        )
        rows = (await self.db.scalars(
            select(Refund)
            .join(Branch, Refund.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(*filters)
        )).all()

        count = len(rows)
        total = sum((Decimal(str(r.amount)) for r in rows), Decimal("0.00"))
        by_method: dict[str, Decimal] = {m: Decimal("0.00") for m in PAYMENT_METHODS}
        for r in rows:
            breakdown = r.payment_breakdown or {r.refund_method: r.amount}
            for method, amount in breakdown.items():
                label = label_lenient(method)
                by_method[label] = by_method.get(label, Decimal("0.00")) + Decimal(str(amount))
        return count, total, by_method

    async def get_refunds_summary(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        branch_id: UUID | None,
        allowed_branch_ids: set[UUID] | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> RefundsSummary:
        refund_count, refund_total, refunds_by_method = await self._refund_totals(
            tenant_id, date_from, date_to, branch_id, "RETURN", allowed_branch_ids, user_id, session_id,
        )
        cancellation_count, cancellation_total, cancellations_by_method = await self._refund_totals(
            tenant_id, date_from, date_to, branch_id, "CANCEL", allowed_branch_ids, user_id, session_id,
        )
        return RefundsSummary(
            date_from=date_from.date().isoformat() if date_from else None,
            date_to=date_to.date().isoformat() if date_to else None,
            branch_id=branch_id,
            refund_count=refund_count,
            refund_total=refund_total,
            refunds_by_payment_method=refunds_by_method,
            cancellation_count=cancellation_count,
            cancellation_total=cancellation_total,
            cancellations_by_payment_method=cancellations_by_method,
        )

    # ──────────────────────────────────────────────────────────────
    # 10. Top returned / cancelled products
    # ──────────────────────────────────────────────────────────────

    async def get_returned_products(
        self,
        tenant_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        branch_id: UUID | None,
        limit: int = 20,
        allowed_branch_ids: set[UUID] | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> list[ReturnedProductItem]:
        """Ranks products by amount returned or cancelled — both RETURN and
        CANCEL refund types combined, since from a "what keeps coming back"
        standpoint a cancelled order's items are just as relevant as a
        returned one's."""
        base = [
            Business.tenant_id == tenant_id,
            Business.deleted_at.is_(None),
            Branch.deleted_at.is_(None),
            Refund.deleted_at.is_(None),
            Refund.status == "COMPLETED",
        ]
        if date_from is not None:
            base.append(Refund.refunded_at >= date_from)
        if date_to is not None:
            base.append(Refund.refunded_at <= date_to)
        if branch_id is not None:
            base.append(Refund.branch_id == branch_id)
        if allowed_branch_ids is not None:
            base.append(Refund.branch_id.in_(allowed_branch_ids))
        if user_id is not None:
            base.append(Refund.processed_by_user_id == user_id)
        if session_id is not None:
            base.append(Refund.session_id == session_id)

        q = await self.db.execute(
            select(
                RefundItem.product_name,
                func.count(RefundItem.id).label("times_returned"),
                func.coalesce(func.sum(RefundItem.quantity), Decimal("0")).label("quantity_returned"),
                func.coalesce(func.sum(RefundItem.amount), Decimal("0.00")).label("amount_returned"),
            )
            .select_from(RefundItem)
            .join(Refund, RefundItem.refund_id == Refund.id)
            .join(Branch, Refund.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(*base)
            .group_by(RefundItem.product_name)
            .order_by(func.sum(RefundItem.amount).desc())
            .limit(limit)
        )

        return [
            ReturnedProductItem(
                product_name=row.product_name,
                times_returned=row.times_returned,
                quantity_returned=Decimal(str(row.quantity_returned or "0")),
                amount_returned=Decimal(str(row.amount_returned or "0.00")),
            )
            for row in q.all()
        ]

    # ──────────────────────────────────────────────────────────────
    # 11. Year comparison — comprehensive multi-year KPI snapshot for the
    #     dedicated "Year Comparison" tab (manual year picks or "last 5
    #     years"), separate from the single-line get_yearly() trend above.
    # ──────────────────────────────────────────────────────────────

    async def get_year_comparison(
        self,
        tenant_id: UUID,
        years: list[int],
        branch_id: UUID | None,
        allowed_branch_ids: set[UUID] | None = None,
    ) -> list[YearComparisonPoint]:
        """One full KPI snapshot per requested year (see SalesSummary),
        each carrying its own Jan-Dec revenue curve and its growth vs. the
        prior calendar year. The prior year is always fetched too — even
        if not itself requested — so a gap comparison (e.g. 2023 vs. 2026
        only) still reports 2023's real growth off 2022, not a blank.
        """
        requested = sorted(set(years))
        years_needed = sorted(set(requested) | {y - 1 for y in requested})

        snapshots: dict[int, tuple[SalesSummary, list[MonthlySalesPoint]]] = {}
        for year in years_needed:
            date_from = datetime(year, 1, 1, tzinfo=timezone.utc)
            date_to = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
            summary = await self.get_summary(
                tenant_id, date_from, date_to, branch_id, allowed_branch_ids,
            )
            monthly = await self.get_monthly(tenant_id, year, branch_id, allowed_branch_ids)
            snapshots[year] = (summary, monthly)

        results = []
        for year in requested:
            summary, monthly = snapshots[year]
            revenue_by_month = {int(m.month.split("-")[1]): m for m in monthly}
            monthly_points = [
                YearComparisonMonthPoint(
                    month=m,
                    revenue=revenue_by_month[m].revenue if m in revenue_by_month else Decimal("0.00"),
                    sales_count=revenue_by_month[m].sales_count if m in revenue_by_month else 0,
                )
                for m in range(1, 13)
            ]

            growth: Decimal | None = None
            prior = snapshots.get(year - 1)
            if prior is not None and prior[0].total_revenue > 0:
                growth = (
                    (summary.total_revenue - prior[0].total_revenue) / prior[0].total_revenue * 100
                ).quantize(Decimal("0.01"))

            results.append(YearComparisonPoint(
                year=year,
                total_sales=summary.total_sales,
                completed_sales=summary.completed_sales,
                cancelled_sales=summary.cancelled_sales,
                refunded_sales=summary.refunded_sales,
                total_revenue=summary.total_revenue,
                total_discount=summary.total_discount,
                total_tax=summary.total_tax,
                avg_order_value=summary.avg_order_value,
                refund_total=summary.refund_total,
                cancellation_total=summary.cancellation_total,
                revenue_growth_pct=growth,
                monthly=monthly_points,
            ))
        return results
