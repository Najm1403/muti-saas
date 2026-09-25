# POS SaaS — Complete Implementation Specification
### Foundational domain specification

This is the primary reference for the core Tenant/Business/Branch, catalog, Variant,
Add-on, inventory, and offline-sale model. It is not a replacement for generated API
documentation or the operational feature guides listed in
[`../DOCUMENTATION.md`](../DOCUMENTATION.md). Current schemas, migrations, and tests win
if this specification has not yet been updated in the same change.

---

## PART A — FOUNDATIONAL RULES (read before writing any code)

### A0. Core principle

**Branch on domain properties, never on business identity.**

```
BAD:  if tenant.business_template.name == "fast_food": ...
GOOD: if product.has_addons: ...
GOOD: if product.allow_inventory_tracking and variant.tracks_inventory: ...
GOOD: if template.config.pos.kitchen_display: ...
```

This does not mean collapsing distinct concepts into one table. Variant and Add-on (A1) are genuinely different and must stay as two systems. The rule is about what code branches ON, not about minimizing the number of concepts.

### A1. Product Variant vs. Variant Selection vs. Add-on

| | **Product Variant** | **Variant Selection** | **Add-on** |
|---|---|---|---|
| Defines | The product's sellable SKU, price, and stock | A shared inventory component chosen with a product | A price delta on top of the sale line |
| Created where | Add Product: default SKU or one SKU per Color | Shared Variant Options library, then attached on product detail | Shared Add-on library, then attached on product detail |
| Generates product combinations? | Colors create one row each at product creation | Never in the current UI | Never |
| Stock | Product/color Variant branch stock | Its linked component product's shared Variant stock | None |
| Examples | Plain drink; Red/Blue phone | RAM, Storage, upgrade component | Toppings, sauce, warranty add-on |

Colors are the create-time priced Variant group exposed by Add Product. Product detail
edits existing Color Variant prices while color membership remains fixed. Attached **Variant
Selections** use `usage_type="inventory_component"`: selecting one consumes its linked
component's shared stock and does not create a combination Variant for the host product.
`usage_type="specification"` is reserved for the create-time Color SKU path.

**Decision rule:** if the value is a product Color with its own price/stock, create the SKU
in Add Product. If it is a reusable stocked component, use a Variant Selection. If it only
changes price or preparation and has no stock, use an Add-on.

**Never call this system "Modifier."** Use "Add-on" / `addon_groups` / `addon_items` everywhere, in code and UI copy. The word "Variant" is already used elsewhere for the SKU-defining system — a near-synonym like "Modifier" sitting next to "Option"/"Variant" is exactly the kind of naming collision that causes an agent (or a developer) to conflate the two systems by accident.

### A2. One Tenant = exactly one Business, with multiple Branches

If a person needs two business types (a burger place and a mobile shop), they get two separate Tenant accounts. Do not build multi-business-per-tenant capability — it is explicitly out of scope. Enforce this at three levels, not just one:
- **Relationship**: `Tenant.business` is a scalar (`uselist=False`), not a list.
- **Database**: `Business.tenant_id` has a `UNIQUE` constraint.
- **Onboarding**: creates exactly one `Business` per `Tenant`, always, no branching logic that could create more.

### A3. Naming collision to avoid: `business_template_id` vs. `module_template_id`

This codebase has (or will have) **two unrelated concepts that both use the word "template":**
- `module_template_id` / `enabled_modules` — controls which **SaaS dashboard features** (Sales, HR, Reports, etc.) a tenant can access. Nothing to do with business type.
- `business_template_id` — controls the **business type** (Fast Food / Electronics) and everything that follows from it (Variant/Add-on config, inventory strictness, pricing fields, POS layout).

**Never name the second one `template_id`.** Keep both fully spelled out (`business_template_id`, `module_template_id`) everywhere — model fields, variable names, UI labels — so they are never visually or semantically confusable.

---

## PART B — COMPLETE DATA MODEL

All primary keys are UUIDs, client-generatable (required for the offline-first Flutter POS — two devices creating rows offline must never collide). Every table a POS device can create or modify offline gets `TimestampMixin` (`created_at`, `updated_at`) + `SoftDeleteMixin` (`deleted_at`) + `SyncMixin` (`sync_status` enum PENDING/SYNCED/FAILED, `synced_at`, `sync_error`). Simple join tables with no independent lifecycle use `TimestampMixin` only.

