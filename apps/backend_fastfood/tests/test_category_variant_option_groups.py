# tests/test_category_variant_option_groups.py
#
# Category-level Variant Option Group templates (CategoryVariantOptionGroup)
# and how they cascade onto ProductVariantOptionGroup — see
# services/category_variant_option_group_service.py's module docstring for
# the exact rules being pinned down here:
#   - attach to category -> attaches to every existing, non-component
#     product in it
#   - detach from category -> detaches from its products, skipping any a
#     live Variant still depends on
#   - editing the category template does NOT retroactively touch products
#     that already have their own row
#   - a new product created in a category picks up its templates
#   - moving a product to a different category re-parents shared groups,
#     detaches old-only ones (unless blocked), attaches new-only ones
#   - a manually/one-off attached group (source_category_id NULL) is never
#     auto-detached by any category-level change

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from core.exceptions import ConflictError, NotFoundError
from models.category import Category
from schemas.product import ProductCreate, ProductUpdate
from schemas.variant_option import VariantOptionComponentSet, VariantOptionCreate
from schemas.variant_option_group import (
    CategoryVariantOptionGroupAttach,
    CategoryVariantOptionGroupUpdate,
    ProductVariantOptionGroupAttach,
    VariantOptionGroupCreate,
)
from services.category_variant_option_group_service import CategoryVariantOptionGroupService
from services.product_service import ProductService
from services.variant_option_group_service import VariantOptionGroupService
from services.variant_option_service import VariantOptionService


async def _make_group(db, H, name="RAM"):
    return await VariantOptionGroupService(db).create(
        H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name=f"{name} {uuid4().hex[:6]}"),
    )


async def _make_product(db, H, category_id=None, code=None):
    return await ProductService(db).create(
        category_id or H["cat_a"].id, H["tenant_a"].id,
        ProductCreate(product_code=code or f"P{uuid4().hex[:8].upper()}", name="Test Product", price=Decimal("10.00")),
    )


async def _second_category(db, H):
    cat = Category(id=uuid4(), business_id=H["biz_a"].id, name=f"Other {uuid4().hex[:6]}", display_order=1)
    db.add(cat)
    await db.flush()
    return cat


@pytest.mark.asyncio
async def test_attach_to_category_cascades_to_existing_products(db, H):
    p1 = await _make_product(db, H)
    p2 = await _make_product(db, H)
    group = await _make_group(db, H)

    await CategoryVariantOptionGroupService(db).attach_to_category(
        H["cat_a"].id, H["tenant_a"].id, CategoryVariantOptionGroupAttach(option_group_id=group.id, is_required=True),
    )

    links1 = await VariantOptionGroupService(db).list_for_product(p1.id, H["tenant_a"].id)
    links2 = await VariantOptionGroupService(db).list_for_product(p2.id, H["tenant_a"].id)
    assert [l.option_group_id for l in links1] == [group.id]
    assert links1[0].is_required is True
    assert links1[0].source_category_id == H["cat_a"].id
    assert [l.option_group_id for l in links2] == [group.id]


@pytest.mark.asyncio
async def test_new_product_in_category_inherits_its_templates(db, H):
    group = await _make_group(db, H)
    await CategoryVariantOptionGroupService(db).attach_to_category(
        H["cat_a"].id, H["tenant_a"].id, CategoryVariantOptionGroupAttach(option_group_id=group.id),
    )

    product = await _make_product(db, H)
    links = await VariantOptionGroupService(db).list_for_product(product.id, H["tenant_a"].id)
    assert [l.option_group_id for l in links] == [group.id]
    assert links[0].source_category_id == H["cat_a"].id


@pytest.mark.asyncio
async def test_detach_from_category_cascades_and_skips_already_customized_removal(db, H):
    p1 = await _make_product(db, H)
    p2 = await _make_product(db, H)
    group = await _make_group(db, H)

    link = await CategoryVariantOptionGroupService(db).attach_to_category(
        H["cat_a"].id, H["tenant_a"].id, CategoryVariantOptionGroupAttach(option_group_id=group.id),
    )
    detached, skipped = await CategoryVariantOptionGroupService(db).detach_from_category(
        H["cat_a"].id, H["tenant_a"].id, link.id,
    )
    # >= 2, not == 2: the H fixture seeds its own pre-existing product in
    # cat_a (prod_a), which also picks up the cascade attach/detach.
    assert detached >= 2
    assert skipped == 0
    assert await VariantOptionGroupService(db).list_for_product(p1.id, H["tenant_a"].id) == []
    assert await VariantOptionGroupService(db).list_for_product(p2.id, H["tenant_a"].id) == []


@pytest.mark.asyncio
async def test_category_edit_does_not_retroactively_change_attached_products(db, H):
    """Editing the category template's is_required must not silently
    overwrite a product that already has its own row (whether or not it was
    itself customized) — only membership (attach/detach) cascades."""
    product = await _make_product(db, H)
    group = await _make_group(db, H)
    cat_svc = CategoryVariantOptionGroupService(db)
    link = await cat_svc.attach_to_category(
        H["cat_a"].id, H["tenant_a"].id, CategoryVariantOptionGroupAttach(option_group_id=group.id, is_required=True),
    )

    await cat_svc.update_attachment(
        H["cat_a"].id, H["tenant_a"].id, link.id, CategoryVariantOptionGroupUpdate(is_required=False),
    )

    product_links = await VariantOptionGroupService(db).list_for_product(product.id, H["tenant_a"].id)
    assert product_links[0].is_required is True  # unchanged despite the category default flipping


