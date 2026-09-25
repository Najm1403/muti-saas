# tests/test_spec_matrix.py
#
# Dedicated coverage for apps/COMPLETE-IMPLEMENTATION-SPEC.md Part I's test
# matrix — each test below is one bullet from that list, verified against the
# real service layer (not just exercised incidentally by other tests).

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from core.exceptions import ConflictError, NotFoundError, ValidationError
from models.device import Device, DeviceStatus
from models.product import Product
from models.variant import Variant
from schemas.addon_group import AddonGroupCreate, ProductAddonGroupAttach
from schemas.addon_item import AddonItemCreate
from schemas.pos_sale import (
    PosSaleAddonSelection,
    PosSaleCreate,
    PosSaleItemCreate,
    PosSalePaymentCreate,
)
from schemas.variant_option import VariantOptionCreate
from schemas.variant_option_group import (
    ProductVariantOptionGroupAttach,
    VariantOptionGroupCreate,
)
from services.addon_group_service import AddonGroupService
from services.addon_item_service import AddonItemService
from services.business_policy import enforce_pricing_policy, enforce_tracking_policy
from services.pos_sale_service import PosSaleService
from services.product_service import ProductService
from services.variant_option_group_service import VariantOptionGroupService
from services.variant_option_service import VariantOptionService
from services.variant_service import VariantService
from schemas.product import ProductCreate


def _sale(H, product, addons=None, options=None, total=Decimal("9.99"), payment=Decimal("9.99")):
    return PosSaleCreate(
        sale_number="SPEC-" + uuid4().hex[:10],
        sold_at=datetime.now(timezone.utc),
        subtotal=total, total=total,
        items=[PosSaleItemCreate(
            variant_id=product.default_variant_id, product_id=product.id, product_name=product.name,
            quantity=1, unit_price=Decimal("9.99"), total=total,
            options=options or [], addons=addons or [],
        )],
        payments=[PosSalePaymentCreate(payment_method="Cash", amount=payment)],
    )


async def _submit(db, H, data):
    return await PosSaleService(db).create(data, H["branch_a"].id, H["device_a"].id, H["user_a"].id, H["tenant_a"].id)


async def _fresh_option(db, H, name="Fresh"):
    """H's og_a already has opt_a attached to prod_a's variant_a — tests that
    need a brand-new, never-yet-used combination_key add a sibling option."""
    return await VariantOptionService(db).create(H["og_a"].id, H["tenant_a"].id, VariantOptionCreate(name=name + uuid4().hex[:6]))


# ══════════════════════════════════════════════════════════════
# 1. A no-variant product sells via its default variant and deducts
#    stock correctly.
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_no_variant_product_sells_via_default_variant_and_deducts_stock(db, H):
    H["pvog_a"].is_required = False  # H's fixture attaches a required group to prod_a by default
    H["prod_a"].allow_inventory_tracking = True
    await db.flush()
    svc = VariantService(db, created_by=H["user_a"].id)
    await svc.set_tracking(H["tenant_a"].id, H["default_variant_a"].id, True, {str(H["branch_a"].id): 5})

    data = _sale(H, H["prod_a"])
    receipt = await _submit(db, H, data)
    assert receipt.total == Decimal("9.99")

    row = await svc.get_branch_stock_row(H["default_variant_a"].id, H["branch_a"].id)
    assert row.stock_quantity == 4