```python
# ── PLATFORM ────────────────────────────────────────────────────────────
class BusinessTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "business_templates"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)   # shape: Part C

class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tenants"
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    tenant_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    enabled_modules: Mapped[list | None] = mapped_column(JSONB, nullable=True)          # UNRELATED to business type
    module_template_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("module_templates.id", ondelete="SET NULL"), nullable=True)
    business_template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("business_templates.id", ondelete="RESTRICT"), nullable=False)  # REQUIRED — see A3
    business: Mapped["Business"] = relationship("Business", back_populates="tenant", uselist=False, cascade="all, delete-orphan")  # ONE-to-ONE, see A2
    business_template: Mapped["BusinessTemplate"] = relationship("BusinessTemplate")

class Business(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "businesses"
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)  # UNIQUE — see A2
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class Branch(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "branches"
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    __table_args__ = (UniqueConstraint("business_id", "branch_code"),)

# ── CATALOG ─────────────────────────────────────────────────────────────
class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "categories"
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "products"
    allow_inventory_tracking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    all_branches: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    preparation_station_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("preparation_stations.id", ondelete="SET NULL"), nullable=True)
    default_variant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("variants.id", ondelete="SET NULL"), nullable=True)
    # NO base_price column — see D1.

class ProductBranch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "branch_products"
    branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), primary_key=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class ProductSpec(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "product_specs"   # electronics only; unused for food, gated by template.config.product_fields.specs
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    spec_key: Mapped[str] = mapped_column(String(100), nullable=False)
    spec_value: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

# ── VARIANT SELECTION LIBRARY (shared inventory components per Business) ──
class VariantOptionGroup(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "variant_option_groups"
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)          # "RAM", "Size", "Storage"
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Selection limits live on the per-product attachment.

class VariantOption(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "variant_options"
    option_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("variant_option_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)          # "8GB", "Large"
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    component_product_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    # Component price/stock belongs to the linked product's default Variant.

class ProductVariantOptionGroup(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "product_variant_option_groups"   # makes VariantOptionGroup reusable across products
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    option_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("variant_option_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)   # per-product override
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usage_type: Mapped[str] = mapped_column(String(20), nullable=False, default="inventory_component")
    min_selections: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_selections: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    default_option_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("variant_options.id", ondelete="SET NULL"), nullable=True)
    __table_args__ = (UniqueConstraint("product_id", "option_group_id"),)

class Variant(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "variants"
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    option_value_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)   # VariantOption ids ONLY, never AddonItem ids
    combination_key: Mapped[str] = mapped_column(String(4096), nullable=False)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)          # gated by template.config.pricing
    compare_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    tracks_inventory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    __table_args__ = (
        UniqueConstraint("product_id", "combination_key", name="uq_variant_combination"),
        CheckConstraint("sale_price >= 0", name="ck_variant_sale_price_nonneg"),
    )
    # NO stock_quantity / branch_id / stock_by_branch / opening_stock — see D2.

# ── ADD-ON SYSTEM (multi-select, price delta only, NO combinatorics; shared per Business) ──
class AddonGroup(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "addon_groups"
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)          # "Toppings", "Base Ingredients"
    selection_type: Mapped[str] = mapped_column(String(10), nullable=False, default="multiple")  # 'single' | 'multiple'
    min_select: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_select: Mapped[int | None] = mapped_column(Integer, nullable=True)   # NULL = unlimited
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class AddonItem(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "addon_items"
    addon_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("addon_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)          # "Extra Cheese", "Onion"
    price_delta: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    default_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # e.g. Onion, removable
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class ProductAddonGroup(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "product_addon_groups"
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    addon_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("addon_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    __table_args__ = (UniqueConstraint("product_id", "addon_group_id"),)

# ── STOCK (StockAdjustment ledger is source of truth; VariantBranchStock is a transactionally-updated cache) ──
class StockAdjustment(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "stock_adjustments"
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("variants.id", ondelete="RESTRICT"), nullable=False, index=True)
    branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False, index=True)  # NOT NULL — always branch-scoped now
    adjustment_type: Mapped[str] = mapped_column("change_type", String(30), nullable=False)   # opening|sale|refund|manual_increase|manual_decrease|manual_set
    quantity_change: Mapped[int | None] = mapped_column("quantity_delta", Integer, nullable=True)
    resulting_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))  # client-side, keeps same-transaction ordering

class VariantBranchStock(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "variant_branch_stock"   # replaces the old JSON-blob approach entirely
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("variants.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    __table_args__ = (
        UniqueConstraint("variant_id", "branch_id", name="uq_variant_branch_stock"),
        CheckConstraint("stock_quantity >= 0", name="ck_variant_branch_stock_nonneg"),
    )

# ── SALES ───────────────────────────────────────────────────────────────
class SaleItem(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "sale_items"
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("variants.id", ondelete="RESTRICT"), nullable=False, index=True)  # NOT NULL — every sale line resolves to a variant, never product-only
    tracked_at_sale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    product_tracking_at_sale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(150), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)   # snapshot of Variant.sale_price at sale time
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    preparation_status: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    kitchen_station_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("preparation_stations.id", ondelete="SET NULL"), nullable=True, index=True)

class SaleItemOption(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "sale_item_options"   # Variant option display snapshot ONLY — no price
    sale_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sale_items.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_option_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("variant_options.id", ondelete="RESTRICT"), nullable=False, index=True)
    option_name: Mapped[str] = mapped_column(String(100), nullable=False)   # snapshot, e.g. "8GB"

class SaleItemAddon(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, SyncMixin):
    __tablename__ = "sale_item_addons"   # the Add-on equivalent of sale_item_options — priced independently
    sale_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sale_items.id", ondelete="CASCADE"), nullable=False, index=True)
    addon_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("addon_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    addon_name: Mapped[str] = mapped_column(String(100), nullable=False)          # snapshot
    price_delta_at_sale: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    was_removed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)   # a default_selected item the customer deselected
```

