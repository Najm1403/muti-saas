# schemas/dashboard.py

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from schemas.common import APIBaseSchema


class TenantDashboardStats(APIBaseSchema):
    # Tenant context
    tenant_id: UUID
    tenant_name: str
    tenant_code: str
    tenant_is_active: bool

    # Counts
    branch_count: int
    active_branch_count: int
    device_count: int
    active_device_count: int
    user_count: int
    low_stock_count: int = 0
    low_stock_threshold: int = 5

    # Sales (today + this month, using local timezone if possible)
    today_sales_count: int
    today_revenue: Decimal
    month_sales_count: int
    month_revenue: Decimal

    # Subscription summary
    subscription_status: str | None = None
    subscription_plan: str | None = None
    subscription_expires_at: datetime | None = None
    trial_ends_at: datetime | None = None
    max_branches: int | None = None
    max_devices: int | None = None
    max_users: int | None = None
