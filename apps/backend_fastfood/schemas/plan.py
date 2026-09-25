# schemas/plan.py

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from schemas.common import APIBaseSchema


class PlanCreate(APIBaseSchema):
    """Fields required to create a new subscription plan."""

    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None
    price_monthly: Decimal = Field(..., gt=0, decimal_places=2)
    price_yearly: Decimal = Field(..., gt=0, decimal_places=2)
    discount_monthly_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100, decimal_places=2)
    discount_yearly_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100, decimal_places=2)
    max_restaurants: int = Field(default=1, ge=-1)
    max_branches: int = Field(default=1, ge=-1)
    max_users: int = Field(default=5, ge=-1)
    max_devices: int = Field(default=2, ge=-1)


class PlanUpdate(APIBaseSchema):
    """All fields optional — only provided fields are updated."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    price_monthly: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    price_yearly: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    discount_monthly_pct: Decimal | None = Field(default=None, ge=0, le=100, decimal_places=2)
    discount_yearly_pct: Decimal | None = Field(default=None, ge=0, le=100, decimal_places=2)
    max_restaurants: int | None = Field(default=None, ge=-1)
    max_branches: int | None = Field(default=None, ge=-1)
    max_users: int | None = Field(default=None, ge=-1)
    max_devices: int | None = Field(default=None, ge=-1)
    is_active: bool | None = None


class PlanResponse(APIBaseSchema):
    """Plan data returned by the API."""

    id: UUID
    name: str
    description: str | None
    price_monthly: Decimal
    price_yearly: Decimal
    discount_monthly_pct: Decimal = Decimal("0")
    discount_yearly_pct: Decimal = Decimal("0")
    max_restaurants: int
    max_branches: int
    max_users: int
    max_devices: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
