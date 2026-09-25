"""Tests for the Laptop Store shareable-component-inventory model:
1. Stock is always keyed by variant_id, never variant_option_id — shared
   library reuse (VariantOptionGroup/VariantOption) must never cause two
   'fixed'-usage products' stock to be shared or summed, EXCEPT for an
   'inventory_component'-usage group, where sharing the same real
   component Product's stock is intentional and automatic (no per-product
   linking step required).
2. usage_type ('specification' | 'inventory_component') is per (product,
   group), not per whole product — a product can mix both (hybrid/
   partially-upgradable machines).
3. Branch-to-branch stock transfer, identical for a plain product's own
   stock and a shared component's stock.
"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from core.exceptions import ConflictError, ValidationError
from models.branch import Branch
from models.product import Product
from models.product_variant_option_group import ProductVariantOptionGroup
from models.stock_adjustment import StockAdjustment
from models.variant_option import VariantOption
from models.variant_option_group import VariantOptionGroup
from schemas.variant_option import VariantOptionComponentSet
from schemas.variant_option_group import ProductVariantOptionAllowedSet, ProductVariantOptionGroupAttach
from services.variant_option_group_service import VariantOptionGroupService
from services.variant_option_service import VariantOptionService
from services.product_service import ProductService
from services.variant_service import VariantService


async def _fresh_option(db, H, group_id, name="Fresh"):
    opt = VariantOption(id=uuid4(), option_group_id=group_id, name=name + uuid4().hex[:6],
                         display_order=0, is_active=True)
    db.add(opt)
    await db.flush()
    return opt


# ══════════════════════════════════════════════════════════════
# Check 1 — two 'specification'-usage products sharing the same "8GB"
# VariantOption have completely independent stock.
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_two_fixed_products_sharing_an_option_have_independent_stock(db, H):
    # A second product under the same business, reusing H's existing shared
    # og_a/opt_a group+option ("Size"/"Large") — the exact same rows prod_a
    # already uses for its own variant_a.
    product_c = Product(
        id=uuid4(), category_id=H["cat_a"].id, product_code="LAPTOP-C", name="Second Laptop",
        display_order=0, is_active=True, allow_inventory_tracking=True,
    )
    db.add(product_c)
    await db.flush()
    from models.product_variant_option_group import ProductVariantOptionGroup
    db.add(ProductVariantOptionGroup(
        product_id=product_c.id, option_group_id=H["og_a"].id, is_required=True, display_order=0,
        usage_type="specification"))
    await db.flush()

    svc = VariantService(db, created_by=H["user_a"].id)
    variant_c = await svc.create(
        H["tenant_a"].id, product_c.id, [H["opt_a"].id], sale_price=Decimal("999.00"),
        tracks_inventory=True, opening_stock_by_branch={str(H["branch_a"].id): 20},
    )

    # H's own variant_a (prod_a) also gets tracked stock for this same option.
    H["prod_a"].allow_inventory_tracking = True
    await db.flush()
    H["variant_a"].tracks_inventory = True
    await db.flush()
    await svc.change_branch_balance(H["variant_a"].id, H["branch_a"].id, 7, create_row_if_missing=True)

    assert variant_c.option_value_ids == H["variant_a"].option_value_ids  # same "8GB"-equivalent option
    assert variant_c.id != H["variant_a"].id  # but a completely separate Variant row

    row_a = await svc.get_branch_stock_row(H["variant_a"].id, H["branch_a"].id)
    row_c = await svc.get_branch_stock_row(variant_c.id, H["branch_a"].id)
    assert row_a.stock_quantity == 7
    assert row_c.stock_quantity == 20

    # Selling one never touches the other.
    await svc.deduct(H["tenant_a"].id, [(H["variant_a"].id, 3)], sale_id=uuid4(), branch_id=H["branch_a"].id)
    row_a = await svc.get_branch_stock_row(H["variant_a"].id, H["branch_a"].id)
    row_c = await svc.get_branch_stock_row(variant_c.id, H["branch_a"].id)
    assert row_a.stock_quantity == 4
    assert row_c.stock_quantity == 20  # untouched


# ══════════════════════════════════════════════════════════════
# Shareable inventory components — set once in the library, shared by every
# product that attaches the group as 'inventory_component'. No per-product
# linking step.
# ══════════════════════════════════════════════════════════════

async def _build_ram_component(db, H, *, name="16GB"):
    """Returns (group, option, component_product, component_variant)."""
    og = VariantOptionGroup(id=uuid4(), business_id=H["biz_a"].id, name=f"RAM {uuid4().hex[:6]}", is_active=True)
    db.add(og)
    await db.flush()
    ram_option = await _fresh_option(db, H, og.id, name)

    resp = await VariantOptionService(db).set_inventory_component(
        ram_option.id, H["tenant_a"].id,
        VariantOptionComponentSet(sale_price=Decimal("9000.00"), cost_price=Decimal("6000.00"),
                                   opening_stock_by_branch={H["branch_a"].id: 10}),
    )
    assert resp.component_product_id is not None
    ram_product = await db.scalar(select(Product).where(Product.id == resp.component_product_id))
    ram_variant = await VariantService(db).get(H["tenant_a"].id, ram_product.default_variant_id)
    return og, ram_option, ram_product, ram_variant


async def _attach_as_component(db, H, product_id, group_id, *, required=False):
    return await VariantOptionGroupService(db).attach_to_product(
        product_id, H["tenant_a"].id,
        ProductVariantOptionGroupAttach(option_group_id=group_id, is_required=required,
                                         usage_type="inventory_component"),
    )


async def _build_chassis(db, H):
    chassis = Product(
        id=uuid4(), category_id=H["cat_a"].id, product_code=f"LAPTOP-{uuid4().hex[:6]}", name="Configurable Laptop",
        display_order=0, is_active=True,
    )
    db.add(chassis)
    await db.flush()
    default_variant = await VariantService(db, created_by=H["user_a"].id).create(
        H["tenant_a"].id, chassis.id, [], sale_price=Decimal("50000.00"))
    chassis.default_variant_id = default_variant.id
    await db.flush()
    return chassis, default_variant


@pytest.mark.asyncio
async def test_set_inventory_component_creates_shared_product_and_is_idempotent(db, H):
    og, ram_option, ram_product, ram_variant = await _build_ram_component(db, H)
    assert ram_product.name == ram_option.name
    assert ram_variant.sale_price == Decimal("9000.00")
    product_response = await ProductService(db).get(ram_product.id, H["tenant_a"].id)
    assert product_response.is_inventory_component is True
    assert product_response.component_option_id == ram_option.id
    assert product_response.component_option_name == ram_option.name
    assert product_response.component_group_name == og.name
    row = await VariantService(db).get_branch_stock_row(ram_variant.id, H["branch_a"].id)
    assert row.stock_quantity == 10

    # Calling it again is a no-op — never creates a second component product.
    resp2 = await VariantOptionService(db).set_inventory_component(
        ram_option.id, H["tenant_a"].id,
        VariantOptionComponentSet(sale_price=Decimal("1.00")),
    )
    assert resp2.component_product_id == ram_product.id
    still_variant = await VariantService(db).get(H["tenant_a"].id, ram_product.default_variant_id)
    assert still_variant.sale_price == Decimal("9000.00")  # unchanged by the no-op call


@pytest.mark.asyncio
async def test_component_product_cannot_become_recursively_configurable(db, H):
    og, ram_option, ram_product, _ = await _build_ram_component(db, H)
    other_group = VariantOptionGroup(
        id=uuid4(), business_id=H["biz_a"].id, name="Storage", is_active=True
    )
    db.add(other_group)
    await db.flush()

    with pytest.raises(ValidationError, match="Inventory components cannot have Variant Selections"):
        await _attach_as_component(db, H, ram_product.id, other_group.id)

    with pytest.raises(ConflictError, match="stock record for a shared Variant Option"):
        await ProductService(db).delete(ram_product.id, H["tenant_a"].id)


@pytest.mark.asyncio
async def test_pos_and_checkout_ignore_legacy_recursive_component_attachment(db, H):
    og, ram_option, ram_product, ram_variant = await _build_ram_component(db, H)
    legacy_group = VariantOptionGroup(
        id=uuid4(), business_id=H["biz_a"].id, name="Legacy recursive group", is_active=True
    )
    db.add(legacy_group)
    await db.flush()
    # Simulates data made before the recursive-attachment guard existed.
    db.add(ProductVariantOptionGroup(
        product_id=ram_product.id,
        option_group_id=legacy_group.id,
        usage_type="inventory_component",
        is_required=True,
    ))
    await db.flush()

    from services.pos_sync_service import PosSyncService
    products = await PosSyncService(db)._products(H["biz_a"].id, H["branch_a"].id, None)
    synced_component = next(p for p in products if p.id == ram_product.id)
    assert synced_component.variant_option_groups == []
    assert await VariantOptionGroupService(db).list_for_product(
        ram_product.id, H["tenant_a"].id
    ) == []

    # The same component remains directly sellable without being forced to
    # choose a child value from the stale recursive attachment.
    from schemas.pos_sale import PosSaleItemCreate
    receipt = await _full_checkout_submit(db, H, [PosSaleItemCreate(
        variant_id=ram_variant.id,
        product_id=ram_product.id,
        product_name=ram_product.name,
        quantity=1,
        unit_price=ram_variant.sale_price,
        total=ram_variant.sale_price,
    )])
    assert len(receipt.items) == 1


@pytest.mark.asyncio
async def test_unset_inventory_component_blocked_with_stock_or_sales(db, H):
    og, ram_option, ram_product, ram_variant = await _build_ram_component(db, H)

    with pytest.raises(ConflictError, match="still has stock"):
        await VariantOptionService(db).unset_inventory_component(ram_option.id, H["tenant_a"].id)

    svc = VariantService(db)
    await svc.change_branch_balance(ram_variant.id, H["branch_a"].id, -10)
    resp = await VariantOptionService(db).unset_inventory_component(ram_option.id, H["tenant_a"].id)
    assert resp.component_product_id is None
    # The backing product itself is untouched — still real, still sellable.
    still_there = await db.scalar(select(Product).where(Product.id == ram_product.id, Product.deleted_at.is_(None)))
    assert still_there is not None


@pytest.mark.asyncio
async def test_two_products_attaching_the_same_component_group_share_one_stock_pool(db, H):
    """The exact scenario spec section 10 describes: 16GB DDR4 offered on
    Laptop A and Laptop B must draw from ONE shared branch stock balance —
    with zero per-product linking action beyond attaching the same group."""
    og, ram_option, ram_product, ram_variant = await _build_ram_component(db, H)
    chassis_a, _ = await _build_chassis(db, H)
    chassis_b, _ = await _build_chassis(db, H)
    await _attach_as_component(db, H, chassis_a.id, og.id)
    await _attach_as_component(db, H, chassis_b.id, og.id)

    svc = VariantService(db)
    # "Sold assembled into chassis A."
    await svc.deduct(H["tenant_a"].id, [(ram_variant.id, 1)], sale_id=uuid4(), branch_id=H["branch_a"].id)
    assert (await svc.get_branch_stock_row(ram_variant.id, H["branch_a"].id)).stock_quantity == 9

    # "Sold assembled into chassis B" — same variant_id, same pool.
    await svc.deduct(H["tenant_a"].id, [(ram_variant.id, 1)], sale_id=uuid4(), branch_id=H["branch_a"].id)
    assert (await svc.get_branch_stock_row(ram_variant.id, H["branch_a"].id)).stock_quantity == 8

    # "Sold loose, standalone" — mechanically identical call.
    await svc.deduct(H["tenant_a"].id, [(ram_variant.id, 1)], sale_id=uuid4(), branch_id=H["branch_a"].id)
    assert (await svc.get_branch_stock_row(ram_variant.id, H["branch_a"].id)).stock_quantity == 7


@pytest.mark.asyncio
async def test_inventory_component_group_never_generates_a_combination_variant(db, H):
    og, ram_option, ram_product, ram_variant = await _build_ram_component(db, H)
    chassis, chassis_default = await _build_chassis(db, H)
    await _attach_as_component(db, H, chassis.id, og.id)

    with pytest.raises(ValidationError, match="never has combination variants"):
        await VariantService(db, created_by=H["user_a"].id).create(
            H["tenant_a"].id, chassis.id, [ram_option.id], sale_price=Decimal("60000.00"))

    from models.variant import Variant
    variants = (await db.scalars(select(Variant).where(Variant.product_id == chassis.id))).all()
    assert len(variants) == 1
    assert variants[0].is_default is True


@pytest.mark.asyncio
async def test_required_component_group_does_not_block_its_own_products_sale(db, H):
    """Regression: marking the component group required=True (the natural
    setup — "every laptop must have RAM selected") must never reject a sale
    of the chassis's own base line, because a chassis's own Variant can
    never carry option_value_ids for an inventory_component group by
    construction (see create())."""
    og, ram_option, ram_product, ram_variant = await _build_ram_component(db, H)
    chassis, chassis_default = await _build_chassis(db, H)
    await _attach_as_component(db, H, chassis.id, og.id, required=True)

    svc = VariantService(db, created_by=H["user_a"].id)
    chassis_variant = await svc.get(H["tenant_a"].id, chassis.default_variant_id)

    # Must not raise — this is exactly what was broken before usage_type existed.
    await svc._check_required_groups(chassis.id, chassis_variant)


@pytest.mark.asyncio
async def test_hybrid_product_only_combinates_its_specification_groups(db, H):
    """spec sections 17/18: a product can mix a 'specification' group (e.g.
    CPU, soldered) and an 'inventory_component' group (e.g. SSD, removable)
    at the same time — only the specification dimension ever appears in a
    combination Variant's option_value_ids."""
    cpu_group = VariantOptionGroup(id=uuid4(), business_id=H["biz_a"].id, name=f"CPU {uuid4().hex[:6]}", is_active=True)
    db.add(cpu_group)
    await db.flush()
    cpu_option = await _fresh_option(db, H, cpu_group.id, "Corei7")

    ssd_group, ssd_option, ssd_product, ssd_variant = await _build_ram_component(db, H, name="512GBSSD")

    chassis, chassis_default = await _build_chassis(db, H)
    await VariantOptionGroupService(db).attach_to_product(
        chassis.id, H["tenant_a"].id,
        ProductVariantOptionGroupAttach(option_group_id=cpu_group.id, is_required=True, usage_type="specification"))
    await _attach_as_component(db, H, chassis.id, ssd_group.id, required=True)

    # Selecting only the CPU (specification) value succeeds and generates a
    # real combination Variant scoped to just that dimension.
    combo = await VariantService(db, created_by=H["user_a"].id).create(
        H["tenant_a"].id, chassis.id, [cpu_option.id], sale_price=Decimal("70000.00"))
    assert combo.option_value_ids == [str(cpu_option.id)]

    # Trying to also fold the SSD (inventory_component) value into a
    # combination is rejected — it's chosen at sale time, not baked in.
    with pytest.raises(ValidationError, match="never has combination variants"):
        await VariantService(db, created_by=H["user_a"].id).create(
            H["tenant_a"].id, chassis.id, [cpu_option.id, ssd_option.id], sale_price=Decimal("85000.00"))