# ══════════════════════════════════════════════════════════════
# 2. A shared Variant Option Group is selectable on a second product
#    without recreating it.
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_shared_variant_option_group_reusable_on_second_product(db, H):
    cat_svc = __import__("services.category_service", fromlist=["CategoryService"]).CategoryService(db)
    from schemas.category import CategoryCreate
    cat2 = await cat_svc.create(H["biz_a"].id, H["tenant_a"].id, CategoryCreate(name="Second Category"))
    prod_svc = ProductService(db)
    prod2 = await prod_svc.create(cat2.id, H["tenant_a"].id, ProductCreate(
        product_code="SECOND", name="Second Product", price=Decimal("4.00"),
    ))

    vog_svc = VariantOptionGroupService(db)
    # H["og_a"] already belongs to biz_a and is attached to prod_a — attach
    # the SAME group to a brand-new product without creating a new one.
    attached = await vog_svc.attach_to_product(
        prod2.id, H["tenant_a"].id, ProductVariantOptionGroupAttach(
            option_group_id=H["og_a"].id, is_required=False, usage_type="specification"),
    )
    assert attached.option_group_id == H["og_a"].id

    links_for_prod1 = await vog_svc.list_for_product(H["prod_a"].id, H["tenant_a"].id)
    links_for_prod2 = await vog_svc.list_for_product(prod2.id, H["tenant_a"].id)
    assert H["og_a"].id in [l.option_group_id for l in links_for_prod1]
    assert H["og_a"].id in [l.option_group_id for l in links_for_prod2]

    # And its existing option is usable on the second product's own variants.
    variant = await VariantService(db).create(
        H["tenant_a"].id, prod2.id, [H["opt_a"].id], sale_price=Decimal("4.50"),
    )
    assert str(H["opt_a"].id) in variant.option_value_ids


# ══════════════════════════════════════════════════════════════
# 3. A topping-heavy order prices correctly with NO combination-row
#    explosion — the Variant table only ever grows per Variant Option
#    Group value, never per Add-on combination.
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_addon_heavy_order_does_not_explode_variant_table(db, H):
    H["pvog_a"].is_required = False
    addon_svc = AddonGroupService(db)
    item_svc = AddonItemService(db)
    group = await addon_svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Toppings", selection_type="multiple"))
    toppings = []
    for name in ["Cheese", "Mushroom", "Olives", "Jalapeno", "Onion"]:
        toppings.append(await item_svc.create(group.id, H["tenant_a"].id, AddonItemCreate(name=name, price_delta=Decimal("1.00"))))

    variant_svc = VariantService(db)
    Variant = __import__("models.variant", fromlist=["Variant"]).Variant
    before = len((await db.scalars(variant_svc.scoped(H["tenant_a"].id).where(
        Variant.product_id == H["prod_a"].id))).all())

    # Sell the same product with every possible subset of toppings selected —
    # none of this may ever create a new Variant row.
    unit_price = Decimal("9.99")
    for size in range(len(toppings) + 1):
        selected = toppings[:size]
        addon_total = sum(t.price_delta for t in selected)
        line_total = unit_price + addon_total
        data = PosSaleCreate(
            sale_number="TOP-" + uuid4().hex[:10], sold_at=datetime.now(timezone.utc),
            subtotal=line_total, total=line_total,
            items=[PosSaleItemCreate(
                variant_id=H["default_variant_a"].id, product_id=H["prod_a"].id, product_name=H["prod_a"].name,
                quantity=1, unit_price=unit_price, total=line_total,
                addons=[PosSaleAddonSelection(addon_item_id=t.id, addon_name=t.name, price_delta=t.price_delta) for t in selected],
            )],
            payments=[PosSalePaymentCreate(payment_method="Cash", amount=line_total)],
        )
        await _submit(db, H, data)

    after = len((await db.scalars(variant_svc.scoped(H["tenant_a"].id).where(
        Variant.product_id == H["prod_a"].id))).all())
    assert after == before, "Add-on selections must never create new Variant rows (spec A1/D4)."


