# schemas/business_template.py
#
# Platform-managed preset for a BUSINESS TYPE — see spec A3.

from uuid import UUID

from pydantic import Field

from schemas.common import APIBaseSchema, UUIDResponseSchema, TimestampResponseSchema


class BusinessTemplateCreate(APIBaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    config: dict = Field(..., description="Shape documented in apps/COMPLETE-IMPLEMENTATION-SPEC.md Part C.")


class BusinessTemplateUpdate(APIBaseSchema):
    name: str | None = Field(None, min_length=1, max_length=100)
    config: dict | None = None


class BusinessTemplateResponse(UUIDResponseSchema, TimestampResponseSchema):
    name: str
    config: dict
