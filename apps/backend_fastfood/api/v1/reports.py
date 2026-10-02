# api/v1/reports.py
#
# Tenant-level sales analytics endpoints.
# All routes are scoped to the authenticated user's tenant.
# No business logic here — delegates entirely to TenantReportService.
# Prefix: /api/v1/reports

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from reportlab.platypus import Spacer
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from api.branch_access import visible_branches
from core.exceptions import ForbiddenError, ValidationError
from db.session import get_db
from schemas.pos_session import SessionVarianceItem
from schemas.tenant_report import (
    BranchSalesItem,
    CashierSalesItem,
    DailySalesPoint,
    MonthlySalesPoint,
    PaymentMethodPoint,
    RefundsSummary,
    ReturnedProductItem,
    SalesSummary,
    TopProductItem,
    YearComparisonPoint,
    YearlySalesPoint,
)
from services.cashier_session_service import CashierSessionService
from services.pdf_report_service import build_pdf, data_table, get_branding, kpi_row, section_title
from services.tenant_report_service import TenantReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


def _svc(db: AsyncSession = Depends(get_db)) -> TenantReportService:
    return TenantReportService(db)


def _session_svc(db: AsyncSession = Depends(get_db)) -> CashierSessionService:
    return CashierSessionService(db)


async def _report_branch_scope(
    current_user: CurrentUser,
    svc: TenantReportService,
    branch_id: UUID | None,
) -> set[UUID] | None:
    """Return the caller's complete branch scope and validate an explicit filter."""
    allowed = await visible_branches(svc.db, current_user)
    if allowed is not None and branch_id is not None and branch_id not in allowed:
        raise ForbiddenError("No access to the selected branch.")
    return allowed