@pytest.mark.asyncio
async def test_category_change_reparents_shared_group_and_keeps_allowed_options(db, H):
    """A group both categories template should just be re-parented on the
    product's existing row (source_category_id updated), not detach+
    reattach — so a per-product customization like allowed-options survives."""
    other_cat = await _second_category(db, H)
    group = await _make_group(db, H)
    opt_svc = VariantOptionService(db)
    option = await opt_svc.create(group.id, H["tenant_a"].id, VariantOptionCreate(name="8GB"))
    tracked = await opt_svc.set_inventory_component(
        option.id, H["tenant_a"].id, VariantOptionComponentSet(sale_price=Decimal("15.00")),
    )
    option = tracked

    cat_svc = CategoryVariantOptionGroupService(db)
    await cat_svc.attach_to_category(H["cat_a"].id, H["tenant_a"].id, CategoryVariantOptionGroupAttach(option_group_id=group.id))
    await cat_svc.attach_to_category(other_cat.id, H["tenant_a"].id, CategoryVariantOptionGroupAttach(option_group_id=group.id))

    product = await _make_product(db, H)  # created under cat_a, inherits the group
    group_svc = VariantOptionGroupService(db)
    links = await group_svc.list_for_product(product.id, H["tenant_a"].id)
    link_id = links[0].id
    from schemas.variant_option_group import ProductVariantOptionAllowedSet
    await group_svc.set_allowed_options(
        product.id, H["tenant_a"].id, link_id, ProductVariantOptionAllowedSet(variant_option_ids=[option.id]),
    )

    await ProductService(db).update(product.id, H["tenant_a"].id, ProductUpdate(category_id=other_cat.id))

    links_after = await group_svc.list_for_product(product.id, H["tenant_a"].id)
    assert len(links_after) == 1
    assert links_after[0].id == link_id  # same row, re-parented — not detach/reattach
    assert links_after[0].source_category_id == other_cat.id
    assert links_after[0].allowed_option_ids == [option.id]  # customization preserved


@pytest.mark.asyncio
async def test_category_change_detaches_old_only_group_and_attaches_new_only_group(db, H):
    other_cat = await _second_category(db, H)
    old_only_group = await _make_group(db, H, name="OldOnly")
    new_only_group = await _make_group(db, H, name="NewOnly")

    cat_svc = CategoryVariantOptionGroupService(db)
    await cat_svc.attach_to_category(H["cat_a"].id, H["tenant_a"].id, CategoryVariantOptionGroupAttach(option_group_id=old_only_group.id))
    await cat_svc.attach_to_category(other_cat.id, H["tenant_a"].id, CategoryVariantOptionGroupAttach(option_group_id=new_only_group.id))

    product = await _make_product(db, H)
    await ProductService(db).update(product.id, H["tenant_a"].id, ProductUpdate(category_id=other_cat.id))

    links = await VariantOptionGroupService(db).list_for_product(product.id, H["tenant_a"].id)
    assert [l.option_group_id for l in links] == [new_only_group.id]


@pytest.mark.asyncio
async def test_manual_one_off_attachment_survives_category_change(db, H):
    other_cat = await _second_category(db, H)
    manual_group = await _make_group(db, H, name="OneOff")
    product = await _make_product(db, H)

    await VariantOptionGroupService(db).attach_to_product(
        product.id, H["tenant_a"].id, ProductVariantOptionGroupAttach(option_group_id=manual_group.id),
    )
    await ProductService(db).update(product.id, H["tenant_a"].id, ProductUpdate(category_id=other_cat.id))

    links = await VariantOptionGroupService(db).list_for_product(product.id, H["tenant_a"].id)
    assert [l.option_group_id for l in links] == [manual_group.id]
    assert links[0].source_category_id is None


@pytest.mark.asyncio
async def test_attach_to_category_skips_shared_inventory_component_products(db, H):
    """An inventory-component product (e.g. the auto-created "RAM 8GB"
    stock product behind a VariantOption) must never itself get Variant
    Selections — see VariantOptionGroupService.attach_to_product's own
    identical guard for a manual attach."""
    ram_group = await _make_group(db, H, name="RAM")
    opt_svc = VariantOptionService(db)
    option = await opt_svc.create(ram_group.id, H["tenant_a"].id, VariantOptionCreate(name="8GB"))
    tracked = await opt_svc.set_inventory_component(
        option.id, H["tenant_a"].id, VariantOptionComponentSet(sale_price=Decimal("20.00")),
    )
    component_product_id = tracked.component_product_id
    assert component_product_id is not None

    components_category_id = None
    from sqlalchemy import select
    from models.product import Product
    components_category_id = await db.scalar(select(Product.category_id).where(Product.id == component_product_id))

    other_group = await _make_group(db, H, name="Storage")
    await CategoryVariantOptionGroupService(db).attach_to_category(
        components_category_id, H["tenant_a"].id, CategoryVariantOptionGroupAttach(option_group_id=other_group.id),
    )
    links = await VariantOptionGroupService(db).list_for_product(component_product_id, H["tenant_a"].id)
    assert links == []


@pytest.mark.asyncio
async def test_attach_to_category_rejects_duplicate(db, H):
    group = await _make_group(db, H)
    svc = CategoryVariantOptionGroupService(db)
    await svc.attach_to_category(H["cat_a"].id, H["tenant_a"].id, CategoryVariantOptionGroupAttach(option_group_id=group.id))
    with pytest.raises(ConflictError):
        await svc.attach_to_category(H["cat_a"].id, H["tenant_a"].id, CategoryVariantOptionGroupAttach(option_group_id=group.id))


@pytest.mark.asyncio
async def test_category_not_found_raises(db, H):
    svc = CategoryVariantOptionGroupService(db)
    with pytest.raises(NotFoundError):
        await svc.list_for_category(uuid4(), H["tenant_a"].id)