---

## PART C — BUSINESS TEMPLATE CONFIG (final shape, both templates)

```json
{
  "name": "Electronics Wholesale",
  "config": {
    "variants": { "enabled": true, "seed_groups": [
      { "name": "RAM", "values": ["4GB", "8GB", "16GB", "32GB"] },
      { "name": "Storage", "values": ["128GB", "256GB", "512GB", "1TB"] },
    ]},
    "addons": { "enabled": true, "seed_groups": [] },
    "inventory": { "tracking_editable": true, "tracking_default_on": true, "tracking_forced_on": false, "low_stock_threshold": 5 },
    "pricing": { "show_cost_price": true },
    "product_fields": { "sku": true, "specs": true, "warranty": true },
    "categories": { "default_categories": ["Laptops", "Mobiles", "Accessories"] }
  }
}
```
```json
{
  "name": "Fast Food",
  "config": {
    "variants": { "enabled": false, "seed_groups": [] },
    "addons": { "enabled": true, "seed_groups": [
      { "name": "Toppings", "selection_type": "multiple", "min_select": 0, "max_select": 5, "items": [
        { "name": "Extra Cheese", "price_delta": 100 }, { "name": "Mushroom", "price_delta": 80 },
        { "name": "Olives", "price_delta": 80 }, { "name": "Jalapeño", "price_delta": 80 }
      ]},
      { "name": "Base Ingredients", "selection_type": "multiple", "min_select": 0, "max_select": null, "items": [
        { "name": "Onion", "price_delta": 0, "default_selected": true }, { "name": "Tomato", "price_delta": 0, "default_selected": true }
      ]}
    ]},
    "inventory": { "tracking_editable": true, "tracking_default_on": false, "tracking_forced_on": false, "low_stock_threshold": 5 },
    "pricing": { "show_cost_price": false },
    "product_fields": { "sku": false, "specs": false, "warranty": false },
    "categories": { "default_categories": ["Burgers", "Sides", "Beverages", "Deals"] }
  }
}
```

Current dashboard attachments are inventory components and never generate host-product
combinations. Color SKUs are created atomically with the product.

---

## PART D — BACKEND SERVICE LOGIC

### D1. Product creation — every product always gets a variant

**Rule:** no product may ever be saved with zero variants. `ProductCreate.price` (not
`base_price`) seeds the default Variant. When Colors are selected,
`priced_variant_group_id` plus `priced_variants` creates one priced/stocked Variant per
Color in the same product-creation transaction.