# ══════════════════════════════════════════════════════════════
# 4. Unchecking a default_selected Add-on Item results in
#    was_removed: true on the persisted sale record.
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_unchecking_default_selected_addon_persists_was_removed(db, H):
    H["pvog_a"].is_required = False
    addon_svc = AddonGroupService(db)
    item_svc = AddonItemService(db)
    group = await addon_svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Base", selection_type="multiple"))
    onion = await item_svc.create(group.id, H["tenant_a"].id, AddonItemCreate(name="Onion", price_delta=Decimal("0"), default_selected=True))

    data = _sale(H, H["prod_a"], addons=[
        PosSaleAddonSelection(addon_item_id=onion.id, addon_name="Onion", price_delta=Decimal("0"), was_removed=True),
    ])
    receipt = await _submit(db, H, data)

    from models.sale_item import SaleItem
    from models.sale_item_addon import SaleItemAddon
    from sqlalchemy import select
    item = await db.scalar(select(SaleItem).where(SaleItem.sale_id == receipt.sale_id))
    stored = await db.scalar(select(SaleItemAddon).where(SaleItemAddon.sale_item_id == item.id))
    assert stored.was_removed is True
    assert stored.addon_name == "Onion"


# ══════════════════════════════════════════════════════════════
# 5/6. Untracked variant sells past zero; tracked quantity variant
#      blocks correctly at zero stock.
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_untracked_variant_sells_past_zero_no_block(db, H):
    H["pvog_a"].is_required = False
    # default_variant_a.tracks_inventory is False by construction (H fixture).
    await VariantService(db).validate_stock(H["tenant_a"].id, [(H["default_variant_a"].id, 999999)], branch_id=H["branch_a"].id)
    # No exception — untracked variants are always sellable regardless of demand.


@pytest.mark.asyncio
async def test_tracked_quantity_variant_blocks_at_zero_stock(db, H):
    H["pvog_a"].is_required = False
    H["prod_a"].allow_inventory_tracking = True
    await db.flush()
    svc = VariantService(db, created_by=H["user_a"].id)
    await svc.set_tracking(H["tenant_a"].id, H["default_variant_a"].id, True, {str(H["branch_a"].id): 0})

    with pytest.raises(ValidationError, match="Insufficient stock"):
        await svc.validate_stock(H["tenant_a"].id, [(H["default_variant_a"].id, 1)], branch_id=H["branch_a"].id)


# ══════════════════════════════════════════════════════════════
# 7/8. Business-template policy is enforced server-side (D6) — a
#      disabled UI control is not a real rule on its own.
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_tracking_forced_on_rejects_untracked_variant_even_via_service_layer(db, H):
    """Simulates an 'Electronics'-style template: tracking_forced_on=True
    must reject tracks_inventory=False regardless of what any UI sent."""
    from models.business_template import BusinessTemplate
    forced_template = BusinessTemplate(id=uuid4(), name=f"Electronics {uuid4().hex[:6]}", config={
        "inventory": {"tracking_forced_on": True}, "pricing": {"require_cost_price": False},
    })
    db.add(forced_template)
    H["tenant_a"].business_template_id = forced_template.id
    await db.flush()

    with pytest.raises(ValidationError, match="requires inventory tracking"):
        await enforce_tracking_policy(db, H["tenant_a"].id, False)

    # And the real creation path enforces it too, not just the raw helper.
    with pytest.raises(ValidationError, match="requires inventory tracking"):
        await VariantService(db).create(
            H["tenant_a"].id, H["prod_a"].id, [], sale_price=Decimal("5.00"), tracks_inventory=False,
        )

    # But omitting tracks_inventory entirely (the tenant dashboard's "Create a
    # variant" form never sent it) must auto-default to tracked, not fail —
    # this was the actual reported bug: "every variant should be trackable"
    # blocked variant creation even though nothing asked for it to be untracked.
    H["prod_a"].allow_inventory_tracking = True
    await db.flush()
    opt = await _fresh_option(db, H, "AutoTracked")
    variant = await VariantService(db).create(
        H["tenant_a"].id, H["prod_a"].id, [opt.id], sale_price=Decimal("5.00"),
    )
    assert variant.tracks_inventory is True