@pytest.mark.asyncio
async def test_allowed_options_restricts_a_groups_shared_values_per_product(db, H):
    """spec section 22 — compatibility is product-specific: a business-wide
    RAM group might offer more values than one particular laptop supports."""
    og = VariantOptionGroup(id=uuid4(), business_id=H["biz_a"].id, name=f"RAM {uuid4().hex[:6]}", is_active=True)
    db.add(og)
    await db.flush()
    ddr4 = await _fresh_option(db, H, og.id, "DDR4")
    ddr5 = await _fresh_option(db, H, og.id, "DDR5")

    chassis, _ = await _build_chassis(db, H)
    link_svc = VariantOptionGroupService(db)
    link = await link_svc.attach_to_product(
        chassis.id, H["tenant_a"].id,
        ProductVariantOptionGroupAttach(option_group_id=og.id, is_required=False, usage_type="specification"))
    # No rows yet — every option in the group is allowed (today's behavior).
    assert link.allowed_option_ids == []

    restricted = await link_svc.set_allowed_options(
        chassis.id, H["tenant_a"].id, link.id, ProductVariantOptionAllowedSet(variant_option_ids=[ddr4.id]))
    assert restricted.allowed_option_ids == [ddr4.id]

    listed = await link_svc.list_for_product(chassis.id, H["tenant_a"].id)
    assert listed[0].allowed_option_ids == [ddr4.id]

    # An option from a different group can never be allow-listed here.
    other_og = VariantOptionGroup(id=uuid4(), business_id=H["biz_a"].id, name="Other", is_active=True)
    db.add(other_og)
    await db.flush()
    foreign_option = await _fresh_option(db, H, other_og.id, "Foreign")
    with pytest.raises(ValidationError, match="must belong to this group"):
        await link_svc.set_allowed_options(
            chassis.id, H["tenant_a"].id, link.id,
            ProductVariantOptionAllowedSet(variant_option_ids=[foreign_option.id]))