**Product colors are create-time Variants.** In **Add Product**, a selected Color requires
its own Sale Price and opening stock. The backend attaches the Color specification group
and creates one real, independently priced and stocked Variant for each selected color.
Colors are never added or removed from product detail afterward; only the existing color
Variant prices remain editable. A product without Colors uses its default Variant.

```python
async def create_product(tenant_id, category_id, data: ProductCreate):
    product = await product_repo.create(
        category_id=category_id, product_code=data.product_code, name=data.name,
        description=data.description, image_path=data.image_path,
        display_order=data.display_order, preparation_station_id=data.preparation_station_id,
        allow_inventory_tracking=data.allow_inventory_tracking,
    )
    default_variant = await variant_service.create(
        tenant_id, product.id, option_ids=[], sale_price=data.price, tracks_inventory=False,
    )
    product.default_variant_id = default_variant.id
    await db.commit()
    return product
```

Consequence: every downstream flow (cart, sale, returns, discounts, reports) always operates on a `variant_id`. There is no `product_id`-only sale path anywhere in the system.

### D2. Stock — ledger is truth, `VariantBranchStock` is a transactionally-updated cache

```
Stock Balance = Sum of StockAdjustment rows for that (variant, branch)
```

Every stock-affecting action does BOTH in the same transaction: insert a `StockAdjustment` row, and update the `VariantBranchStock.stock_quantity` cache (for quantity-tracked) — never one without the other, and never update the cache directly without a paired ledger row.

```python
async def change_branch_balance(db, variant, branch_id, change, *, create_row_if_missing=False):
    row = await get_branch_stock_row(db, variant.id, branch_id, lock=True)
    if row is None:
        if not create_row_if_missing:
            raise ValidationError("This variant is not stocked at the selected branch.")
        row = VariantBranchStock(variant_id=variant.id, branch_id=branch_id, stock_quantity=0)
        db.add(row); await db.flush()
    new_quantity = row.stock_quantity + change
    if new_quantity < 0:
        raise ValidationError("Stock cannot become negative.")
    row.stock_quantity = new_quantity
    return new_quantity
```

Every mutation site (opening stock, sale deduction, refund restore, manual adjust, manual set) calls this, then writes a paired `StockAdjustment` row with `resulting_quantity=new_quantity`.

**Opening stock is always per-branch** — never a flat/global number. Add Product collects it
for the plain/default Variant or for every selected Color Variant. Product detail presents
the resulting totals read-only; later mutations happen in Inventory.

### D3. Quantity tracking and aggregate presentation

All tracked Variants use the branch quantity ledger/cache contract in D2.

Product detail derives its read-only **Overall Stock** view from Variant branch balances:

- plain product: total across branches plus every branch quantity;
- colored product: total across all color Variants/branches, followed by every color's
  total and per-branch quantities.

This aggregate is presentation only. Stock mutations still address one concrete Variant
and branch through `/api/v1/variants/{id}/stock...`.

### D4. Variant creation — create-time Colors

The dashboard calls this path for Add Product's selected Colors. Attaching a group with
`usage_type="inventory_component"` resolves the component's own Variant instead.

