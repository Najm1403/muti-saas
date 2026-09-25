# schemas/branch.py

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
)


class BranchCreate(APIBaseSchema):
    """
    Data required to create a branch under a business.

    branch_code must be unique within the business.
    """

    branch_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=150)
    address: str | None = Field(None, max_length=500)
    phone: str | None = Field(None, max_length=30)


class BranchUpdate(APIBaseSchema):
    """
    Fields that may be updated on an existing branch.
    """

    name: str | None = Field(None, min_length=1, max_length=150)
    address: str | None = Field(None, max_length=500)
    phone: str | None = Field(None, max_length=30)
    is_active: bool | None = None


class BranchResponse(UUIDResponseSchema, TimestampResponseSchema):
    """
    Branch record returned by the API.
    """

    business_id: UUID
    branch_code: str
    name: str
    address: str | None
    phone: str | None
    is_active: bool


class BranchStatsResponse(APIBaseSchema):
    """Branch row enriched with device + sales aggregate data."""
    id: UUID
    business_id: UUID
    name: str
    branch_code: str
    address: str | None = None
    phone: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    device_count: int = 0
    active_device_count: int = 0
    activated_device_count: int = 0
    last_sync_at: datetime | None = None

    today_sales_count: int = 0
    today_revenue: Decimal = Decimal("0.00")
    month_sales_count: int = 0
    month_revenue: Decimal = Decimal("0.00")
