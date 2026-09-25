# schemas/product.py

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
    SyncResponseSchema,
)


class PricedVariantInput(APIBaseSchema):
    """One selected value of a create-time Priced Variant Group (e.g. one
    color) — see ProductCreate.priced_variants. sale_price/cost_price are
    each value's own full price (the Add Product form pre-fills them from
    ProductCreate.price/cost_price as an editable default) — not a delta."""

    option_id: UUID
    sale_price: Decimal = Field(..., ge=Decimal("0"))
    cost_price: Decimal | None = Field(default=None, ge=Decimal("0"))
    opening_stock_by_branch: dict[UUID, int] | None = Field(
        None,
        description="Applied to this value's own combination Variant when "
                     "allow_inventory_tracking is set. Keys must exactly "
                     "match the branches this product is being assigned to.",
    )


class ProductCreate(APIBaseSchema):
    """
    Data required to create a product under a category.

    Supports offline-first: id may be provided by the Android client.

    price seeds the default Variant's sale_price (spec D1) — there is no
    base_price on Product itself. Every product always gets a zero-option
    default Variant at creation time.
    """

    id: UUID | None = Field(
        None,
        description="Client-generated UUID for offline sync. Server generates if omitted.",
    )
    product_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(None, max_length=500)
    image_path: str | None = Field(None, max_length=500)
    sku: str | None = Field(
        None, max_length=100,
        description="Optional. Gated by template.config.product_fields.sku — never required.",
    )
    warranty: str | None = Field(
        None, max_length=100,
        description="Optional free-text warranty terms, e.g. '1 year'. Gated by "
                     "template.config.product_fields.warranty — never required.",
    )
    price: Decimal = Field(..., ge=Decimal("0"), description="Seeds the default variant's sale_price.")
    cost_price: Decimal | None = Field(
        None, ge=Decimal("0"),
        description="Optionally seeds the default variant's cost_price.",
    )
    display_order: int = Field(default=0, ge=0)
    preparation_station_id: UUID | None = Field(
        None,
        description="KDS routing: which station prepares this product.",
    )
    allow_inventory_tracking: bool = Field(
        default=False,
        description="Master switch allowing this product's variants to track inventory.",
    )
    all_branches: bool | None = Field(
        None, description="Branch assignment applied atomically with creation. Defaults to "
                           "True (every branch) when omitted.",
    )
    branch_ids: list[UUID] | None = Field(
        None, description="Used when all_branches=False.",
    )
    opening_stock_by_branch: dict[UUID, int] | None = Field(
        None,
        description="Applied to the default variant when allow_inventory_tracking is set. "
                     "Keys must exactly match the branches this product is being assigned to.",
    )
    priced_variant_group_id: UUID | None = Field(
        None,
        description="A shared VariantOptionGroup (e.g. 'Colors') to attach as "
                     "usage_type='specification' and seed with one priced, "
                     "stocked combination Variant per entry in priced_variants. "
                     "Create-time only; colors are not added later from the "
                     "product detail page.",
    )
    priced_variants: list[PricedVariantInput] | None = Field(
        None,
        description="One entry per selected value of priced_variant_group_id. "
                     "Ignored (group is never attached) when empty, so a "
                     "product is never left with a required group and zero "
                     "satisfying variants.",
    )


class ProductUpdate(APIBaseSchema):
    """
    Fields that may be updated on an existing product.
    """

    category_id: UUID | None = Field(
        None,
        description=(
            "Moves the product to a different category. Re-syncs its Variant "
            "Option Group attachments to match the new category's templates — "
            "see CategoryVariantOptionGroupService.resync_product_category_change."
        ),
    )
    name: str | None = Field(None, min_length=1, max_length=150)
    description: str | None = Field(None, max_length=500)
    image_path: str | None = Field(None, max_length=500)
    sku: str | None = Field(None, max_length=100)
    warranty: str | None = Field(None, max_length=100)
    price: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        description="Updates the default Variant price when the product has no priced combination variants.",
    )
    display_order: int | None = Field(None, ge=0)
    is_active: bool | None = None
    preparation_station_id: UUID | None = None
    allow_inventory_tracking: bool | None = None


class ProductResponse(UUIDResponseSchema, TimestampResponseSchema, SyncResponseSchema):
    """
    Product record returned by the API including sync metadata.
    """

    category_id: UUID
    product_code: str
    name: str
    description: str | None
    image_path: str | None
    sku: str | None = None
    warranty: str | None = None
    display_order: int
    is_active: bool
    all_branches: bool = True
    preparation_station_id: UUID | None = None
    default_variant_id: UUID | None = None
    variant_option_group_count: int = 0
    specification_group_count: int = 0
    # Whether this product has any real priced combination Variant (beyond
    # its own always-present zero-option default) — the signal the dashboard
    # uses to lock/unlock the base Price field, instead of
    # specification_group_count (a group can be attached with zero actual
    # combinations, which must NOT lock anything — see product_service.py).
    has_combination_variants: bool = False
    addon_group_count: int = 0
    allow_inventory_tracking: bool = False
    # A component is still a normal, independently sellable Product with its
    # own default Variant and stock pool. This flag only changes how catalog
    # administration treats it: component choices belong to the configurable
    # parent product, never recursively to the component itself.
    is_inventory_component: bool = False
    component_option_id: UUID | None = None
    component_option_name: str | None = None
    component_group_name: str | None = None
    # Convenience — the default variant's sale_price, so simple products
    # (no Variant Option Groups) can be listed/edited without a second call.
    price: Decimal | None = None


class ProductSkuSuggestion(APIBaseSchema):
    """A suggested, currently-unused SKU for a new product — a convenience
    only (sku has no DB-level uniqueness constraint); the tenant may still
    edit or replace it before saving."""

    sku: str
