# schemas/sale.py

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from schemas.units import Units
from pydantic import AliasPath, Field

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
    SyncResponseSchema,
)
from schemas.payment import PaymentResponse


# ─────────────────────────────────────────────
# SaleItemOption
# ─────────────────────────────────────────────

class SaleItemOptionCreate(APIBaseSchema):
    """
    Variant Option selected by the customer for one sale item — display/audit
    snapshot only, no price (the price effect is already baked into
    SaleItem.unit_price, which snapshots the Variant's sale_price).
    """

    id: UUID | None = Field(
        None,
        description="Client-generated UUID for offline sync.",
    )
    variant_option_id: UUID
    option_name: str = Field(..., max_length=100)


class SaleItemOptionResponse(UUIDResponseSchema, SyncResponseSchema):
    """
    Selected Variant Option returned as part of a SaleItem response.
    """

    sale_item_id: UUID
    variant_option_id: UUID
    option_name: str


# ─────────────────────────────────────────────
# SaleItem
# ─────────────────────────────────────────────

class SaleItemCreate(APIBaseSchema):
    """
    One product line inside a sale.

    product_name and unit_price are stored as snapshots so that
    historical totals remain correct if the product price changes.
    """

    id: UUID | None = Field(
        None,
        description="Client-generated UUID for offline sync.",
    )
    variant_id: UUID
    product_id: UUID
    product_name: str = Field(..., max_length=150)
    quantity: Units = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=Decimal("0"))
    discount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    total: Decimal = Field(..., ge=Decimal("0"))
    options: list[SaleItemOptionCreate] = Field(default_factory=list)


class SaleItemResponse(UUIDResponseSchema, TimestampResponseSchema, SyncResponseSchema):
    """
    Sale item returned as part of a Sale response.
    """

    sale_id: UUID
    variant_id: UUID
    product_id: UUID
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    total: Decimal
    preparation_status: str | None = None
    kitchen_station_id: UUID | None = None
    options: list[SaleItemOptionResponse] = []


# ─────────────────────────────────────────────
# Sale
# ─────────────────────────────────────────────

class SaleCreate(APIBaseSchema):
    """
    A complete sales transaction submitted by a POS device.

    Designed for both online (web) and offline-first (Android) flows.
    The Android app generates UUIDs locally and includes them on sync.
    A sale must have at least one item.
    """

    id: UUID | None = Field(
        None,
        description="Client-generated UUID for offline sync. Server generates if omitted.",
    )
    branch_id: UUID
    device_id: UUID
    user_id: UUID
    sale_number: str = Field(..., min_length=1, max_length=50)
    sold_at: datetime = Field(..., description="Actual sale time on the POS device.")
    subtotal: Decimal = Field(..., ge=Decimal("0"))
    discount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    tax_rate: Decimal | None = Field(None, description="Decimal rate, e.g. 0.15 for 15%.")
    total: Decimal = Field(..., ge=Decimal("0"))
    status: str = Field(default="COMPLETED", max_length=30)
    order_status: str | None = Field(
        None,
        max_length=30,
        description="KDS order status. Null means KDS not in use.",
    )
    promotion_id: UUID | None = None
    deal_id: UUID | None = None
    items: list[SaleItemCreate] = Field(..., min_length=1)


class SaleStatusUpdate(APIBaseSchema):
    """
    Allowed status transition for an unpaid sale (`CANCELLED`).
    """

    status: str = Field(..., max_length=30)


class SaleResponse(UUIDResponseSchema, TimestampResponseSchema, SyncResponseSchema):
    """
    Complete sale record returned by the API.
    """

    branch_id: UUID
    device_id: UUID
    user_id: UUID
    session_id: UUID | None = None
    cashier_name: str = Field(validation_alias=AliasPath("user", "full_name"))
    cashier_username: str = Field(validation_alias=AliasPath("user", "username"))
    sale_number: str
    sold_at: datetime
    subtotal: Decimal
    discount: Decimal
    tax_amount: Decimal
    tax_rate: Decimal | None = None
    total: Decimal
    status: str
    order_status: str | None = None
    promotion_id: UUID | None = None
    deal_id: UUID | None = None
    items: list[SaleItemResponse] = []
    payments: list[PaymentResponse] = []


class SaleListResponse(UUIDResponseSchema, TimestampResponseSchema, SyncResponseSchema):
    """
    Lightweight sale record used in list endpoints (no nested items).
    """

    branch_id: UUID
    device_id: UUID
    user_id: UUID
    session_id: UUID | None = None
    cashier_name: str = Field(validation_alias=AliasPath("user", "full_name"))
    cashier_username: str = Field(validation_alias=AliasPath("user", "username"))
    sale_number: str
    sold_at: datetime
    subtotal: Decimal
    discount: Decimal
    tax_amount: Decimal
    tax_rate: Decimal | None = None
    total: Decimal
    status: str
    order_status: str | None = None
    promotion_id: UUID | None = None
    deal_id: UUID | None = None