@pytest.mark.asyncio
async def test_upgradable_sale_validates_and_deducts_every_item(db, H):
    """A full sale of an upgradable chassis + its shared RAM component as two
    separate SaleItems (checkout wiring is a later phase — this proves the
    underlying validate/deduct machinery both lines would run through):
    both pass validate_variant_selection(), both pass validate_stock(), and
    deduct() correctly decreases each one's own stock — the chassis is
    untracked (no stock to check), the RAM's real stock decreases by
    exactly the quantity sold."""
    from schemas.pos_sale import PosSaleItemCreate

    og, ram_option, ram_product, ram_variant = await _build_ram_component(db, H)
    chassis, chassis_default = await _build_chassis(db, H)
    await _attach_as_component(db, H, chassis.id, og.id, required=True)

    svc = VariantService(db, created_by=H["user_a"].id)
    chassis_variant = await svc.get(H["tenant_a"].id, chassis.default_variant_id)

    items = [
        PosSaleItemCreate(
            variant_id=chassis_variant.id, product_id=chassis.id, product_name=chassis.name,
            quantity=1, unit_price=chassis_variant.sale_price, total=chassis_variant.sale_price,
            options=[],
        ),
        PosSaleItemCreate(
            variant_id=ram_variant.id, product_id=ram_product.id, product_name=ram_product.name,
            quantity=1, unit_price=ram_variant.sale_price, total=ram_variant.sale_price,
            options=[],
        ),
    ]

    # Both items must validate — this is the exact bug this pattern used to hit.
    await svc.validate_variant_selection(H["tenant_a"].id, items)
    await svc.validate_stock(
        H["tenant_a"].id, [(i.variant_id, int(i.quantity)) for i in items], branch_id=H["branch_a"].id)

    before = (await svc.get_branch_stock_row(ram_variant.id, H["branch_a"].id)).stock_quantity
    sale_id = uuid4()
    await svc.deduct(H["tenant_a"].id,
        [(i.variant_id, int(i.quantity), i.id) for i in items],
        sale_id, branch_id=H["branch_a"].id)
    after = (await svc.get_branch_stock_row(ram_variant.id, H["branch_a"].id)).stock_quantity
    assert after == before - 1  # the RAM leg was tracked and deducted

    # Both legs recorded as one sale's stock movement (RAM only — the
    # chassis is untracked, so it correctly produces no StockAdjustment).
    adjustments = (await db.scalars(select(StockAdjustment).where(
        StockAdjustment.reference_id == str(sale_id)))).all()
    assert len(adjustments) == 1
    assert adjustments[0].variant_id == ram_variant.id


