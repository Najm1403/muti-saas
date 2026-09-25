# schemas/report.py

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from schemas.common import APIBaseSchema


# ═══════════════════════════════════════════════════════════════
# PLATFORM REPORTS  (used by api/platform/reports.py)
# ═══════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────

class PlatformSummary(APIBaseSchema):
    total_tenants: int
    active_tenants: int
    total_users: int
    total_branches: int
    total_devices: int
    estimated_mrr: Decimal


# ─────────────────────────────────────────────
# Tenant Report
# ─────────────────────────────────────────────

class TenantGrowthPoint(APIBaseSchema):
    label: str        # e.g. "2024-01"
    new_tenants: int
    cumulative: int


class TenantReport(APIBaseSchema):
    total: int
    new_this_period: int
    active: int           # is_active = True
    suspended: int        # is_active = False
    with_trial: int       # has TRIAL subscription
    with_active_sub: int  # has ACTIVE subscription
    cancelled: int        # has CANCELLED subscription
    growth: list[TenantGrowthPoint]


# ─────────────────────────────────────────────
# Subscription Report
# ─────────────────────────────────────────────

class PlanBreakdownItem(APIBaseSchema):
    plan_id: UUID
    plan_name: str
    tenant_count: int
    monthly_value: Decimal
    pct_of_active: float


class SubscriptionReport(APIBaseSchema):
    active: int
    trial: int
    expired: int
    suspended: int
    cancelled: int
    plan_breakdown: list[PlanBreakdownItem]
    estimated_mrr: Decimal
    estimated_arr: Decimal


# ─────────────────────────────────────────────
# Plan Performance
# ─────────────────────────────────────────────

class PlanPerformanceItem(APIBaseSchema):
    plan_id: UUID
    plan_name: str
    tenant_count: int
    pct_of_tenants: float
    mrr: Decimal


# ─────────────────────────────────────────────
# Branch Report
# ─────────────────────────────────────────────

class BranchTenantItem(APIBaseSchema):
    tenant_id: UUID
    tenant_name: str
    branch_count: int
    plan_limit: int   # max_branches from plan; -1 = unlimited


class BranchReport(APIBaseSchema):
    total_branches: int
    tenant_breakdown: list[BranchTenantItem]


# ─────────────────────────────────────────────
# Device Report
# ─────────────────────────────────────────────

class DeviceTenantItem(APIBaseSchema):
    tenant_id: UUID
    tenant_name: str
    total: int
    online: int    # is_activated AND last_sync_at within 2 h
    offline: int


class DeviceReport(APIBaseSchema):
    total: int
    activated: int
    never_activated: int
    online: int
    offline: int
    disabled: int
    tenant_breakdown: list[DeviceTenantItem]


# ─────────────────────────────────────────────
# User Report
# ─────────────────────────────────────────────

class UserTenantItem(APIBaseSchema):
    tenant_id: UUID
    tenant_name: str
    user_count: int


class UserReport(APIBaseSchema):
    total: int
    active: int
    disabled: int
    owners: int
    managers: int
    staff: int
    tenant_breakdown: list[UserTenantItem]


# ─────────────────────────────────────────────
# Activity Report
# ─────────────────────────────────────────────

class ActivitySummary(APIBaseSchema):
    tenant_creations: int
    device_registrations: int
    branch_creations: int
    user_creations: int
    logins: int
    failed_logins: int


# ─────────────────────────────────────────────
# Revenue Report
# ─────────────────────────────────────────────

class RevenueMonthItem(APIBaseSchema):
    month: str       # "YYYY-MM"
    amount: Decimal


class RevenuePlanItem(APIBaseSchema):
    plan_name: str
    amount: Decimal


class RevenueReport(APIBaseSchema):
    this_month: Decimal
    last_month: Decimal
    growth_pct: float | None
    by_plan: list[RevenuePlanItem]
    monthly_trend: list[RevenueMonthItem]   # last 6 months


class ReportRequest(APIBaseSchema):
    """
    Common date range filter for report endpoints.
    """

    branch_id: UUID
    date_from: date
    date_to: date


class SalesSummaryReport(APIBaseSchema):
    """
    Aggregated sales figures for a branch over a date range.
    """

    branch_id: UUID
    date_from: date
    date_to: date
    total_transactions: int
    total_revenue: Decimal
    total_discount: Decimal
    net_revenue: Decimal
    total_refunds: int
    total_refunded_amount: Decimal


class DailySalesRow(APIBaseSchema):
    """
    Sales totals for a single day.
    """

    date: date
    total_transactions: int
    total_revenue: Decimal
    total_discount: Decimal
    net_revenue: Decimal


class DailySalesReport(APIBaseSchema):
    """
    Day-by-day breakdown of sales for a branch.
    """

    branch_id: UUID
    date_from: date
    date_to: date
    rows: list[DailySalesRow] = Field(default_factory=list)


class TopProductRow(APIBaseSchema):
    """
    Sales performance of a single product.
    """

    product_id: UUID
    product_name: str
    quantity_sold: Decimal
    total_revenue: Decimal


class TopProductsReport(APIBaseSchema):
    """
    Best-selling products for a branch over a date range.
    """

    branch_id: UUID
    date_from: date
    date_to: date
    rows: list[TopProductRow] = Field(default_factory=list)


class CashierSalesRow(APIBaseSchema):
    """
    Sales totals for a single cashier (user).
    """

    user_id: UUID
    full_name: str
    total_transactions: int
    total_revenue: Decimal


class CashierSalesReport(APIBaseSchema):
    """
    Sales broken down by cashier for a branch.
    """

    branch_id: UUID
    date_from: date
    date_to: date
    rows: list[CashierSalesRow] = Field(default_factory=list)


class PaymentMethodRow(APIBaseSchema):
    """
    Total amount collected per payment method.
    """

    payment_method: str
    total_transactions: int
    total_amount: Decimal


class PaymentMethodReport(APIBaseSchema):
    """
    Revenue split by payment method for a branch.
    """

    branch_id: UUID
    date_from: date
    date_to: date
    rows: list[PaymentMethodRow] = Field(default_factory=list)