```python
async def create_variant(tenant_id, product_id, option_ids, *, sale_price, cost_price=None,
                          tracks_inventory=False, opening_stock_by_branch=None):
    product = await get_product(tenant_id, product_id)
    await enforce_tracking_policy(tenant_id, tracks_inventory)     # D6
    await enforce_pricing_policy(tenant_id, cost_price)            # D6
    if sale_price is None or sale_price < 0:
        raise ValidationError("sale_price is required and must be non-negative.")

    key = combination_key(option_ids)   # sorted, joined VariantOption ids ONLY
    if await db.scalar(select(Variant).where(Variant.product_id == product_id, Variant.combination_key == key)):
        raise ConflictError("Variant already exists for this option combination.")

    # Only Color/specification groups may define this product Variant. Inventory-component
    # attachments resolve to their own component product and are rejected here.
    links = await db.scalars(select(ProductVariantOptionGroup).where(ProductVariantOptionGroup.product_id == product_id))
    group_ids = {l.option_group_id for l in links}
    options = await db.scalars(select(VariantOption).where(VariantOption.id.in_(option_ids))) if option_ids else []
    if len(options) != len(option_ids) or any(o.option_group_id not in group_ids for o in options):
        raise ValidationError("Variant option values must belong to this product.")
    for link in links:
        count = sum(o.option_group_id == link.option_group_id for o in options)
        if count > 1:
            raise ValidationError("Only one value may be selected per Variant Option Group.")   # structurally can't be multi-select
        if link.is_required and count != 1:
            raise ValidationError("A required Variant Option Group must have exactly one value selected.")

    variant = Variant(product_id=product_id, option_value_ids=[str(i) for i in option_ids],
        combination_key=key, sale_price=sale_price, cost_price=cost_price,
        tracks_inventory=tracks_inventory, is_default=(len(option_ids) == 0))
    db.add(variant); await db.flush()

    if tracks_inventory and opening_stock_by_branch:
        validated = await validate_branch_opening(tenant_id, product_id, opening_stock_by_branch)
        for branch_id_str, amount in validated.items():
            db.add(VariantBranchStock(variant_id=variant.id, branch_id=UUID(branch_id_str), stock_quantity=amount))
            await db.flush()
            db.add(StockAdjustment(variant_id=variant.id, branch_id=UUID(branch_id_str), adjustment_type="opening",
                quantity_change=amount, resulting_quantity=amount, note="Opening stock"))
    return variant
```

**Add-on selections never reach this function at all.** There is no parameter here for them — Toppings are attached to a product via a completely separate call (`attach_addon_group(product_id, addon_group_id)`), and selected at POS time independently of which variant was picked. This is what makes the conflation structurally impossible rather than just discouraged by convention.

### D5. Onboarding — seeding a new tenant from its template

```python
async def onboard(data: OnboardingCreate):
    template = await db.scalar(select(BusinessTemplate).where(BusinessTemplate.id == data.business_template_id))
    if not template:
        raise NotFoundError("Business template not found.")
    tenant = Tenant(name=data.name, tenant_code=data.tenant_code, business_template_id=template.id)
    db.add(tenant); await db.flush()
    # ... owner user + admin role, standard onboarding logic ...
    business = Business(tenant_id=tenant.id, name=data.name)
    db.add(business); await db.flush()
    branch = Branch(business_id=business.id, branch_code=data.branch_code, name=data.branch_name)
    db.add(branch); await db.flush()

    config = template.config or {}
    for cat_name in config.get("categories", {}).get("default_categories", []):
        db.add(Category(business_id=business.id, name=cat_name))
    await db.flush()

    for group_def in config.get("variants", {}).get("seed_groups", []):
        group = VariantOptionGroup(business_id=business.id, name=group_def["name"])
        db.add(group); await db.flush()
        for value in group_def.get("values", []):
            db.add(VariantOption(option_group_id=group.id, name=value))
    await db.flush()

    for addon_def in config.get("addons", {}).get("seed_groups", []):
        group = AddonGroup(business_id=business.id, name=addon_def["name"],
            selection_type=addon_def.get("selection_type", "multiple"),
            min_select=addon_def.get("min_select", 0), max_select=addon_def.get("max_select"))
        db.add(group); await db.flush()
        for item_def in addon_def.get("items", []):
            db.add(AddonItem(addon_group_id=group.id, name=item_def["name"],
                price_delta=item_def.get("price_delta", 0), default_selected=item_def.get("default_selected", False)))
    await db.flush()

    await db.commit()
```

### D6. Business-template policy enforcement — server-side, not just UI

A disabled checkbox in the form is not a real rule on its own — it must also be rejected by the API.

```python
async def load_business_policy(tenant_id) -> dict:
    tenant = await db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    template = await db.scalar(select(BusinessTemplate).where(BusinessTemplate.id == tenant.business_template_id))
    return (template.config if template else {}) or {}

async def enforce_tracking_policy(tenant_id, tracks_inventory: bool):
    policy = await load_business_policy(tenant_id)
    if policy.get("inventory", {}).get("tracking_forced_on") and not tracks_inventory:
        raise ValidationError("This business type requires inventory tracking on every variant.")

async def enforce_pricing_policy(tenant_id, cost_price):
    # Cost Price is an optional accounting field for every business type.
    # Cost Price is optional.
    return None
```

Call both in variant create/update.

### D7. POS checkout — Add-on pricing is re-verified server-side, never trusted from the client