@pytest.mark.asyncio
async def test_tracking_default_on_seeds_products_but_remains_editable(db, H):
    """A template default is not a mandate: omitted means tracked, while an
    explicit tenant choice to disable tracking remains valid."""
    from models.business_template import BusinessTemplate
    template = BusinessTemplate(id=uuid4(), name=f"DefaultTracked {uuid4().hex[:6]}", config={
        "inventory": {"tracking_default_on": True, "tracking_forced_on": False},
    })
    db.add(template)
    H["tenant_a"].business_template_id = template.id
    await db.flush()

    defaulted = await ProductService(db).create(
        H["cat_a"].id,
        H["tenant_a"].id,
        ProductCreate(
            product_code=f"DEF-{uuid4().hex[:8]}",
            name="Default tracked",
            price=Decimal("10.00"),
        ),
    )
    assert defaulted.allow_inventory_tracking is True
    default_variant = await db.get(Variant, defaulted.default_variant_id)
    assert default_variant.tracks_inventory is True

    opted_out = await ProductService(db).create(
        H["cat_a"].id,
        H["tenant_a"].id,
        ProductCreate(
            product_code=f"OFF-{uuid4().hex[:8]}",
            name="Explicitly untracked",
            price=Decimal("10.00"),
            allow_inventory_tracking=False,
        ),
    )
    assert opted_out.allow_inventory_tracking is False


@pytest.mark.asyncio
async def test_tenant_dashboard_low_stock_is_tracked_branch_scoped(db, H):
    from services.tenant_dashboard_service import TenantDashboardService

    H["biz_a"].low_stock_threshold = 5
    H["prod_a"].allow_inventory_tracking = True
    H["prod_a"].all_branches = True
    variants = (await db.scalars(
        select(Variant).where(Variant.product_id == H["prod_a"].id)
    )).all()
    for variant in variants:
        variant.tracks_inventory = variant.id == H["default_variant_a"].id
    await db.flush()

    stats = await TenantDashboardService(db).get_stats(H["tenant_a"].id)
    assert stats.low_stock_threshold == 5
    # No cache row is still zero stock; tenant B's catalog must not leak in.
    assert stats.low_stock_count == 1


@pytest.mark.asyncio
async def test_tracks_inventory_auto_defaults_when_product_allows_tracking(db, H):
    """Even without tracking_forced_on, a product that already has tracking
    enabled should get auto-tracked variants by default (item 3) — the
    tenant may still explicitly untrack an individual variant."""
    H["prod_a"].allow_inventory_tracking = True
    await db.flush()

    opt1 = await _fresh_option(db, H, "Auto")
    auto = await VariantService(db).create(
        H["tenant_a"].id, H["prod_a"].id, [opt1.id], sale_price=Decimal("5.00"),
    )
    assert auto.tracks_inventory is True

    opt2 = await _fresh_option(db, H, "ManualOff")
    manual_off = await VariantService(db).create(
        H["tenant_a"].id, H["prod_a"].id, [opt2.id], sale_price=Decimal("5.00"), tracks_inventory=False,
    )
    assert manual_off.tracks_inventory is False

    # A product that never enabled tracking still can't get a tracked variant,
    # auto-default or not.
    H["prod_b"].allow_inventory_tracking = False
    await db.flush()
    opt_b = await VariantOptionService(db).create(
        H["og_b"].id, H["tenant_b"].id, VariantOptionCreate(name="FreshB" + uuid4().hex[:6]))
    untracked_product = await VariantService(db).create(
        H["tenant_b"].id, H["prod_b"].id, [opt_b.id], sale_price=Decimal("5.00"),
    )
    assert untracked_product.tracks_inventory is False


@pytest.mark.asyncio
async def test_compute_sellability_flags_orphaned_variant_missing_required_group(db, H):
    """A product's zero-option default variant becomes unsellable — with a
    clear reason, not just a silent flag — once a required Variant Option
    Group it doesn't satisfy is attached to that product. This is exactly
    what previously let stock be added to a SKU that could never be sold:
    sellable was hardcoded True everywhere, never actually computed."""
    svc = VariantService(db)
    sellability = await svc.compute_sellability(
        [H["default_variant_a"], H["variant_a"]]
    )

    # H's og_a/pvog_a (required=True) is attached to prod_a, but
    # default_variant_a has option_value_ids=[] — it satisfies nothing.
    orphaned_sellable, orphaned_reason = sellability[H["default_variant_a"].id]
    assert orphaned_sellable is False
    assert orphaned_reason is not None
    assert "required" in orphaned_reason.lower()

    # variant_a selects opt_a (og_a's option) — it does satisfy the
    # required group and must stay sellable.
    real_sellable, real_reason = sellability[H["variant_a"].id]
    assert real_sellable is True
    assert real_reason is None

    # Empty input must not error.
    assert await svc.compute_sellability([]) == {}