# ──────────────────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/summary",
    response_model=SalesSummary,
    status_code=status.HTTP_200_OK,
    summary="Sales summary",
    description=(
        "Returns aggregate totals (count, revenue, discount, tax, average order value) "
        "for the tenant, optionally filtered by date range and/or branch."
    ),
)
async def get_summary(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    branch_id: UUID | None = None,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantReportService = Depends(_svc),
) -> SalesSummary:
    allowed = await _report_branch_scope(current_user, svc, branch_id)
    return await svc.get_summary(
        tenant_id=current_user.tenant_id,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
        allowed_branch_ids=allowed,
        user_id=user_id,
        session_id=session_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Daily breakdown
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/daily",
    response_model=list[DailySalesPoint],
    status_code=status.HTTP_200_OK,
    summary="Daily sales breakdown",
    description=(
        "Returns one data point per calendar day that had at least one sale. "
        "Only days with records are returned — zero-sale days are omitted."
    ),
)
async def get_daily(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    branch_id: UUID | None = None,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantReportService = Depends(_svc),
) -> list[DailySalesPoint]:
    allowed = await _report_branch_scope(current_user, svc, branch_id)
    return await svc.get_daily(
        tenant_id=current_user.tenant_id,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
        allowed_branch_ids=allowed,
        user_id=user_id,
        session_id=session_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Top products
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/products",
    response_model=list[TopProductItem],
    status_code=status.HTTP_200_OK,
    summary="Top products by revenue",
    description=(
        "Returns the top-selling products (COMPLETED sales only) ranked by revenue. "
        "Groups by product_name snapshot. Defaults to top 20."
    ),
)
async def get_top_products(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    branch_id: UUID | None = None,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    limit: int = 20,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantReportService = Depends(_svc),
) -> list[TopProductItem]:
    allowed = await _report_branch_scope(current_user, svc, branch_id)
    return await svc.get_top_products(
        tenant_id=current_user.tenant_id,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
        limit=limit,
        allowed_branch_ids=allowed,
        user_id=user_id,
        session_id=session_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# By cashier
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/cashiers",
    response_model=list[CashierSalesItem],
    status_code=status.HTTP_200_OK,
    summary="Sales by cashier",
    description=(
        "Returns sales performance broken down per cashier. "
        "sales_count includes all statuses; completed_count and revenue are COMPLETED only."
    ),
)
async def get_by_cashier(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    branch_id: UUID | None = None,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantReportService = Depends(_svc),
) -> list[CashierSalesItem]:
    allowed = await _report_branch_scope(current_user, svc, branch_id)
    return await svc.get_by_cashier(
        tenant_id=current_user.tenant_id,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
        allowed_branch_ids=allowed,
        user_id=user_id,
        session_id=session_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# By branch
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/branches",
    response_model=list[BranchSalesItem],
    status_code=status.HTTP_200_OK,
    summary="Sales by branch",
    description=(
        "Returns sales performance broken down per branch within the caller's branch scope. "
        "sales_count includes all statuses; completed_count and revenue are COMPLETED only."
    ),
)
async def get_by_branch(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    branch_id: UUID | None = None,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantReportService = Depends(_svc),
) -> list[BranchSalesItem]:
    allowed = await _report_branch_scope(current_user, svc, branch_id)
    return await svc.get_by_branch(
        tenant_id=current_user.tenant_id,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
        allowed_branch_ids=allowed,
        user_id=user_id,
        session_id=session_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Monthly
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/monthly",
    response_model=list[MonthlySalesPoint],
    status_code=status.HTTP_200_OK,
    summary="Monthly sales trend",
    description=(
        "Returns one data point per month. When year is provided, only that year is returned. "
        "Otherwise returns the last 24 months. Revenue is COMPLETED sales only."
    ),
)
async def get_monthly(
    year: int | None = None,
    branch_id: UUID | None = None,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantReportService = Depends(_svc),
) -> list[MonthlySalesPoint]:
    allowed = await _report_branch_scope(current_user, svc, branch_id)
    return await svc.get_monthly(
        tenant_id=current_user.tenant_id,
        year=year,
        branch_id=branch_id,
        allowed_branch_ids=allowed,
        user_id=user_id,
        session_id=session_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Yearly
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/yearly",
    response_model=list[YearlySalesPoint],
    status_code=status.HTTP_200_OK,
    summary="Yearly sales trend",
    description=(
        "Returns one data point per year across all historical data. "
        "Revenue is COMPLETED sales only. Ordered by year ascending."
    ),
)
async def get_yearly(
    branch_id: UUID | None = None,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantReportService = Depends(_svc),
) -> list[YearlySalesPoint]:
    allowed = await _report_branch_scope(current_user, svc, branch_id)
    return await svc.get_yearly(
        tenant_id=current_user.tenant_id,
        branch_id=branch_id,
        allowed_branch_ids=allowed,
        user_id=user_id,
        session_id=session_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Year comparison — dedicated multi-year KPI comparison (manual years or
# "last 5 years"), separate from the single-line /yearly trend above.
# ──────────────────────────────────────────────────────────────────────────────

def _validate_comparison_years(years: list[int]) -> None:
    if not years:
        raise ValidationError("Select at least one year to compare.")
    if len(years) > 10:
        raise ValidationError("Select at most 10 years to compare.")


@router.get(
    "/year-comparison",
    response_model=list[YearComparisonPoint],
    status_code=status.HTTP_200_OK,
    summary="Year-over-year comparison",
    description=(
        "A full KPI snapshot (sales, revenue, refunds/cancellations, average "
        "order value, month-by-month revenue curve, growth vs. the prior "
        "calendar year) for each requested year. Pass 1-10 years as repeated "
        "?years=2025&years=2026 query params."
    ),
)
async def get_year_comparison(
    years: list[int] = Query(...),
    branch_id: UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantReportService = Depends(_svc),
) -> list[YearComparisonPoint]:
    _validate_comparison_years(years)
    allowed = await _report_branch_scope(current_user, svc, branch_id)
    return await svc.get_year_comparison(
        tenant_id=current_user.tenant_id,
        years=years,
        branch_id=branch_id,
        allowed_branch_ids=allowed,
    )


@router.get(
    "/year-comparison/pdf",
    summary="Year-over-year comparison — PDF",
    description=(
        "The same data as /year-comparison, bundled into one printable A4 "
        "document: a year-by-year KPI table (with growth %) and a "
        "month-by-year revenue matrix."
    ),
)
async def get_year_comparison_pdf(
    years: list[int] = Query(...),
    branch_id: UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantReportService = Depends(_svc),
) -> Response:
    _validate_comparison_years(years)
    allowed = await _report_branch_scope(current_user, svc, branch_id)
    points = await svc.get_year_comparison(
        tenant_id=current_user.tenant_id, years=years, branch_id=branch_id, allowed_branch_ids=allowed,
    )
    business_name, logo_bytes, branch_line, currency = await get_branding(
        svc.db, current_user.tenant_id, branch_id,
    )

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    flowables: list = [
        section_title("Year-by-Year Summary"),
        data_table(
            ["Year", "Total Sales", "Completed", "Revenue", "Avg Order", "Refunds", "Cancellations", "YoY Growth"],
            [
                [
                    p.year, p.total_sales, p.completed_sales, f"{currency} {p.total_revenue:.2f}",
                    f"{currency} {p.avg_order_value:.2f}", f"{currency} {p.refund_total:.2f}",
                    f"{currency} {p.cancellation_total:.2f}",
                    f"{p.revenue_growth_pct:+.1f}%" if p.revenue_growth_pct is not None else "—",
                ]
                for p in points
            ],
            numeric_cols={1, 2, 3, 4, 5, 6, 7},
            col_fractions=[0.08, 0.11, 0.11, 0.15, 0.13, 0.13, 0.14, 0.15],
        ),
    ]

    if points:
        year_col_fraction = 0.78 / len(points)
        flowables += [
            section_title("Monthly Revenue Comparison"),
            data_table(
                ["Month"] + [str(p.year) for p in points],
                [
                    [month_names[m - 1]] + [f"{currency} {p.monthly[m - 1].revenue:.2f}" for p in points]
                    for m in range(1, 13)
                ],
                numeric_cols=set(range(1, len(points) + 1)),
                col_fractions=[0.22] + [year_col_fraction] * len(points),
                totals=["Total"] + [f"{currency} {p.total_revenue:.2f}" for p in points],
            ),
        ]

    period = ", ".join(str(p.year) for p in points)
    pdf_bytes = await build_pdf(
        business_name=business_name, logo_bytes=logo_bytes, branch_line=branch_line,
        report_title="Year Comparison Report", subtitle=period, flowables=flowables,
    )
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="year-comparison-report.pdf"'},
    )


# ──────────────────────────────────────────────────────────────────────────────
# By payment method
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/payment-methods",
    response_model=list[PaymentMethodPoint],
    status_code=status.HTTP_200_OK,
    summary="Sales by payment method",
    description=(
        "Revenue collected per payment method (Cash / JazzCash / EasyPaisa / "
        "Online Transfer / Credit Card) — the same breakdown the POS shift-close "
        "screen shows per session, rolled up across the tenant. COMPLETED sales only. "
        "group_by=day|week|month|year returns one point per period; omit it (or "
        "'none') for a single overall total across date_from..date_to."
    ),
)
async def get_by_payment_method(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    branch_id: UUID | None = None,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    group_by: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantReportService = Depends(_svc),
) -> list[PaymentMethodPoint]:
    allowed = await _report_branch_scope(current_user, svc, branch_id)
    return await svc.get_by_payment_method(
        tenant_id=current_user.tenant_id,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
        group_by=group_by,
        allowed_branch_ids=allowed,
        user_id=user_id,
        session_id=session_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Refunds & cancellations
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/refunds",
    response_model=RefundsSummary,
    status_code=status.HTTP_200_OK,
    summary="Refunds & cancellations summary",
    description=(
        "Aggregate totals for returns (RETURN) and same-shift cancellations "
        "(CANCEL) — COMPLETED refunds only, each with its own payment-method "
        "breakdown. The business-wide analogue of the POS shift-close "
        "screen's per-shift refund/cancellation section."
    ),
)
async def get_refunds_summary(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    branch_id: UUID | None = None,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantReportService = Depends(_svc),
) -> RefundsSummary:
    allowed = await _report_branch_scope(current_user, svc, branch_id)
    return await svc.get_refunds_summary(
        tenant_id=current_user.tenant_id,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
        allowed_branch_ids=allowed,
        user_id=user_id,
        session_id=session_id,
    )