```python
async def resolve_addon_price_deltas(db, item_data) -> dict:
    # Never trust client-submitted price_delta — always re-fetch from AddonItem.
    # A tampered client payload could otherwise submit price_delta: 0 for a paid topping.
    addon_ids = [a.addon_item_id for a in item_data.addons]
    if not addon_ids:
        return {}
    rows = await db.scalars(select(AddonItem).where(AddonItem.id.in_(addon_ids)))
    found = {row.id: row.price_delta for row in rows}
    missing = set(addon_ids) - found.keys()
    if missing:
        raise ValidationError(f"Unknown add-on item(s): {missing}")
    return found

async def validate_totals(db, sale_data):
    computed_subtotal = Decimal("0.00")
    for item in sale_data.items:
        true_deltas = await resolve_addon_price_deltas(db, item)
        addon_total = sum(Decimal("0.00") if a.was_removed else true_deltas[a.addon_item_id] for a in item.addons)
        expected = ((item.unit_price + addon_total) * item.quantity) - item.discount
        if abs(item.total - expected) > Decimal("0.01"):
            raise ValidationError(f"Item '{item.product_name}' total mismatch.")
        computed_subtotal += item.total
    if abs(sale_data.subtotal - computed_subtotal) > Decimal("0.01"):
        raise ValidationError("Sale subtotal mismatch.")
```