@pytest.mark.asyncio
async def test_cost_price_remains_optional_with_legacy_required_flag(db, H):
    from models.business_template import BusinessTemplate
    cost_required_template = BusinessTemplate(id=uuid4(), name=f"CostRequired {uuid4().hex[:6]}", config={
        "inventory": {"tracking_forced_on": False}, "pricing": {"require_cost_price": True},
    })
    db.add(cost_required_template)
    H["tenant_a"].business_template_id = cost_required_template.id
    await db.flush()

    await enforce_pricing_policy(db, H["tenant_a"].id, None)

    H["pvog_a"].is_required = False
    opt1 = await _fresh_option(db, H, "CostA")
    optional = await VariantService(db).create(
        H["tenant_a"].id, H["prod_a"].id, [opt1.id], sale_price=Decimal("5.00"), cost_price=None,
    )
    assert optional.cost_price is None

    # A cost price present satisfies the same policy.
    opt2 = await _fresh_option(db, H, "CostB")
    variant = await VariantService(db).create(
        H["tenant_a"].id, H["prod_a"].id, [opt2.id], sale_price=Decimal("5.00"), cost_price=Decimal("3.00"),
    )
    assert variant.cost_price == Decimal("3.00")


@pytest.mark.asyncio
async def test_variants_disabled_template_rejects_attaching_a_variant_option_group(db, H):
    """Fast-Food-style template (config.variants.enabled=False, Product +
    delta-priced Add-ons only) must reject attaching a Variant Option Group
    server-side too — the dashboard hiding "Attach Option Group" is not a
    real rule on its own (mirrors the tracking/cost-price policy tests above)."""
    from models.business_template import BusinessTemplate
    from services.business_policy import enforce_variants_enabled

    no_variants_template = BusinessTemplate(id=uuid4(), name=f"NoVariants {uuid4().hex[:6]}", config={
        "variants": {"enabled": False},
    })
    db.add(no_variants_template)
    H["tenant_a"].business_template_id = no_variants_template.id
    await db.flush()

    with pytest.raises(ValidationError, match="does not use Variant Option Groups"):
        await enforce_variants_enabled(db, H["tenant_a"].id)

    cat_svc = __import__("services.category_service", fromlist=["CategoryService"]).CategoryService(db)
    from schemas.category import CategoryCreate
    cat2 = await cat_svc.create(H["biz_a"].id, H["tenant_a"].id, CategoryCreate(name="Fastfood Category"))
    prod_svc = ProductService(db)
    prod2 = await prod_svc.create(cat2.id, H["tenant_a"].id, ProductCreate(
        product_code="BURGER", name="Burger", price=Decimal("4.00"),
    ))
    new_group = await VariantOptionGroupService(db).create(
        H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name=f"Size {uuid4().hex[:6]}"),
    )
    with pytest.raises(ValidationError, match="does not use Variant Option Groups"):
        await VariantOptionGroupService(db).attach_to_product(
            prod2.id, H["tenant_a"].id,
            ProductVariantOptionGroupAttach(option_group_id=new_group.id, is_required=False),
        )

    # Switching to a template without the flag (business_template_id is
    # required, not nullable) must not carry the rejection forward — fails
    # open, matching every other business_policy check in this module.
    open_template = BusinessTemplate(id=uuid4(), name=f"Open {uuid4().hex[:6]}", config={})
    db.add(open_template)
    H["tenant_a"].business_template_id = open_template.id
    await db.flush()
    attached = await VariantOptionGroupService(db).attach_to_product(
        prod2.id, H["tenant_a"].id,
        ProductVariantOptionGroupAttach(option_group_id=new_group.id, is_required=False),
    )
    assert attached.option_group_id == new_group.id