# ══════════════════════════════════════════════════════════════
# Full checkout wiring — a selected inventory component travels through
# PosSaleService.create() as its own ordinary PosSaleItemCreate, tagged
# back to its parent via parent_item_id/satisfies_option_group_id/
# component_option_id (never a nested child schema — see
# services/pos_sale_service.py's _validate_component_selections()).
# ══════════════════════════════════════════════════════════════

async def _full_checkout_submit(db, H, items, *, total=None):
    from schemas.pos_sale import PosSaleCreate, PosSalePaymentCreate
    from services.pos_sale_service import PosSaleService
    subtotal = sum(i.total for i in items)
    grand_total = total if total is not None else subtotal
    data = PosSaleCreate(
        sale_number="LAPTOP-" + uuid4().hex[:10],
        sold_at=datetime.now(timezone.utc),
        subtotal=subtotal, total=grand_total,
        items=items,
        payments=[PosSalePaymentCreate(payment_method="Cash", amount=grand_total)],
    )
    return await PosSaleService(db).create(
        data, H["branch_a"].id, H["device_a"].id, H["user_a"].id, H["tenant_a"].id)


@pytest.mark.asyncio
async def test_checkout_blocks_required_component_group_when_unfulfilled(db, H):
    og, ram_option, ram_product, ram_variant = await _build_ram_component(db, H)
    chassis, chassis_default = await _build_chassis(db, H)
    await _attach_as_component(db, H, chassis.id, og.id, required=True)

    from schemas.pos_sale import PosSaleItemCreate
    items = [PosSaleItemCreate(
        variant_id=chassis_default.id, product_id=chassis.id, product_name=chassis.name,
        quantity=1, unit_price=chassis_default.sale_price, total=chassis_default.sale_price,
    )]
    with pytest.raises(ValidationError, match="requires a selection"):
        await _full_checkout_submit(db, H, items)


