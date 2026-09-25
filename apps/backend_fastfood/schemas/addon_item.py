# schemas/addon_item.py

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
    SyncResponseSchema,
)


class AddonItemCreate(APIBaseSchema):
    id: UUID | None = Field(
        None,
        description="Client-generated UUID for offline sync. Server generates if omitted.",
    )
    name: str = Field(..., min_length=1, max_length=100)
    price_delta: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    default_selected: bool = False
    display_order: int = Field(default=0, ge=0)


class AddonItemUpdate(APIBaseSchema):
    name: str | None = Field(None, min_length=1, max_length=100)
    price_delta: Decimal | None = Field(None, ge=Decimal("0"))
    default_selected: bool | None = None
    display_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class AddonItemResponse(UUIDResponseSchema, TimestampResponseSchema, SyncResponseSchema):
    addon_group_id: UUID
    name: str
    price_delta: Decimal
    default_selected: bool
    display_order: int
    is_active: bool