@pytest.mark.asyncio
async def test_addons_disabled_template_rejects_attaching_an_addon_group(db, H):
    """Mirror of the variants-disabled test above, for the opposite case:
    a Laptop-style template (config.addons.enabled=False, priced entirely
    via Variant Options) must reject attaching an Add-on Group server-side
    too — the dashboard hiding the Add-ons section is not a real rule on
    its own."""
    from models.business_template import BusinessTemplate
    from services.business_policy import enforce_addons_enabled

    no_addons_template = BusinessTemplate(id=uuid4(), name=f"NoAddons {uuid4().hex[:6]}", config={
        "addons": {"enabled": False},
    })
    db.add(no_addons_template)
    H["tenant_a"].business_template_id = no_addons_template.id
    await db.flush()

    with pytest.raises(ValidationError, match="does not use Add-on Groups"):
        await enforce_addons_enabled(db, H["tenant_a"].id)

    cat_svc = __import__("services.category_service", fromlist=["CategoryService"]).CategoryService(db)
    from schemas.category import CategoryCreate
    cat2 = await cat_svc.create(H["biz_a"].id, H["tenant_a"].id, CategoryCreate(name="Laptop Category"))
    prod_svc = ProductService(db)
    prod2 = await prod_svc.create(cat2.id, H["tenant_a"].id, ProductCreate(
        product_code="LAPTOP1", name="Laptop", price=Decimal("999.00"),
    ))
    new_group = await AddonGroupService(db).create(
        H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name=f"Extras {uuid4().hex[:6]}"),
    )
    with pytest.raises(ValidationError, match="does not use Add-on Groups"):
        await AddonGroupService(db).attach_to_product(
            prod2.id, H["tenant_a"].id,
            ProductAddonGroupAttach(addon_group_id=new_group.id),
        )

    # Switching to a template without the flag must not carry the rejection
    # forward — fails open, matching every other business_policy check.
    open_template = BusinessTemplate(id=uuid4(), name=f"Open {uuid4().hex[:6]}", config={})
    db.add(open_template)
    H["tenant_a"].business_template_id = open_template.id
    await db.flush()
    attached = await AddonGroupService(db).attach_to_product(
        prod2.id, H["tenant_a"].id,
        ProductAddonGroupAttach(addon_group_id=new_group.id),
    )
    assert attached.addon_group_id == new_group.id


# ══════════════════════════════════════════════════════════════
# 10. Passing an AddonItem id into a Variant's option_ids at creation
#     fails validation — no code path accepts it.
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_addon_item_id_rejected_as_variant_option_id(db, H):
    H["pvog_a"].is_required = False
    addon_svc = AddonGroupService(db)
    item_svc = AddonItemService(db)
    group = await addon_svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Extras"))
    item = await item_svc.create(group.id, H["tenant_a"].id, AddonItemCreate(name="Extra Sauce"))

    with pytest.raises(ValidationError, match="must belong to this product"):
        await VariantService(db).create(
            H["tenant_a"].id, H["prod_a"].id, [item.id], sale_price=Decimal("5.00"),
        )