@pytest.mark.asyncio
async def test_checkout_succeeds_with_correctly_tagged_component_and_deducts_its_stock(db, H):
    og, ram_option, ram_product, ram_variant = await _build_ram_component(db, H)
    chassis, chassis_default = await _build_chassis(db, H)
    await _attach_as_component(db, H, chassis.id, og.id, required=True)

    from schemas.pos_sale import PosSaleItemCreate
    chassis_item_id = uuid4()
    items = [
        PosSaleItemCreate(
            id=chassis_item_id, variant_id=chassis_default.id, product_id=chassis.id, product_name=chassis.name,
            quantity=1, unit_price=chassis_default.sale_price, total=chassis_default.sale_price,
        ),
        PosSaleItemCreate(
            variant_id=ram_variant.id, product_id=ram_product.id, product_name=ram_product.name,
            quantity=1, unit_price=ram_variant.sale_price, total=ram_variant.sale_price,
            # og.id (the shared VariantOptionGroup id) — the only id the POS
            # ever has for this group, since that's what full-sync sends
            # (see PosSyncService._products' PosSyncVariantOptionGroup); the
            # attachment row's own id (ProductVariantOptionGroup.id) is never
            # exposed to the client and must not be expected here.
            parent_item_id=chassis_item_id, satisfies_option_group_id=og.id, component_option_id=ram_option.id,
        ),
    ]
    svc = VariantService(db)
    before = (await svc.get_branch_stock_row(ram_variant.id, H["branch_a"].id)).stock_quantity
    receipt = await _full_checkout_submit(db, H, items)
    assert len(receipt.items) == 2
    # The RAM line's own receipt entry is grouped under the chassis line.
    ram_receipt_item = next(i for i in receipt.items if i.product_name == ram_product.name)
    chassis_receipt_item = next(i for i in receipt.items if i.product_name == chassis.name)
    assert ram_receipt_item.parent_item_id == chassis_receipt_item.id
    after = (await svc.get_branch_stock_row(ram_variant.id, H["branch_a"].id)).stock_quantity
    assert after == before - 1


