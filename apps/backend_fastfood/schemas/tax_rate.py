# schemas/tax_rate.py

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from schemas.common import APIBaseSchema, UUIDResponseSchema, TimestampResponseSchema


class TaxRateCreate(APIBaseSchema):
    """Data required to create a tax rate for the tenant."""

    name: str = Field(..., min_length=1, max_length=100)
    rate: Decimal = Field(..., ge=Decimal("0"), le=Decimal("100"))
    is_inclusive: bool = False
    is_default: bool = False


class TaxRateUpdate(APIBaseSchema):
    """Fields that may be updated on an existing tax rate."""

    name: str | None = Field(None, min_length=1, max_length=100)
    rate: Decimal | None = Field(None, ge=Decimal("0"), le=Decimal("100"))
    is_inclusive: bool | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class TaxRateResponse(UUIDResponseSchema, TimestampResponseSchema):
    """Tax rate record returned by the API."""

    tenant_id: UUID
    name: str
    rate: Decimal
    is_inclusive: bool
    is_default: bool
    is_active: bool