# ══════════════════════════════════════════════════════════════
# 11. Two offline devices each creating a sale get non-colliding
#     identifiers and both sync cleanly.
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_two_devices_create_sales_with_no_id_collisions(db, H):
    H["pvog_a"].is_required = False
    second_device = Device(
        id=uuid4(), branch_id=H["branch_a"].id, device_code="DEV_A2", letter="B", name="Second POS",
        device_type="POS", status=DeviceStatus.ACTIVE,
    )
    db.add(second_device)
    await db.flush()

    data1 = _sale(H, H["prod_a"])
    data1.id = uuid4()
    receipt1 = await PosSaleService(db).create(data1, H["branch_a"].id, H["device_a"].id, H["user_a"].id, H["tenant_a"].id)

    data2 = _sale(H, H["prod_a"])
    data2.id = uuid4()
    receipt2 = await PosSaleService(db).create(data2, H["branch_a"].id, second_device.id, H["user_a"].id, H["tenant_a"].id)

    assert receipt1.sale_id != receipt2.sale_id
    assert data1.id != data2.id

    from models.sale import Sale
    from sqlalchemy import select
    stored1 = await db.scalar(select(Sale).where(Sale.id == receipt1.sale_id))
    stored2 = await db.scalar(select(Sale).where(Sale.id == receipt2.sale_id))
    assert stored1.device_id == H["device_a"].id
    assert stored2.device_id == second_device.id


# ══════════════════════════════════════════════════════════════
# 12. An idempotent retry (same sale_number, same device) must NOT be
#     falsely deduplicated when two submissions differ only by which
#     variant_id was sold at an equal price.
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_idempotent_retry_not_falsely_deduped_when_variant_differs_at_equal_price(db, H):
    H["pvog_a"].is_required = False
    # A second variant on the same product at the exact same price as the default.
    fresh_opt = await _fresh_option(db, H, "Idemp")
    other_variant = await VariantService(db).create(
        H["tenant_a"].id, H["prod_a"].id, [fresh_opt.id], sale_price=Decimal("9.99"),
    )

    sale_number = "IDEMP-" + uuid4().hex[:8]
    # Retry recognition matches on the client-generated Sale id (offline-first
    # devices resend the same id on retry) plus full line content — so the
    # first and third submissions below deliberately share one.
    client_sale_id = uuid4()
    common = dict(sale_number=sale_number, sold_at=datetime.now(timezone.utc), subtotal=Decimal("9.99"), total=Decimal("9.99"))

    first = PosSaleCreate(id=client_sale_id, **common, items=[PosSaleItemCreate(
        variant_id=H["default_variant_a"].id, product_id=H["prod_a"].id, product_name=H["prod_a"].name,
        quantity=1, unit_price=Decimal("9.99"), total=Decimal("9.99"),
    )], payments=[PosSalePaymentCreate(payment_method="Cash", amount=Decimal("9.99"))])
    await _submit(db, H, first)

    # Same sale_number, same device, but a DIFFERENT variant_id at the same
    # price — this must be treated as a genuine conflict, never silently
    # accepted as "the same retry".
    second = PosSaleCreate(**common, items=[PosSaleItemCreate(
        variant_id=other_variant.id, product_id=H["prod_a"].id, product_name=H["prod_a"].name,
        quantity=1, unit_price=Decimal("9.99"), total=Decimal("9.99"),
    )], payments=[PosSalePaymentCreate(payment_method="Cash", amount=Decimal("9.99"))])
    with pytest.raises(ConflictError):
        await _submit(db, H, second)

    # But re-submitting the exact same payload (same client-generated id) IS
    # recognized as a safe retry.
    third = PosSaleCreate(id=client_sale_id, **common, items=[PosSaleItemCreate(
        variant_id=H["default_variant_a"].id, product_id=H["prod_a"].id, product_name=H["prod_a"].name,
        quantity=1, unit_price=Decimal("9.99"), total=Decimal("9.99"),
    )], payments=[PosSalePaymentCreate(payment_method="Cash", amount=Decimal("9.99"))])
    receipt = await _submit(db, H, third)
    assert receipt.total == Decimal("9.99")