@pytest.mark.asyncio
async def test_checkout_rejects_spoofed_component_pairing(db, H):
    """Never trust the client's claimed component pairing (spec §42/43) —
    here the item claims to be the RAM option but its variant_id is
    actually an unrelated product's variant."""
    og, ram_option, ram_product, ram_variant = await _build_ram_component(db, H)
    chassis, chassis_default = await _build_chassis(db, H)
    await _attach_as_component(db, H, chassis.id, og.id, required=True)
    # A second, unrelated product with no groups of its own attached — used
    # only so the spoofed item passes every *other* check (combination-key,
    # its own required groups) and fails on exactly the one thing this test
    # is about: the component-pairing check.
    wrong_product, wrong_variant = await _build_chassis(db, H)

    from schemas.pos_sale import PosSaleItemCreate
    chassis_item_id = uuid4()
    items = [
        PosSaleItemCreate(
            id=chassis_item_id, variant_id=chassis_default.id, product_id=chassis.id, product_name=chassis.name,
            quantity=1, unit_price=chassis_default.sale_price, total=chassis_default.sale_price,
        ),
        PosSaleItemCreate(
            variant_id=wrong_variant.id, product_id=wrong_product.id, product_name=wrong_product.name,
            quantity=1, unit_price=wrong_variant.sale_price, total=wrong_variant.sale_price,
            parent_item_id=chassis_item_id, satisfies_option_group_id=og.id, component_option_id=ram_option.id,
        ),
    ]
    with pytest.raises(ValidationError, match="doesn't match the selected component"):
        await _full_checkout_submit(db, H, items)


@pytest.mark.asyncio
async def test_checkout_rejects_partially_tagged_component(db, H):
    chassis, chassis_default = await _build_chassis(db, H)
    from schemas.pos_sale import PosSaleItemCreate
    items = [PosSaleItemCreate(
        variant_id=chassis_default.id, product_id=chassis.id, product_name=chassis.name,
        quantity=1, unit_price=chassis_default.sale_price, total=chassis_default.sale_price,
        parent_item_id=uuid4(),  # only one of the three pairing fields set
    )]
    with pytest.raises(ValidationError, match="must all be set together"):
        await _full_checkout_submit(db, H, items)


