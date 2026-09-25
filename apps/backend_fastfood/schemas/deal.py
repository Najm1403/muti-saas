# schemas/deal.py

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from schemas.common import APIBaseSchema, UUIDResponseSchema, TimestampResponseSchema


class DealItemCreate(APIBaseSchema):
    """Data required to add an item to a deal bundle. Requires product_id or category_id."""

    product_id: UUID | None = None
    category_id: UUID | None = None
    quantity: int = Field(default=1, ge=1)
    is_free: bool = False
    sort_order: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_target(self) -> "DealItemCreate":
        if not self.product_id and not self.category_id:
            raise ValueError("Deal item must specify product_id or category_id.")
        return self


class DealItemUpdate(APIBaseSchema):
    """Fields that may be updated on an existing deal item."""

    quantity: int | None = Field(None, ge=1)
    is_free: bool | None = None
    sort_order: int | None = Field(None, ge=0)


class DealItemResponse(UUIDResponseSchema, TimestampResponseSchema):
    """Deal item record returned by the API."""

    deal_id: UUID
    product_id: UUID | None
    category_id: UUID | None
    quantity: int
    is_free: bool
    sort_order: int


class DealCreate(APIBaseSchema):
    """Data required to create a deal bundle."""

    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(None, max_length=500)
    deal_code: str = Field(..., min_length=2, max_length=50)
    image_path: str | None = Field(None, max_length=500)
    fixed_price: Decimal | None = Field(None, ge=Decimal("0"))
    discount_value: Decimal | None = Field(None, ge=Decimal("0"))
    discount_type: Literal["FLAT", "PERCENTAGE"] | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    display_order: int = Field(default=0, ge=0)


class DealUpdate(APIBaseSchema):
    """Fields that may be updated on an existing deal."""

    name: str | None = Field(None, min_length=1, max_length=150)
    description: str | None = Field(None, max_length=500)
    image_path: str | None = Field(None, max_length=500)
    fixed_price: Decimal | None = Field(None, ge=Decimal("0"))
    discount_value: Decimal | None = Field(None, ge=Decimal("0"))
    discount_type: Literal["FLAT", "PERCENTAGE"] | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    display_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class DealResponse(UUIDResponseSchema, TimestampResponseSchema):
    """Deal record returned by the API, including its bundle items."""

    tenant_id: UUID
    name: str
    description: str | None
    deal_code: str
    image_path: str | None
    fixed_price: Decimal | None
    discount_value: Decimal | None
    discount_type: str | None
    valid_from: datetime | None
    valid_until: datetime | None
    display_order: int
    is_active: bool
    all_branches: bool = True
    items: list[DealItemResponse] = []
