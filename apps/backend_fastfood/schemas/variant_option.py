# schemas/variant_option.py
#
# NO price field — pricing lives only on Variant.sale_price (spec D1).

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
    SyncResponseSchema,
)


class VariantOptionCreate(APIBaseSchema):
    id: UUID | None = Field(
        None,
        description="Client-generated UUID for offline sync. Server generates if omitted.",
    )
    name: str = Field(..., min_length=1, max_length=100)
    display_order: int = Field(default=0, ge=0)


class VariantOptionUpdate(APIBaseSchema):
    name: str | None = Field(None, min_length=1, max_length=100)
    display_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class VariantOptionResponse(UUIDResponseSchema, TimestampResponseSchema, SyncResponseSchema):
    option_group_id: UUID
    name: str
    display_order: int
    is_active: bool
    component_product_id: UUID | None = None


class VariantOptionComponentSet(APIBaseSchema):
    """Starts tracking this option as a shared inventory component (Laptop
    Store model) — auto-creates the one real Product+Variant it now
    represents. A no-op (returns current state) if already tracked; use the
    normal PATCH /variants/{id} and stock endpoints against
    component_product_id's default_variant_id to change price/stock
    afterward.

    Always quantity-tracked — components (RAM sticks, storage drives, ...)
    are counted, not individually serialized."""

    sale_price: Decimal = Field(..., ge=Decimal("0"))
    cost_price: Decimal | None = Field(None, ge=Decimal("0"))
    opening_stock_by_branch: dict[UUID, int] | None = None
