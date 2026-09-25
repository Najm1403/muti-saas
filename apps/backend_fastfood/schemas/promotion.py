# schemas/promotion.py

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from schemas.common import APIBaseSchema, UUIDResponseSchema, TimestampResponseSchema


class PromotionCreate(APIBaseSchema):
    """Data required to create a promotion. BXGY and FREE_ITEM types require a reward target."""

    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(None, max_length=500)
    promo_code: str | None = Field(None, max_length=50)
    type: Literal["PERCENTAGE", "FLAT_AMOUNT", "BXGY", "FREE_ITEM"]
    discount_value: Decimal = Field(..., ge=Decimal("0"))

    trigger_product_id: UUID | None = None
    trigger_category_id: UUID | None = None
    trigger_min_qty: int | None = Field(None, ge=1)
    trigger_min_amount: Decimal | None = Field(None, ge=Decimal("0"))

    reward_product_id: UUID | None = None
    reward_category_id: UUID | None = None
    reward_quantity: int | None = Field(None, ge=1)
    reward_discount_type: Literal["FREE", "PERCENTAGE", "FLAT_AMOUNT"] | None = None
    reward_discount_value: Decimal | None = Field(None, ge=Decimal("0"))

    valid_from: datetime | None = None
    valid_until: datetime | None = None
    max_uses: int | None = Field(None, ge=1)

    @model_validator(mode="after")
    def check_bxgy_fields(self) -> "PromotionCreate":
        if self.type in ("BXGY", "FREE_ITEM"):
            if not self.reward_product_id and not self.reward_category_id:
                raise ValueError(
                    "BXGY and FREE_ITEM promotions require reward_product_id or reward_category_id."
                )
        return self


class PromotionUpdate(APIBaseSchema):
    """Fields that may be updated on an existing promotion."""

    name: str | None = Field(None, min_length=1, max_length=150)
    description: str | None = Field(None, max_length=500)
    promo_code: str | None = Field(None, max_length=50)
    discount_value: Decimal | None = Field(None, ge=Decimal("0"))
    trigger_min_qty: int | None = Field(None, ge=1)
    trigger_min_amount: Decimal | None = Field(None, ge=Decimal("0"))
    reward_quantity: int | None = Field(None, ge=1)
    reward_discount_value: Decimal | None = Field(None, ge=Decimal("0"))
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    max_uses: int | None = Field(None, ge=1)
    is_active: bool | None = None


class PromotionResponse(UUIDResponseSchema, TimestampResponseSchema):
    """Promotion record returned by the API."""

    tenant_id: UUID
    name: str
    description: str | None
    promo_code: str | None
    type: str
    discount_value: Decimal
    trigger_product_id: UUID | None
    trigger_category_id: UUID | None
    trigger_min_qty: int | None
    trigger_min_amount: Decimal | None
    reward_product_id: UUID | None
    reward_category_id: UUID | None
    reward_quantity: int | None
    reward_discount_type: str | None
    reward_discount_value: Decimal | None
    valid_from: datetime | None
    valid_until: datetime | None
    max_uses: int | None
    used_count: int
    is_active: bool
    all_branches: bool = True


# ─────────────────────────────────────────────
# Evaluate endpoint schemas
# ─────────────────────────────────────────────

class CartItem(APIBaseSchema):
    """A single item in the cart submitted for promotion evaluation."""

    product_id: UUID
    category_id: UUID | None = None
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., ge=Decimal("0"))


class PromotionEvaluateRequest(APIBaseSchema):
    """Request body for the /promotions/evaluate endpoint."""

    items: list[CartItem]
    promo_code: str | None = None
    order_total: Decimal = Field(..., ge=Decimal("0"))


class ApplicablePromotion(APIBaseSchema):
    """A promotion that is applicable to the submitted cart."""

    promotion_id: UUID
    promotion_name: str
    promo_code: str | None
    type: str
    discount_amount: Decimal
    reward_product_id: UUID | None = None
    reward_quantity: int | None = None
    message: str
