# schemas/business.py

from uuid import UUID

from pydantic import Field, field_validator

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
    SyncResponseSchema,
)


class BusinessCreate(APIBaseSchema):
    """
    Data required to create a Business under a tenant.

    A tenant has exactly one Business (see spec A2) — this is normally only
    ever called once, from the onboarding flow.
    """

    name: str = Field(..., min_length=1, max_length=150)
    currency: str = Field(
        default="Rs.",
        max_length=8,
        description="Money display string synced to POS devices (e.g. 'Rs.', '$').",
    )
    low_stock_threshold: int = Field(default=5, ge=0, le=1_000_000)


class BusinessUpdate(APIBaseSchema):
    """
    Fields that may be updated on the tenant's Business.
    """

    name: str | None = Field(None, min_length=1, max_length=150)
    currency: str | None = Field(None, max_length=8)
    receipt_tagline: str | None = Field(None, max_length=80)
    receipt_thank_you: str | None = Field(None, max_length=120)
    receipt_terms: str | None = Field(None, max_length=1000)
    low_stock_threshold: int | None = Field(None, ge=0, le=1_000_000)
    is_active: bool | None = None

    @field_validator("receipt_tagline")
    @classmethod
    def tagline_is_short(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.split())
        if len(value.split()) > 4:
            raise ValueError("Receipt tagline must contain no more than 4 words.")
        return value or None


class BusinessResponse(UUIDResponseSchema, TimestampResponseSchema, SyncResponseSchema):
    """
    Business record returned by the API.
    """

    tenant_id: UUID
    name: str
    currency: str
    logo_path: str | None = None
    receipt_tagline: str | None = None
    receipt_thank_you: str | None = None
    receipt_terms: str | None = None
    low_stock_threshold: int = 5
    is_active: bool
