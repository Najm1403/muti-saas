# schemas/addon_group.py

from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
    SyncResponseSchema,
)


class AddonGroupCreate(APIBaseSchema):
    id: UUID | None = Field(
        None,
        description="Client-generated UUID for offline sync. Server generates if omitted.",
    )
    name: str = Field(..., min_length=1, max_length=100)
    selection_type: Literal["single", "multiple"] = "multiple"
    min_select: int = Field(default=0, ge=0)
    max_select: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def check_selection_range(self) -> "AddonGroupCreate":
        if self.max_select is not None and self.min_select > self.max_select:
            raise ValueError("min_select cannot be greater than max_select.")
        return self


class AddonGroupUpdate(APIBaseSchema):
    name: str | None = Field(None, min_length=1, max_length=100)
    selection_type: Literal["single", "multiple"] | None = None
    min_select: int | None = Field(None, ge=0)
    max_select: int | None = Field(None, ge=1)
    is_active: bool | None = None


class AddonGroupResponse(UUIDResponseSchema, TimestampResponseSchema, SyncResponseSchema):
    business_id: UUID
    name: str
    selection_type: str
    min_select: int
    max_select: int | None
    is_active: bool


class ProductAddonGroupAttach(APIBaseSchema):
    """Attach an existing (shared) Add-on Group to a product."""

    addon_group_id: UUID
    display_order: int = Field(default=0, ge=0)


class ProductAddonGroupResponse(APIBaseSchema):
    id: UUID
    product_id: UUID
    addon_group_id: UUID
    display_order: int
    # Denormalized for convenience.
    name: str
    selection_type: str
    min_select: int
    max_select: int | None
