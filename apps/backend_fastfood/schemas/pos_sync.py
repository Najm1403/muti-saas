# schemas/pos_sync.py
#
# Payloads for the POS sync endpoints.
# Full sync: initial device setup — complete menu snapshot for the branch.
# Delta sync: pull only records changed since last sync time (currently
# implemented as a full-replace re-sync — see SyncRepository.deltaSync on
# the Flutter side).
# Upload: push batch of offline-queued sales to the cloud.

from __future__ import annotations
from schemas.variant import SyncedVariantResponse

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from schemas.units import Units
from pydantic import Field

from schemas.common import APIBaseSchema


# ──────────────────────────────────────────────────────────
# Menu objects (minimal fields needed by the POS app)
# ──────────────────────────────────────────────────────────

class PosSyncVariantOption(APIBaseSchema):
    id: UUID
    option_group_id: UUID
    name: str
    display_order: int
    is_active: bool
    # Laptop Store shareable-inventory model — set only when this option is
    # tracked as a shared inventory component (VariantOption.
    # component_product_id resolved to its default Variant). The POS
    # resolves this option's own price/stock by looking this id up in the
    # already-synced `variants` list — no separate data stream needed.
    component_variant_id: UUID | None = None


class PosSyncVariantOptionGroup(APIBaseSchema):
    """A shared Variant Option Group as attached to one product — see
    models/product_variant_option_group.py. is_required is the per-product
    override; the group itself has no min/max_selections (always single-select,
    spec A1)."""
    id: UUID
    product_id: UUID
    name: str
    is_required: bool
    display_order: int
    options: list[PosSyncVariantOption] = []
    # Laptop Store shareable-inventory model — see
    # models/product_variant_option_group.py. 'specification' (default):
    # unchanged today's behavior, options define a combination Variant.
    # 'inventory_component': the POS must offer these options as a dynamic,
    # independently priced/stocked pick at sale time instead (never baked
    # into a combination). allowed_option_ids empty = every option above is
    # offered; non-empty = only those ids.
    usage_type: str = "specification"
    allowed_option_ids: list[UUID] = Field(default_factory=list)


class PosSyncAddonItem(APIBaseSchema):
    id: UUID
    addon_group_id: UUID
    name: str
    price_delta: Decimal
    default_selected: bool
    display_order: int
    is_active: bool


class PosSyncAddonGroup(APIBaseSchema):
    """A shared Add-on Group as attached to one product — see
    models/product_addon_group.py. Never feeds into variant generation."""
    id: UUID
    product_id: UUID
    name: str
    selection_type: str
    min_select: int
    max_select: int | None
    display_order: int
    items: list[PosSyncAddonItem] = []


class PosSyncProduct(APIBaseSchema):
    id: UUID
    category_id: UUID
    product_code: str
    name: str
    description: str | None
    price: Decimal
    # Default (zero-option) variant's sale_price — spec D1, no more base_price.
    image_path: str | None
    display_order: int
    is_active: bool
    default_variant_id: UUID | None = None
    variant_option_groups: list[PosSyncVariantOptionGroup] = []
    addon_groups: list[PosSyncAddonGroup] = []
    allow_inventory_tracking: bool = False


class PosSyncCategory(APIBaseSchema):
    id: UUID
    name: str
    description: str | None
    image_path: str | None
    display_order: int
    is_active: bool


class PosSyncTaxRate(APIBaseSchema):
    id: UUID
    name: str
    rate: Decimal
    is_inclusive: bool
    is_default: bool


class PosSyncDealItem(APIBaseSchema):
    id: UUID
    product_id: UUID | None
    category_id: UUID | None
    quantity: int
    is_free: bool
    sort_order: int


class PosSyncDeal(APIBaseSchema):
    id: UUID
    name: str
    description: str | None
    deal_code: str
    fixed_price: Decimal | None
    discount_value: Decimal | None
    discount_type: str | None
    valid_from: datetime | None
    valid_until: datetime | None
    is_active: bool
    items: list[PosSyncDealItem] = []


class PosSyncPromotion(APIBaseSchema):
    id: UUID
    name: str
    promo_code: str | None
    type: str
    discount_value: Decimal
    trigger_min_qty: int | None
    trigger_min_amount: Decimal | None
    trigger_product_id: UUID | None
    trigger_category_id: UUID | None
    valid_from: datetime | None
    valid_until: datetime | None
    max_uses: int | None
    used_count: int
    reward_product_id: UUID | None = None
    reward_category_id: UUID | None = None
    reward_quantity: int | None = None
    reward_discount_type: str | None = None
    reward_discount_value: Decimal | None = None
    is_active: bool


# ──────────────────────────────────────────────────────────
# Sync responses
# ──────────────────────────────────────────────────────────