@router.get(
    "/returned-products",
    response_model=list[ReturnedProductItem],
    status_code=status.HTTP_200_OK,
    summary="Top returned / cancelled products",
    description=(
        "Products ranked by amount returned or cancelled (RETURN and CANCEL "
        "refund types combined). Defaults to top 20."
    ),
)
async def get_returned_products(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    branch_id: UUID | None = None,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    limit: int = 20,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantReportService = Depends(_svc),
) -> list[ReturnedProductItem]:
    allowed = await _report_branch_scope(current_user, svc, branch_id)
    return await svc.get_returned_products(
        tenant_id=current_user.tenant_id,
        date_from=date_from,
        date_to=date_to,
        branch_id=branch_id,
        limit=limit,
        allowed_branch_ids=allowed,
        user_id=user_id,
        session_id=session_id,
    )


# ──────────────────────────────────────────────────────────────────────────────
# PDF export — real A4 document (reportlab), not a browser print
# ──────────────────────────────────────────────────────────────────────────────

def _report_granularity(date_from: datetime | None, date_to: datetime | None) -> dict:
    """Mirrors the tenant dashboard's own granularity rule (reports.html
    computeGranularity()) so this export never mixes a short selected period
    with an unrelated full-year monthly table, or vice versa: a 31-day-or-
    shorter range gets the daily chart's data, a longer one gets the monthly
    table scoped to that range's year (and month span, when it stays inside
    one calendar year). Year-over-year comparison lives in its own
    /year-comparison/pdf export, not here.
    """
    if date_from is None and date_to is None:
        return {"show_daily": False, "show_monthly": True, "year": None, "month_range": None}
    if date_from is None or date_to is None:
        return {"show_daily": True, "show_monthly": False, "year": None, "month_range": None}
    span_days = (date_to.date() - date_from.date()).days + 1
    if span_days <= 31:
        return {"show_daily": True, "show_monthly": False, "year": None, "month_range": None}
    same_year = date_from.year == date_to.year
    return {
        "show_daily": False, "show_monthly": True, "year": date_from.year,
        "month_range": (date_from.month, date_to.month) if same_year else None,
    }