@pytest.mark.asyncio
async def test_sync_payload_carries_usage_type_allowed_options_and_component_variant(db, H):
    og, ram_option, ram_product, ram_variant = await _build_ram_component(db, H)
    chassis, chassis_default = await _build_chassis(db, H)
    link = await _attach_as_component(db, H, chassis.id, og.id, required=True)
    await VariantOptionGroupService(db).set_allowed_options(
        chassis.id, H["tenant_a"].id, link.id, ProductVariantOptionAllowedSet(variant_option_ids=[ram_option.id]))

    from services.pos_sync_service import PosSyncService
    products = await PosSyncService(db)._products(H["biz_a"].id, H["branch_a"].id, None)
    synced_chassis = next(p for p in products if p.id == chassis.id)
    assert len(synced_chassis.variant_option_groups) == 1
    synced_group = synced_chassis.variant_option_groups[0]
    # The shared VariantOptionGroup id, not the attachment row's own id —
    # this is the only id the POS ever learns, and what it must echo back
    # as satisfies_option_group_id on checkout (see pos_sale_service.py's
    # _validate_component_selections()).
    assert synced_group.id == og.id
    assert synced_group.usage_type == "inventory_component"
    assert synced_group.allowed_option_ids == [ram_option.id]
    synced_option = next(o for o in synced_group.options if o.id == ram_option.id)
    assert synced_option.component_variant_id == ram_variant.id


# ══════════════════════════════════════════════════════════════
# Branch-to-branch stock transfer.
# ══════════════════════════════════════════════════════════════

async def _second_branch(db, H):
    branch2 = Branch(id=uuid4(), business_id=H["biz_a"].id, branch_code="BR_A2",
                      name="Alpha Branch 2", is_active=True)
    db.add(branch2)
    await db.flush()
    return branch2


@pytest.mark.asyncio
async def test_transfer_quantity_tracked_moves_stock_and_links_both_legs(db, H):
    branch2 = await _second_branch(db, H)
    svc = VariantService(db, created_by=H["user_a"].id)
    H["variant_a"].tracks_inventory = True
    await db.flush()
    await svc.change_branch_balance(H["variant_a"].id, H["branch_a"].id, 20, create_row_if_missing=True)

    await svc.transfer_stock(H["tenant_a"].id, H["variant_a"].id, H["branch_a"].id, branch2.id, 5, note="Restock")

    source = await svc.get_branch_stock_row(H["variant_a"].id, H["branch_a"].id)
    dest = await svc.get_branch_stock_row(H["variant_a"].id, branch2.id)
    assert source.stock_quantity == 15
    assert dest.stock_quantity == 5

    adjustments = (await db.scalars(select(StockAdjustment).where(
        StockAdjustment.variant_id == H["variant_a"].id,
        StockAdjustment.adjustment_type.in_(["transfer_out", "transfer_in"]),
    ))).all()
    assert len(adjustments) == 2
    out_row = next(a for a in adjustments if a.adjustment_type == "transfer_out")
    in_row = next(a for a in adjustments if a.adjustment_type == "transfer_in")
    assert out_row.quantity_change == -5
    assert in_row.quantity_change == 5
    assert out_row.reference_id == in_row.reference_id
    assert out_row.branch_id == H["branch_a"].id
    assert in_row.branch_id == branch2.id


@pytest.mark.asyncio
async def test_transfer_quantity_tracked_rejects_insufficient_source_stock(db, H):
    branch2 = await _second_branch(db, H)
    svc = VariantService(db, created_by=H["user_a"].id)
    H["variant_a"].tracks_inventory = True
    await db.flush()
    await svc.change_branch_balance(H["variant_a"].id, H["branch_a"].id, 3, create_row_if_missing=True)

    with pytest.raises(ValidationError):
        await svc.transfer_stock(H["tenant_a"].id, H["variant_a"].id, H["branch_a"].id, branch2.id, 999)

    # Nothing moved — source untouched.
    source = await svc.get_branch_stock_row(H["variant_a"].id, H["branch_a"].id)
    assert source.stock_quantity == 3