# ══════════════════════════════════════════════════════════════
# Deleting an orphaned zero-option default Variant — the cleanup path for
# the exact scenario compute_sellability was built to detect: a required
# Variant Option Group attached after the default Variant already existed,
# leaving it permanently unsellable (reported live: a fresh "dell" product
# whose default Variant showed "Can't be sold — missing a required option"
# forever, with no way to remove it).
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_delete_orphaned_default_variant_succeeds_and_clears_default_variant_id(db, H):
    prod = await ProductService(db).create(H["cat_a"].id, H["tenant_a"].id, ProductCreate(
        product_code="DELLTEST", name="Dell Test", price=Decimal("56000.00"),
    ))
    group = await VariantOptionGroupService(db).create(
        H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name=f"RAM {uuid4().hex[:6]}"),
    )
    await VariantOptionGroupService(db).attach_to_product(
        prod.id, H["tenant_a"].id, ProductVariantOptionGroupAttach(
            option_group_id=group.id, is_required=True, usage_type="specification"),
    )
    opt = await VariantOptionService(db).create(group.id, H["tenant_a"].id, VariantOptionCreate(name="16GB"))
    real_variant = await VariantService(db).create(
        H["tenant_a"].id, prod.id, [opt.id], sale_price=Decimal("56000.00"),
    )

    variants_stmt = VariantService(db).scoped(H["tenant_a"].id).where(Variant.product_id == prod.id)
    default_variant = next(v for v in (await db.scalars(variants_stmt)).all() if v.is_default)
    assert default_variant.id != real_variant.id  # sanity: the orphaned one, not the real combination

    sellability = await VariantService(db).compute_sellability([default_variant])
    assert sellability[default_variant.id] == (False, VariantService.UNSELLABLE_REASON)

    await VariantService(db).delete(H["tenant_a"].id, default_variant.id)

    with pytest.raises(NotFoundError):
        await VariantService(db).get(H["tenant_a"].id, default_variant.id)
    refreshed_product = await db.scalar(select(Product).where(Product.id == prod.id))
    assert refreshed_product.default_variant_id is None


@pytest.mark.asyncio
async def test_delete_variant_blocked_when_it_still_has_stock(db, H):
    H["pvog_a"].is_required = False
    H["prod_a"].allow_inventory_tracking = True
    await db.flush()
    opt = await _fresh_option(db, H, "HasStock")
    variant = await VariantService(db).create(
        H["tenant_a"].id, H["prod_a"].id, [opt.id], sale_price=Decimal("5.00"),
        tracks_inventory=True, opening_stock_by_branch={H["branch_a"].id: 3},
    )
    with pytest.raises(ConflictError, match="still has stock"):
        await VariantService(db).delete(H["tenant_a"].id, variant.id)


@pytest.mark.asyncio
async def test_delete_variant_blocked_when_it_has_sale_history(db, H):
    # H's fixture already sold H["default_variant_a"] once (item_a) — the
    # exact "ever sold" case, for free, without simulating a new sale here.
    with pytest.raises(ConflictError, match="sale history"):
        await VariantService(db).delete(H["tenant_a"].id, H["default_variant_a"].id)


@pytest.mark.asyncio
async def test_delete_variant_blocked_as_the_products_last_remaining_variant(db, H):
    prod = await ProductService(db).create(H["cat_a"].id, H["tenant_a"].id, ProductCreate(
        product_code="LONELY", name="Lonely Product", price=Decimal("1.00"),
    ))
    with pytest.raises(ConflictError, match="last one"):
        await VariantService(db).delete(H["tenant_a"].id, prod.default_variant_id)


@pytest.mark.asyncio
async def test_deleted_variant_combination_key_can_be_reused(db, H):
    """Removing a priced combination Variant (e.g. un-offering a Color) must
    not permanently block ever recreating that same option combination —
    only a live row should collide (uq_variant_combination is a partial
    index over deleted_at IS NULL, see models/variant.py)."""
    H["pvog_a"].is_required = False
    H["prod_a"].allow_inventory_tracking = True
    await db.flush()
    opt = await _fresh_option(db, H, "Reofferable")
    svc = VariantService(db)
    first = await svc.create(H["tenant_a"].id, H["prod_a"].id, [opt.id], sale_price=Decimal("5.00"))
    await svc.delete(H["tenant_a"].id, first.id)

    second = await svc.create(H["tenant_a"].id, H["prod_a"].id, [opt.id], sale_price=Decimal("6.00"))
    assert second.id != first.id
    assert second.sale_price == Decimal("6.00")
