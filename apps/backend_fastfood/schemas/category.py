# schemas/category.py

from uuid import UUID

from pydantic import Field

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
    SyncResponseSchema,
)


class CategoryCreate(APIBaseSchema):
    """
    Data required to create a product category under a business.

    Supports offline-first: id may be provided by the Android client.
    If omitted, the server generates it.
    """

    id: UUID | None = Field(
        None,
        description="Client-generated UUID for offline sync. Server generates if omitted.",
    )
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    image_path: str | None = Field(None, max_length=500)
    display_order: int = Field(default=0, ge=0)


class CategoryUpdate(APIBaseSchema):
    """
    Fields that may be updated on an existing category.
    """

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    image_path: str | None = Field(None, max_length=500)
    display_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class CategoryResponse(UUIDResponseSchema, TimestampResponseSchema, SyncResponseSchema):
    """
    Category record returned by the API including sync metadata.
    """

    business_id: UUID
    name: str
    description: str | None
    image_path: str | None
    display_order: int
    is_active: bool