@router.get(
    "/pdf",
    summary="Sales report — PDF",
    description=(
        "The same data as summary/daily-or-monthly/branches/cashiers/products/"
        "payment-methods/refunds, bundled into one printable A4 document, "
        "scoped to the same granularity the dashboard shows on screen for the "
        "given date range. Charts are screen-only — this covers every tabular "
        "section."
    ),
)
async def get_report_pdf(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    branch_id: UUID | None = None,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantReportService = Depends(_svc),
) -> Response:
    allowed = await _report_branch_scope(current_user, svc, branch_id)
    kwargs = dict(
        tenant_id=current_user.tenant_id, branch_id=branch_id,
        allowed_branch_ids=allowed, user_id=user_id, session_id=session_id,
    )
    gran = _report_granularity(date_from, date_to)
    summary = await svc.get_summary(date_from=date_from, date_to=date_to, **kwargs)
    daily = await svc.get_daily(date_from=date_from, date_to=date_to, **kwargs) if gran["show_daily"] else []
    monthly = await svc.get_monthly(year=gran["year"], **kwargs) if gran["show_monthly"] else []
    if gran["month_range"] is not None:
        lo, hi = gran["month_range"]
        monthly = [m for m in monthly if lo <= int(m.month.split("-")[1]) <= hi]
    by_branch = await svc.get_by_branch(date_from=date_from, date_to=date_to, **kwargs)
    by_cashier = await svc.get_by_cashier(date_from=date_from, date_to=date_to, **kwargs)
    top_products = await svc.get_top_products(date_from=date_from, date_to=date_to, **kwargs)
    payment_methods = await svc.get_by_payment_method(date_from=date_from, date_to=date_to, **kwargs)
    refunds = await svc.get_refunds_summary(date_from=date_from, date_to=date_to, **kwargs)
    returned_products = await svc.get_returned_products(date_from=date_from, date_to=date_to, **kwargs)

    business_name, logo_bytes, branch_line, currency = await get_branding(
        svc.db, current_user.tenant_id, branch_id,
    )

    period = " · ".join(filter(None, [
        f"From {summary.date_from}" if summary.date_from else None,
        f"To {summary.date_to}" if summary.date_to else None,
    ])) or "All time"

    flowables: list = [
        kpi_row([
            ("GROSS SALES", f"{currency} {summary.gross_sales:.2f}"),
            ("TOTAL SALES", str(summary.total_sales)),
            ("REVENUE", f"{currency} {summary.total_revenue:.2f}"),
            ("AVG ORDER VALUE", f"{currency} {summary.avg_order_value:.2f}"),
            ("TAX COLLECTED", f"{currency} {summary.total_tax:.2f}"),
        ]),
        Spacer(1, 4),
        kpi_row([
            ("RETURNS", f"{refunds.refund_count} · {currency} {refunds.refund_total:.2f}"),
            ("CANCELLATIONS", f"{refunds.cancellation_count} · {currency} {refunds.cancellation_total:.2f}"),
            ("REFUNDED SALES", str(summary.refunded_sales)),
            ("CANCELLED SALES", str(summary.cancelled_sales)),
        ]),
        Spacer(1, 4),
    ]

    refund_rows = [[label, f"{currency} {amt:.2f}"]
                   for label, amt in refunds.refunds_by_payment_method.items() if amt]
    cancellation_rows = [[label, f"{currency} {amt:.2f}"]
                         for label, amt in refunds.cancellations_by_payment_method.items() if amt]
    if refund_rows or cancellation_rows:
        flowables.append(section_title("Refunds & Cancellations"))
        if refund_rows:
            flowables.append(data_table(
                ["Returns — Method", "Amount"], refund_rows,
                numeric_cols={1}, col_fractions=[0.6, 0.4],
                totals=["Total returns", f"{currency} {refunds.refund_total:.2f}"],
            ))
        if cancellation_rows:
            flowables.append(Spacer(1, 6))
            flowables.append(data_table(
                ["Cancellations — Method", "Amount"], cancellation_rows,
                numeric_cols={1}, col_fractions=[0.6, 0.4],
                totals=["Total cancellations", f"{currency} {refunds.cancellation_total:.2f}"],
            ))

    if returned_products:
        flowables += [
            section_title("Top Returned / Cancelled Products"),
            data_table(
                ["Product", "Times", "Qty Returned", "Amount Returned"],
                [[p.product_name, p.times_returned, str(p.quantity_returned), f"{currency} {p.amount_returned:.2f}"]
                 for p in returned_products],
                numeric_cols={1, 2, 3}, col_fractions=[0.4, 0.18, 0.2, 0.22],
            ),
        ]

    if payment_methods and payment_methods[0].breakdown:
        flowables += [
            section_title("Revenue by Payment Method"),
            data_table(
                ["Method", "Transactions", "Amount"],
                [[b.payment_method, b.transactions, f"{currency} {b.amount:.2f}"]
                 for b in payment_methods[0].breakdown],
                numeric_cols={1, 2}, col_fractions=[0.5, 0.25, 0.25],
            ),
        ]

    if daily:
        flowables += [
            section_title("Daily Sales"),
            data_table(
                ["Date", "Sales", "Completed", "Revenue"],
                [[d.date, d.sales_count, d.completed_count, f"{currency} {d.revenue:.2f}"] for d in daily],
                numeric_cols={1, 2, 3}, col_fractions=[0.3, 0.2, 0.2, 0.3],
            ),
        ]

    if monthly:
        flowables += [
            section_title("Monthly Revenue"),
            data_table(
                ["Month", "Sales", "Revenue"],
                [[m.month, m.sales_count, f"{currency} {m.revenue:.2f}"] for m in monthly],
                numeric_cols={1, 2}, col_fractions=[0.4, 0.3, 0.3],
            ),
        ]

    if by_branch:
        flowables += [
            section_title("Revenue by Branch"),
            data_table(
                ["Branch", "Code", "Total Sales", "Completed", "Revenue"],
                [[b.branch_name, b.branch_code, b.sales_count, b.completed_count, f"{currency} {b.revenue:.2f}"]
                 for b in by_branch],
                numeric_cols={2, 3, 4}, col_fractions=[0.3, 0.15, 0.18, 0.15, 0.22],
            ),
        ]

    if by_cashier:
        flowables += [
            section_title("Sales by Cashier"),
            data_table(
                ["Cashier", "Total Sales", "Completed", "Revenue"],
                [[c.user_name, c.sales_count, c.completed_count, f"{currency} {c.revenue:.2f}"] for c in by_cashier],
                numeric_cols={1, 2, 3}, col_fractions=[0.4, 0.2, 0.18, 0.22],
            ),
        ]

    if top_products:
        flowables += [
            section_title("Top Products"),
            data_table(
                ["Product", "Orders", "Qty Sold", "Revenue"],
                [[p.product_name, p.order_count, str(p.quantity_sold), f"{currency} {p.revenue:.2f}"]
                 for p in top_products],
                numeric_cols={1, 2, 3}, col_fractions=[0.4, 0.2, 0.18, 0.22],
            ),
        ]

    pdf_bytes = await build_pdf(
        business_name=business_name, logo_bytes=logo_bytes, branch_line=branch_line,
        report_title="Sales Report", subtitle=period, flowables=flowables,
    )
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="sales-report.pdf"'},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Cash reconciliation by shift — the tenant-admin view of the per-shift
# variance a cashier already sees on their own device at close time (see
# CashierSessionService.close/_summary), never previously visible to anyone
# else. Deliberately a thin pass-through to CashierSessionService rather
# than TenantReportService — it reads CashierSession, not Sale, aggregates.
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/shifts",
    response_model=list[SessionVarianceItem],
    status_code=status.HTTP_200_OK,
    summary="Cash reconciliation by shift",
    description=(
        "Closed shifts with their cash variance (closing cash vs. expected "
        "cash = opening cash + cash sales - cash refunds). Pass "
        "shortages_only=true to see only shifts where the drawer came up "
        "short."
    ),
)
async def list_shift_variance(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    branch_id: UUID | None = None,
    shortages_only: bool = False,
    limit: int = Query(default=100, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    svc: CashierSessionService = Depends(_session_svc),
) -> list[SessionVarianceItem]:
    allowed = await visible_branches(svc.db, current_user)
    if allowed is not None and branch_id is not None and branch_id not in allowed:
        raise ForbiddenError("No access to the selected branch.")
    return await svc.list_variance(
        tenant_id=current_user.tenant_id,
        branch_id=branch_id,
        date_from=date_from,
        date_to=date_to,
        allowed_branch_ids=allowed,
        shortages_only=shortages_only,
        limit=limit,
    )
