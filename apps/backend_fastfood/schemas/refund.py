# schemas/refund.py

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from schemas.units import Units
from pydantic import Field

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
    SyncResponseSchema,
)


# ─────────────────────────────────────────────
# RefundItem
# ─────────────────────────────────────────────

class RefundItemCreate(APIBaseSchema):
    """
    One item being returned as part of a refund.

    product_name and unit_price are snapshots — the original
    SaleItem is never modified.
    """

    sale_item_id: UUID
    product_name: str = Field(..., max_length=150)
    quantity: Units = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=Decimal("0"))
    amount: Decimal = Field(..., ge=Decimal("0"))


class RefundItemResponse(UUIDResponseSchema, TimestampResponseSchema, SyncResponseSchema):
    """
    Refunded item returned as part of a Refund response.
    """

    refund_id: UUID
    sale_item_id: UUID
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal


# ─────────────────────────────────────────────
# Refund
# ─────────────────────────────────────────────

class RefundCreate(APIBaseSchema):
    """
    A refund issued against a sale.

    Supports both full and partial refunds.
    At least one item must be included.
    """

    id: UUID | None = Field(
        None,
        description="Client-generated UUID for offline sync. Server generates if omitted.",
    )
    sale_id: UUID
    branch_id: UUID
    device_id: UUID
    refund_number: str = Field(..., min_length=1, max_length=50)
    refunded_at: datetime = Field(..., description="Actual refund time on the POS device.")
    amount: Decimal = Field(..., ge=Decimal("0"))
    refund_method: str = Field(..., max_length=50)
    reason: str | None = Field(None, max_length=500)
    items: list[RefundItemCreate] = Field(..., min_length=1)


class RefundResponse(UUIDResponseSchema, TimestampResponseSchema, SyncResponseSchema):
    """
    Complete refund record returned by the API.
    """

    sale_id: UUID
    branch_id: UUID
    device_id: UUID
    refund_number: str
    refunded_at: datetime
    amount: Decimal
    refund_method: str
    payment_breakdown: dict[str, Decimal] = {}
    reason: str | None
    status: str
    refund_type: str = "RETURN"
    processed_by_user_id: UUID | None = None
    session_id: UUID | None = None
    items: list[RefundItemResponse] = []


class PosReturnItemCreate(APIBaseSchema):
    """A server-priced quantity selected from an existing invoice."""

    sale_item_id: UUID
    quantity: Units = Field(..., gt=0)


class PosReturnCreate(APIBaseSchema):
    reason: str | None = Field(None, max_length=500)
    items: list[PosReturnItemCreate] = Field(..., min_length=1)


class PosCancelCreate(APIBaseSchema):
    reason: str = Field(..., min_length=1, max_length=500)


class PosRefundResult(APIBaseSchema):
    id: UUID
    sale_id: UUID
    sale_number: str
    refund_number: str
    refund_type: str
    amount: Decimal
    status: str
