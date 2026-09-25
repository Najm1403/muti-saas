# schemas/tenant_report.py
#
# Pydantic output schemas for tenant-level sales analytics endpoints.
# These are pure output shapes — no ORM mapping needed.

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from schemas.common import APIBaseSchema


class SalesSummary(APIBaseSchema):
    """Aggregate sales summary for a tenant over a date range."""

    date_from: str | None
    date_to: str | None
    branch_id: UUID | None
    total_sales: int
    completed_sales: int
    cancelled_sales: int
    refunded_sales: int
    total_revenue: Decimal
    total_discount: Decimal
    total_tax: Decimal
    avg_order_value: Decimal
    # Money actually handed back to customers — RETURN refunds (a later,
    # partial or full item return) and CANCEL refunds (a same-shift full
    # reversal of the whole bill) counted separately, since a cancellation
    # is closer to "this sale never really happened" while a return is a
    # genuine after-the-fact reversal. total_revenue above already excludes
    # both (see TenantReportService._revenue_expr) — these two fields exist
    # so that exclusion is visible instead of silently invisible.
    refund_total: Decimal
    cancellation_total: Decimal


class DailySalesPoint(APIBaseSchema):
    """One data point per calendar day."""

    date: str               # "2026-01-15"
    sales_count: int
    completed_count: int
    revenue: Decimal


class TopProductItem(APIBaseSchema):
    """Aggregate sales stats for a single product (by name snapshot)."""

    product_name: str
    quantity_sold: Decimal
    revenue: Decimal
    order_count: int


class CashierSalesItem(APIBaseSchema):
    """Sales performance broken down per cashier."""

    user_id: UUID
    user_name: str          # full_name preferred, username as fallback
    sales_count: int
    completed_count: int
    revenue: Decimal


class BranchSalesItem(APIBaseSchema):
    """Sales performance broken down per branch."""

    branch_id: UUID
    branch_name: str
    branch_code: str
    sales_count: int
    completed_count: int
    revenue: Decimal


class MonthlySalesPoint(APIBaseSchema):
    """One data point per calendar month."""

    month: str              # "2026-01"
    sales_count: int
    revenue: Decimal


class YearlySalesPoint(APIBaseSchema):
    """One data point per calendar year."""

    year: int
    sales_count: int
    revenue: Decimal


class PaymentMethodBreakdownItem(APIBaseSchema):
    """Total collected through a single payment method within a period."""

    payment_method: str      # canonical label — see core.payment_methods.PAYMENT_METHODS
    transactions: int
    amount: Decimal


class PaymentMethodPoint(APIBaseSchema):
    """One period's payment-method breakdown.

    `period` is None for the overall (ungrouped) totals, otherwise a bucket
    label matching `group_by`: "2026-01-15" (day), the Monday of the ISO week
    (week), "2026-01" (month), or "2026" (year).
    """

    period: str | None
    total_amount: Decimal
    breakdown: list[PaymentMethodBreakdownItem] = Field(default_factory=list)


class RefundsSummary(APIBaseSchema):
    """Aggregate refund/return and cancellation totals for a tenant over a
    date range — the business-wide analogue of the POS shift-close screen's
    per-shift refund/cancellation breakdown (see
    services/cashier_session_service.py::_summary). Only COMPLETED Refund
    rows are counted, split by refund_type: RETURN (a later, possibly
    partial item return) vs CANCEL (a same-shift full reversal)."""

    date_from: str | None
    date_to: str | None
    branch_id: UUID | None
    refund_count: int
    refund_total: Decimal
    refunds_by_payment_method: dict[str, Decimal]
    cancellation_count: int
    cancellation_total: Decimal
    cancellations_by_payment_method: dict[str, Decimal]


class ReturnedProductItem(APIBaseSchema):
    """A product's return/cancellation footprint, ranked by amount returned
    — which items customers bring back most, or which orders get cancelled
    most. Grouped by RefundItem.product_name (a snapshot, same convention
    as TopProductItem.product_name)."""

    product_name: str
    times_returned: int
    quantity_returned: Decimal
    amount_returned: Decimal


class YearComparisonMonthPoint(APIBaseSchema):
    """One calendar month's revenue within a YearComparisonPoint — always
    12 entries (Jan..Dec), zero-filled for months with no sales, so the
    frontend can chart/tabulate multiple years side by side without gaps."""

    month: int  # 1-12
    revenue: Decimal
    sales_count: int


class YearComparisonPoint(APIBaseSchema):
    """One requested year's full KPI snapshot for the tenant dashboard's
    Year Comparison tab — the same aggregate shape as SalesSummary, plus a
    12-point monthly revenue curve for charting and this year's revenue
    growth against the immediately preceding calendar year (fetched even
    when that prior year wasn't itself requested, so comparing e.g. only
    2023 and 2026 still shows 2023's real growth vs. 2022)."""

    year: int
    total_sales: int
    completed_sales: int
    cancelled_sales: int
    refunded_sales: int
    total_revenue: Decimal
    total_discount: Decimal
    total_tax: Decimal
    avg_order_value: Decimal
    refund_total: Decimal
    cancellation_total: Decimal
    revenue_growth_pct: Decimal | None
    monthly: list[YearComparisonMonthPoint]
