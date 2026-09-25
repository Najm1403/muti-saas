# schemas/product_spec.py
#
# Repeatable key/value specification rows for a product (spec Part B / G2).
# Gated by template.config.product_fields.specs — never required.

from uuid import UUID

from pydantic import Field

from schemas.common import APIBaseSchema, UUIDResponseSchema, TimestampResponseSchema


class ProductSpecCreate(APIBaseSchema):
    spec_key: str = Field(..., min_length=1, max_length=100)
    spec_value: str = Field(..., min_length=1, max_length=500)
    sort_order: int = Field(default=0, ge=0)


class ProductSpecUpdate(APIBaseSchema):
    spec_key: str | None = Field(None, min_length=1, max_length=100)
    spec_value: str | None = Field(None, min_length=1, max_length=500)
    sort_order: int | None = Field(None, ge=0)


class ProductSpecResponse(UUIDResponseSchema, TimestampResponseSchema):
    product_id: UUID
    spec_key: str
    spec_value: str
    sort_order: int
