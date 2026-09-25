from decimal import Decimal
from uuid import UUID

from pydantic import Field

from schemas.common import APIBaseSchema, UUIDResponseSchema


class VariantCreate(APIBaseSchema):
    option_ids: list[UUID] = Field(default_factory=list, max_length=50)
    sale_price: Decimal = Field(..., ge=Decimal("0"))
    cost_price: Decimal | None = Field(default=None, ge=Decimal("0"))
    tracks_inventory: bool | None = Field(
        default=None,
        description="Omit/null to auto-default from business policy (tracked "
                     "whenever the template forces tracking or the product "
                     "already allows it) — pass explicitly to override.",
    )
    opening_stock_by_branch: dict[UUID, int] | None = None


class VariantUpdate(APIBaseSchema):
    model_config = {"extra": "forbid"}
    sale_price: Decimal | None = Field(default=None, ge=Decimal("0"))
    cost_price: Decimal | None = Field(default=None, ge=Decimal("0"))
    compare_price: Decimal | None = Field(default=None, ge=Decimal("0"))
    tracks_inventory: bool | None = None
    opening_stock_by_branch: dict[UUID, int] | None = None


class VariantStockUpdate(APIBaseSchema):
    stock_quantity: int = Field(..., ge=0, strict=True)
    note: str | None = Field(default=None, max_length=255)


class VariantStockAdjustment(APIBaseSchema):
    quantity: int = Field(..., gt=0, strict=True)
    note: str | None = Field(default=None, max_length=255)


class VariantStockTransfer(APIBaseSchema):
    """Moves stock for one Variant from one branch to another. Works
    identically whether the variant is a 'fixed' product's own SKU or the
    shared component behind an 'upgradable' product — both are just Variant
    stock underneath."""

    from_branch_id: UUID
    to_branch_id: UUID
    quantity: int = Field(..., gt=0, strict=True)
    note: str | None = Field(default=None, max_length=255)


class VariantResponse(UUIDResponseSchema):
    product_id: UUID
    option_value_ids: list[UUID]
    sale_price: Decimal
    cost_price: Decimal | None = None
    compare_price: Decimal | None = None
    tracks_inventory: bool
    is_default: bool
    stock_by_branch: dict[str, int] | None = None
    opening_stock: int | None = None
    product_name: str | None = None
    variant_name: str | None = None
    # Whether this SKU currently has a value for every required Variant
    # Option Group on its product — a variant can go stale (e.g. a group
    # attached after it was created) without being deleted. Always computed
    # server-side (VariantService.compute_sellability), never hardcoded, so
    # the tenant dashboard and POS can both warn before/while stock is added
    # to a SKU that can never actually be sold.
    sellable: bool = True
    sellable_reason: str | None = None


class SyncedVariantResponse(VariantResponse):
    allow_inventory_tracking: bool = False