At sale persistence, for each item: create one `SaleItem` (with `variant_id`, `unit_price` = the variant's `sale_price` snapshot), one `SaleItemOption` per selected Variant Option (display-only, no price), and one `SaleItemAddon` per selected/removed Add-on (with the server-verified `price_delta_at_sale`).

Stock deduction, per line:
```python
async def deduct_line(db, variant, branch_id, quantity, sale_id):
    if variant.tracks_inventory:
        new_balance = await change_branch_balance(db, variant, branch_id, -quantity)
        db.add(StockAdjustment(variant_id=variant.id, branch_id=branch_id, adjustment_type="sale",
            quantity_change=-quantity, resulting_quantity=new_balance, reference_id=str(sale_id)))
    # untracked (e.g. unlimited pizza) — no-op, always sellable
```

**Idempotency/offline-retry check must compare `variant_id` and the full addons list, not just product/price/options** — two submissions differing only in which variant was sold at an equal price must never be treated as the same retry.

---

## PART E — API SCHEMAS (Pydantic field lists)

```python
class ProductCreate(BaseModel):
    product_code: str
    name: str
    description: str | None = None
    image_path: str | None = None
    price: Decimal                      # seeds the default variant's sale_price — NOT base_price
    display_order: int = 0
    preparation_station_id: UUID | None = None
    allow_inventory_tracking: bool = False
    opening_stock_by_branch: dict[UUID, int] | None = None
    priced_variant_group_id: UUID | None = None       # create-time Colors group
    priced_variants: list[PricedVariantInput] | None = None

class VariantCreate(BaseModel):
    option_ids: list[UUID] = []
    sale_price: Decimal
    cost_price: Decimal | None = None
    tracks_inventory: bool = False
    opening_stock_by_branch: dict[str, int] | None = None   # {branch_id: quantity}

class AddonGroupCreate(BaseModel):
    name: str
    selection_type: Literal["single", "multiple"] = "multiple"
    min_select: int = 0
    max_select: int | None = None

class AddonItemCreate(BaseModel):
    addon_group_id: UUID
    name: str
    price_delta: Decimal = Decimal("0.00")
    default_selected: bool = False

class PosSaleVariantOptionSnapshot(BaseModel):
    variant_option_id: UUID
    option_name: str

class PosSaleAddonSelection(BaseModel):
    addon_item_id: UUID
    addon_name: str
    price_delta: Decimal          # client-submitted; server RE-VERIFIES against AddonItem, see D7
    was_removed: bool = False

class PosSaleItemCreate(BaseModel):
    id: UUID | None = None
    product_id: UUID
    variant_id: UUID
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal = Decimal("0.00")
    total: Decimal
    options: list[PosSaleVariantOptionSnapshot] = []
    addons: list[PosSaleAddonSelection] = []

class OnboardingCreate(BaseModel):
    name: str
    tenant_code: str
    business_template_id: UUID        # REQUIRED — see A3 for the naming rule
    owner_username: str
    owner_name: str
    owner_email: str | None = None
    branch_code: str
    branch_name: str
    plan_id: UUID | None = None
    trial_days: int = 0
    billing_cycle: str = "MONTHLY"
```

---

## PART F — FLUTTER / POS IMPLEMENTATION

### F1. POS UI state — keep SKU, component, and Add-on choices separate

```dart
class PosState {
  final String? selectedCategoryId;
  final String? selectedProductId;
  final Map<String, String> selectedVariantOptions;   // specification/color SKU resolution
  final Map<String, String> selectedComponents;       // groupId -> shared component optionId
  final Map<String, Set<String>> selectedAddons;       // addonGroupId -> Set of addonItemIds (multi-select)
  final int quantity;
  // ...
}
```

Use distinct methods and state for each concept:
- `selectVariantOption(groupId, optionId)` resolves a product-owned SKU (including a Color).
- `selectComponent(groupId, optionId)` selects a linked component Variant whose price and
  stock remain independent of the host product.
- `toggleAddon(groupId, addonItemId, {maxSelections})` — checkbox behavior: adds/removes from the set, respecting `maxSelections` if given.

**Never let one method serve both roles via a `multiSelect: bool` flag.** That flag was exactly how the backend bug's UI-side twin happened — one data structure standing in for two different concepts.

### F2. Cart item shape

```dart
class CartItem {
  final String id;
  final String productId;
  final String variantId;                    // REQUIRED — every cart item resolves to a variant
  final String productName;
  final Decimal unitPrice;                   // = Variant.sale_price at add-to-cart time
  final Decimal quantity;
  final Decimal discount;
  final List<CartVariantOption> variantOptions;   // display only, NO price
  final List<CartAddon> addons;                   // priced, may include was_removed entries
}

class CartVariantOption {
  final String variantOptionId;
  final String optionName;
}

class CartAddon {
  final String addonItemId;
  final String addonName;
  final Decimal priceDelta;
  final bool wasRemoved;
}
```

Line total = `unitPrice * quantity + Sum(addon.priceDelta for addons where !wasRemoved) * quantity - discount`.

### F3. Add-to-cart flow — resolves to a variant always, picker is conditional

```dart
void addToCart(Product product) {
  final needsPicker = product.variants.length > 1 || product.addonGroups.isNotEmpty;
  if (needsPicker) {
    openCustomizationModal(product);   // one modal, two OPTIONAL sections (F4)
  } else {
    addLineItem(product.defaultVariantId, quantity: 1);   // still a variant_id, just resolved silently
  }
}
```

### F4. Customization modal — visually separate SKU, component, and Add-on sections

```
Customize: Laptop
-----------------------------
Color (SKU - choose one)
  o Black  * Silver

RAM (Variant Selection - shared component)
  o 8GB  * 16GB

Extras (Add-on)
  [x] Extended Warranty
```

On "Add to Cart", resolve the product/color SKU to a real Variant. Add each selected
inventory component as a linked component cart line using its own Variant and stock pool.
Translate Add-ons into `CartAddon` entries. Never synthesize a new host-product combination
from Variant Selections.

### F5. Local (offline) data — Drift tables needed

Add local tables mirroring: `variants`, `variant_branch_stock`, `variant_option_groups`,
`variant_options`, `addon_groups`, and `addon_items`. Sync is full-replace in this codebase.

### F6. Draft order persistence — matches the CartItem shape in F2

When serializing a parked draft to JSON (and back), persist `variantId`, `variantOptions` (id + name only), and `addons` (id, name, priceDelta, wasRemoved) per cart item — never a merged/flattened structure that loses the Variant/Add-on distinction.

---

## PART G — UI SCREENS

### G1. Platform Dashboard (new)

- **Business Templates**: list/create/edit screen for `BusinessTemplate` rows — name + a JSON config editor (validate against Part C's shape server-side before save).
- **Create Tenant** form: add a required **Business Template** dropdown. On submit, calls the onboarding endpoint (D5), which handles all seeding server-side — the form itself does nothing beyond collecting the selection.

### G2. Tenant Dashboard — Add Product form

- No `base_price` field. A plain product has one **Sale Price** and opening stock. When
  Colors are selected, each color row requires its own Sale Price and opening stock and is
  saved as a real Variant.
- Branch availability: unchanged pattern (`all_branches` checkbox + branch multi-select).
- Fields gated by `template.config.product_fields`: `sku`, `specs` (repeatable key-value), `warranty` — shown/hidden per template, not per hardcoded business-type check.

### G3. Tenant Dashboard — Product detail page

- Color membership remains as configured in Add Product; existing color Variant Sale Prices
  remain editable.
- **Variant Selections** attach shared inventory-component groups. They do not generate a
  product combination table and do not replace the product's own stock.
- **New, visually separate "Add-ons" section on the same page**: "Attach Add-on Group" opens a picker over the Business's shared Add-on library (or create new). Lists each group's items with price deltas. This section never talks to the variant-generation logic at all.
- **New sidebar screens**: "Variant Options" (library) and "Add-on Groups" (library) — both business-wide, both seeded at onboarding, both editable afterward.
- **Overall Stock**: read-only all-branch total. Colored products also show every color's
  total and per-branch quantities; plain products show their default Variant by branch.

### G4. POS (Flutter) — see Part F for the exact state/flow logic.

---

## PART H — BUILD ORDER

1. Create every model in Part B.
2. Implement the service logic in Part D (product/color creation, quantity stock ledger, variant creation validation, onboarding seeding, policy enforcement, checkout).
3. Implement the schemas in Part E.
4. Build the Platform Dashboard screens (G1) and wire onboarding to seed correctly (D5).
5. Build the Tenant Dashboard changes (G2, G3).
6. Implement the Flutter state split (F1), cart shape (F2), add-to-cart flow (F3), customization modal (F4).
7. Add local Drift tables and extend the sync payload (F5); update draft persistence (F6).
8. Drop/recreate the dev database, generate one fresh initial Alembic migration. Resume normal incremental migrations from this point on for all future changes.

---

## PART I — TEST MATRIX

- A no-variant product (e.g. a canned drink) sells via its silently-resolved default variant and deducts stock correctly.
- A shared Variant Selection (RAM) created once is selectable on a second product without
  recreating it and consumes the same linked component stock pool.
- A colored product has exactly one sellable Variant per selected Color; attaching RAM,
  Storage, or Add-ons creates no additional host-product combination rows.
- Unchecking a `default_selected` Add-on Item ("Onion") results in `was_removed: true` on the sale record and prints "No Onion" on the kitchen ticket.
- An untracked variant (`tracks_inventory=false`, e.g. unlimited pizza) sells past zero stock with no block.
- A tracked quantity variant blocks correctly at zero stock.
- Electronics: `tracks_inventory` cannot be set to `false` via the API even if the UI is bypassed (D6 enforced server-side).
- Creating/updating a menu product or variant without `cost_price` succeeds; Cost Price is always optional.
- Colored product stock equals the sum of its color Variants, while each color and branch
  remains independently auditable and mutable.
- Attempting to pass an `AddonItem` id into a Variant's `option_ids` at creation fails validation (D4) — confirm no code path accepts it.
- Two offline devices each creating a sale get non-colliding UUIDs and sync cleanly.
- An idempotent offline retry (same `sale_number`, same device) is correctly recognized even when two lines differ only by which `variant_id` was sold at an equal price — must NOT be falsely deduplicated.

---

## PART J — GUARDRAILS (final)

- Branch on domain properties, never on business/template identity (A0).
- Variant and Add-on are permanently separate systems — a multi-select group must never be able to reach `combination_key` (A1, D4).
- Never call the Add-on system "Modifier" anywhere, in code or UI (A1).
- One Tenant, one Business — enforced by relationship cardinality AND a DB `UNIQUE` constraint, not convention alone (A2).
- `business_template_id` and `module_template_id` are unrelated concepts — keep both names fully spelled out everywhere (A3).
- Never mutate `VariantBranchStock.stock_quantity` directly — always through the paired ledger-and-cache update (D2).
- Inventory mutations always use the quantity ledger/cache contract in D3.
- Never trust a client-submitted Add-on price — always re-verify against `AddonItem.price_delta` server-side (D7).
- Use the supported Business Template feature flags and policies in Part C.
- Every sale line resolves to a `variant_id` — there is no product-only sale path anywhere (D1).
- Enforce business-template policy (tracking, pricing) server-side — a disabled or hidden form field is not a real rule on its own (D6).