class PosSyncResponse(APIBaseSchema):
    """Complete branch snapshot for initial device setup or full refresh."""

    branch_id: UUID
    branch_name: str
    branch_code: str
    branch_address: str | None = None
    branch_phone: str | None = None
    business_name: str
    receipt_logo_base64: str | None = None
    receipt_tagline: str | None = None
    receipt_thank_you: str | None = None
    receipt_terms: str | None = None
    currency: str = "Rs."
    low_stock_threshold: int = 5
    synced_at: datetime
    categories: list[PosSyncCategory] = []
    products: list[PosSyncProduct] = []
    tax_rates: list[PosSyncTaxRate] = []
    deals: list[PosSyncDeal] = []
    promotions: list[PosSyncPromotion] = []
    variants: list[SyncedVariantResponse] = []
    inventory_model_version: int = 6
    # Business Template config driving which POS layout the client renders
    # (spec Part C / F3/G4) — synced so it's available offline, same as
    # everything else in this payload. Unknown values must fall back to the
    # side-panel layout client-side, never crash.
    pos_layout: str = "grid_with_variant_picker"


class PosDeltaSyncResponse(APIBaseSchema):
    """Changed records only — everything with updated_at > since."""

    branch_id: UUID
    branch_name: str
    branch_code: str
    branch_address: str | None = None
    branch_phone: str | None = None
    business_name: str
    receipt_logo_base64: str | None = None
    receipt_tagline: str | None = None
    receipt_thank_you: str | None = None
    receipt_terms: str | None = None
    low_stock_threshold: int = 5
    since: datetime
    synced_at: datetime
    categories: list[PosSyncCategory] = []
    products: list[PosSyncProduct] = []
    tax_rates: list[PosSyncTaxRate] = []
    deals: list[PosSyncDeal] = []
    promotions: list[PosSyncPromotion] = []
    variants: list[SyncedVariantResponse] = []
    inventory_model_version: int = 6
    pos_layout: str = "grid_with_variant_picker"


# ──────────────────────────────────────────────────────────
# Offline sale upload
# ──────────────────────────────────────────────────────────

class PosOfflineOption(APIBaseSchema):
    id: UUID | None = None
    variant_option_id: UUID
    option_name: str


class PosOfflineAddon(APIBaseSchema):
    id: UUID | None = None
    addon_item_id: UUID
    addon_name: str
    price_delta: Decimal = Decimal("0.00")
    was_removed: bool = False


class PosOfflineItem(APIBaseSchema):
    id: UUID | None = None
    variant_id: UUID
    product_id: UUID
    product_name: str
    quantity: Units = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=Decimal("0"))
    discount: Decimal = Decimal("0.00")
    total: Decimal = Field(..., ge=Decimal("0"))
    options: list[PosOfflineOption] = []
    addons: list[PosOfflineAddon] = []
    # Laptop Store shareable-inventory model — see PosSaleItemCreate's
    # matching fields (schemas/pos_sale.py).
    parent_item_id: UUID | None = None
    satisfies_option_group_id: UUID | None = None
    component_option_id: UUID | None = None


class PosOfflinePayment(APIBaseSchema):
    payment_method: str = Field(..., max_length=50)
    amount: Decimal = Field(..., gt=Decimal("0"))
    reference: str | None = Field(None, max_length=150)


class PosOfflineSale(APIBaseSchema):
    """One offline-queued sale submitted for cloud sync."""

    id: UUID | None = Field(None, description="Client-generated UUID preserved on server.")
    origin_proof: str | None = None
    session_id: UUID | None = None
    sale_number: str = Field(..., max_length=50)
    sold_at: datetime
    subtotal: Decimal = Field(..., ge=Decimal("0"))
    discount: Decimal = Decimal("0.00")
    total: Decimal = Field(..., ge=Decimal("0"))
    tax_amount: Decimal = Decimal("0.00")
    tax_rate: Decimal | None = None
    promotion_id: UUID | None = None
    deal_id: UUID | None = None
    items: list[PosOfflineItem] = Field(..., min_length=1)
    payments: list[PosOfflinePayment] = []


class PosUploadRequest(APIBaseSchema):
    """Batch of offline sales submitted in one request."""

    sales: list[PosOfflineSale] = Field(..., min_length=1)


class PosUploadResult(APIBaseSchema):
    """Per-sale result inside an upload response."""

    sale_number: str
    sale_id: UUID | None
    status: str  # "created", "duplicate", "error"
    error: str | None = None
    # Only meaningful when status == "error". True (the safe default) means
    # the failure may be transient (a bug, a timeout, a momentary DB issue)
    # and the client should keep resubmitting this sale on future sync ticks.
    # False means the failure is a deterministic business-rule rejection
    # (bad/inconsistent data, a genuine duplicate conflict, a missing
    # reference) that will fail identically no matter how many times it is
    # retried — the client quarantines it instead of resubmitting forever.
    retryable: bool = True


class PosUploadResponse(APIBaseSchema):
    total: int
    created: int
    duplicates: int
    errors: int
    results: list[PosUploadResult] = []
