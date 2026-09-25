# tests/test_menu_services.py
#
# Service-level tests for Category, Product, Variant Option Group/Option,
# and Add-on Group/Item (spec A1: Variants are single-select and define the
# SKU; Add-ons are multi-select, price-delta only, and never generate
# variant combinations).
# Tests CRUD operations, ownership enforcement, relationship traversal,
# and cross-tenant access denial — all via the service layer.
# All DB writes are rolled back after each test.

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError, ValidationError
from models.variant import Variant
from services.category_service import CategoryService
from services.variant_option_group_service import VariantOptionGroupService
from services.variant_option_service import VariantOptionService
from services.addon_group_service import AddonGroupService
from services.addon_item_service import AddonItemService
from services.product_service import ProductService
from services.variant_service import VariantService
from schemas.category import CategoryCreate, CategoryUpdate
from schemas.product import ProductCreate, ProductUpdate
from schemas.variant_option_group import (
    ProductVariantOptionGroupAttach,
    VariantOptionGroupCreate,
    VariantOptionGroupUpdate,
)
from schemas.variant_option import VariantOptionCreate, VariantOptionUpdate
from schemas.addon_group import (
    AddonGroupCreate,
    AddonGroupUpdate,
    ProductAddonGroupAttach,
)
from schemas.addon_item import AddonItemCreate, AddonItemUpdate


# ════════════════════════════════════════════════════════════════
# CategoryService
# ════════════════════════════════════════════════════════════════

class TestCategoryService:

    @pytest.mark.asyncio
    async def test_create_and_get(self, db: AsyncSession, H):
        svc = CategoryService(db)
        data = CategoryCreate(name="Desserts", display_order=5)
        created = await svc.create(H["biz_a"].id, H["tenant_a"].id, data)

        assert created.name == "Desserts"
        assert created.display_order == 5
        assert created.is_active is True
        assert created.business_id == H["biz_a"].id

        fetched = await svc.get(created.id, H["tenant_a"].id)
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_get_wrong_tenant_raises_not_found(self, db: AsyncSession, H):
        svc = CategoryService(db)
        with pytest.raises(NotFoundError):
            await svc.get(H["cat_a"].id, H["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_create_under_wrong_tenant_business_raises(
        self, db: AsyncSession, H
    ):
        svc = CategoryService(db)
        data = CategoryCreate(name="Should Fail")
        with pytest.raises(NotFoundError):
            await svc.create(H["biz_b"].id, H["tenant_a"].id, data)

    @pytest.mark.asyncio
    async def test_list_returns_only_own_tenant_categories(
        self, db: AsyncSession, H
    ):
        svc = CategoryService(db)
        cats = await svc.list(H["biz_a"].id, H["tenant_a"].id)
        ids = [c.id for c in cats]
        assert H["cat_a"].id in ids
        assert H["cat_b"].id not in ids

    @pytest.mark.asyncio
    async def test_list_cross_tenant_business_raises(self, db: AsyncSession, H):
        svc = CategoryService(db)
        with pytest.raises(NotFoundError):
            await svc.list(H["biz_b"].id, H["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_update_name(self, db: AsyncSession, H):
        svc = CategoryService(db)
        updated = await svc.update(
            H["cat_a"].id, H["tenant_a"].id, CategoryUpdate(name="Updated Burgers")
        )
        assert updated.name == "Updated Burgers"

    @pytest.mark.asyncio
    async def test_update_wrong_tenant_raises(self, db: AsyncSession, H):
        svc = CategoryService(db)
        with pytest.raises(NotFoundError):
            await svc.update(
                H["cat_a"].id, H["tenant_b"].id, CategoryUpdate(name="X")
            )

    @pytest.mark.asyncio
    async def test_activate_deactivate(self, db: AsyncSession, H):
        svc = CategoryService(db)
        deactivated = await svc.deactivate(H["cat_a"].id, H["tenant_a"].id)
        assert deactivated.is_active is False

        activated = await svc.activate(H["cat_a"].id, H["tenant_a"].id)
        assert activated.is_active is True

    @pytest.mark.asyncio
    async def test_delete_makes_category_invisible(self, db: AsyncSession, H):
        svc = CategoryService(db)
        data = CategoryCreate(name="Temporary")
        created = await svc.create(H["biz_a"].id, H["tenant_a"].id, data)
        await svc.delete(created.id, H["tenant_a"].id)

        with pytest.raises(NotFoundError):
            await svc.get(created.id, H["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_delete_wrong_tenant_raises(self, db: AsyncSession, H):
        svc = CategoryService(db)
        with pytest.raises(NotFoundError):
            await svc.delete(H["cat_a"].id, H["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_inactive_category_hidden_from_list_by_default(
        self, db: AsyncSession, H
    ):
        svc = CategoryService(db)
        await svc.deactivate(H["cat_a"].id, H["tenant_a"].id)
        cats = await svc.list(H["biz_a"].id, H["tenant_a"].id)
        assert not any(c.id == H["cat_a"].id for c in cats)

    @pytest.mark.asyncio
    async def test_include_inactive_flag_shows_all(self, db: AsyncSession, H):
        svc = CategoryService(db)
        await svc.deactivate(H["cat_a"].id, H["tenant_a"].id)
        cats = await svc.list(
            H["biz_a"].id, H["tenant_a"].id, include_inactive=True
        )
        assert any(c.id == H["cat_a"].id for c in cats)


# ════════════════════════════════════════════════════════════════
# ProductService
# ════════════════════════════════════════════════════════════════

class TestProductService:

    @pytest.mark.asyncio
    async def test_create_and_get(self, db: AsyncSession, H):
        """Creating a product always seeds a zero-option default Variant (spec D1)."""
        svc = ProductService(db)
        data = ProductCreate(
            product_code="WRAP_01",
            name="Chicken Wrap",
            price=Decimal("8.50"),
            display_order=1,
        )
        created = await svc.create(H["cat_a"].id, H["tenant_a"].id, data)

        assert created.name == "Chicken Wrap"
        assert created.price == Decimal("8.50")
        assert created.product_code == "WRAP_01"
        assert created.category_id == H["cat_a"].id
        assert created.default_variant_id is not None

        fetched = await svc.get(created.id, H["tenant_a"].id)
        assert fetched.id == created.id
        assert fetched.price == Decimal("8.50")

    @pytest.mark.asyncio
    async def test_create_with_branches_and_opening_stock_in_one_call(self, db: AsyncSession, H):
        """The Add Product drawer sends branch assignment + opening stock
        atomically with creation — branch assignment must land before the
        default Variant is created so opening_stock_by_branch validates
        against the branches actually being assigned, not all_branches=True."""
        svc = ProductService(db)
        created = await svc.create(H["cat_a"].id, H["tenant_a"].id, ProductCreate(
            product_code="STOCK_01", name="Stocked Product", price=Decimal("10.00"),
            allow_inventory_tracking=True,
            all_branches=False, branch_ids=[H["branch_a"].id],
            opening_stock_by_branch={H["branch_a"].id: 25},
        ))
        assignment = await svc.get_branch_assignment(created.id, H["tenant_a"].id)
        assert assignment.all_branches is False
        assert [b.id for b in assignment.branches] == [H["branch_a"].id]

        row = await VariantService(db).get_branch_stock_row(created.default_variant_id, H["branch_a"].id)
        assert row.stock_quantity == 25

    @pytest.mark.asyncio
    async def test_create_with_priced_variant_group_seeds_one_variant_per_color(self, db: AsyncSession, H):
        """The Add Product drawer's Colors section: each checked color has
        its own full sale_price/cost_price (pre-filled from the base Price/
        Cost Price fields in the UI, editable — not a delta), seeding one
        priced, stocked combination Variant per color atomically with
        product creation."""
        from schemas.product import PricedVariantInput

        group = await VariantOptionGroupService(db).create(
            H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name=f"Colors {uuid4().hex[:6]}"),
        )
        opt_svc = VariantOptionService(db)
        red = await opt_svc.create(group.id, H["tenant_a"].id, VariantOptionCreate(name="Red"))
        gold = await opt_svc.create(group.id, H["tenant_a"].id, VariantOptionCreate(name="Gold"))

        svc = ProductService(db)
        created = await svc.create(H["cat_a"].id, H["tenant_a"].id, ProductCreate(
            product_code="LAPTOP_01", name="Laptop", price=Decimal("1000.00"),
            allow_inventory_tracking=True,
            all_branches=False, branch_ids=[H["branch_a"].id],
            priced_variant_group_id=group.id,
            priced_variants=[
                PricedVariantInput(option_id=red.id, sale_price=Decimal("1000.00"),
                                    opening_stock_by_branch={H["branch_a"].id: 3}),
                PricedVariantInput(option_id=gold.id, sale_price=Decimal("1050.00"),
                                    opening_stock_by_branch={H["branch_a"].id: 1}),
            ],
        ))

        links = await VariantOptionGroupService(db).list_for_product(created.id, H["tenant_a"].id)
        assert len(links) == 1
        assert links[0].usage_type == "specification"
        assert links[0].is_required is True

        variant_svc = VariantService(db)
        variants = (await db.scalars(
            variant_svc.scoped(H["tenant_a"].id).where(Variant.product_id == created.id)
        )).all()
        colored = {UUID(v.option_value_ids[0]): v for v in variants if v.option_value_ids}
        assert colored[red.id].sale_price == Decimal("1000.00")
        assert colored[gold.id].sale_price == Decimal("1050.00")

        red_row = await VariantService(db).get_branch_stock_row(colored[red.id].id, H["branch_a"].id)
        assert red_row.stock_quantity == 3

    @pytest.mark.asyncio
    async def test_create_with_priced_variant_group_but_no_colors_attaches_nothing(self, db: AsyncSession, H):
        """An empty priced_variants list must never attach a required group
        with zero satisfying variants — that would make the product
        permanently unsellable with no error anywhere."""
        from schemas.product import PricedVariantInput  # noqa: F401 — kept for symmetry/clarity

        group = await VariantOptionGroupService(db).create(
            H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name=f"Colors {uuid4().hex[:6]}"),
        )
        svc = ProductService(db)
        created = await svc.create(H["cat_a"].id, H["tenant_a"].id, ProductCreate(
            product_code="LAPTOP_02", name="Laptop No Colors", price=Decimal("1000.00"),
            priced_variant_group_id=group.id, priced_variants=[],
        ))
        links = await VariantOptionGroupService(db).list_for_product(created.id, H["tenant_a"].id)
        assert links == []
        assert created.has_combination_variants is False

    @pytest.mark.asyncio
    async def test_price_lock_only_fires_once_real_combination_variants_exist(self, db: AsyncSession, H):
        """An Inventory Component group leaves the base product's own price
        directly editable. A Specification-usage group only blocks it once
        it actually has a priced combination Variant (e.g. a Color) — being
        attached alone, with zero combinations, must NOT lock the price with
        no way to unlock it again (this was the exact bug in HP2100-shaped
        products the price-delta Colors feature depends on not repeating)."""
        svc = ProductService(db)
        component_product = await svc.create(H["cat_a"].id, H["tenant_a"].id, ProductCreate(
            product_code="COMP_PRICE", name="Component-only Product", price=Decimal("5.00"),
        ))
        group = await VariantOptionGroupService(db).create(
            H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name=f"Colors {uuid4().hex[:6]}"),
        )
        await VariantOptionGroupService(db).attach_to_product(
            component_product.id, H["tenant_a"].id,
            ProductVariantOptionGroupAttach(option_group_id=group.id, is_required=False),
        )
        updated = await svc.update(component_product.id, H["tenant_a"].id, ProductUpdate(price=Decimal("6.00")))
        assert updated.price == Decimal("6.00")

        spec_product = await svc.create(H["cat_a"].id, H["tenant_a"].id, ProductCreate(
            product_code="SPEC_PRICE", name="Specification Product", price=Decimal("5.00"),
        ))
        spec_group = await VariantOptionGroupService(db).create(
            H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name=f"RAM {uuid4().hex[:6]}"),
        )
        await VariantOptionGroupService(db).attach_to_product(
            spec_product.id, H["tenant_a"].id,
            ProductVariantOptionGroupAttach(option_group_id=spec_group.id, is_required=False,
                                             usage_type="specification"),
        )
        # Attached, but zero combinations yet — price stays editable.
        still_editable = await svc.update(spec_product.id, H["tenant_a"].id, ProductUpdate(price=Decimal("5.50")))
        assert still_editable.price == Decimal("5.50")

        option = await VariantOptionService(db).create(
            spec_group.id, H["tenant_a"].id, VariantOptionCreate(name="16GB"),
        )
        await VariantService(db).create(
            H["tenant_a"].id, spec_product.id, [option.id], sale_price=Decimal("7.00"),
        )
        with pytest.raises(ValidationError, match="priced Variant combinations"):
            await svc.update(spec_product.id, H["tenant_a"].id, ProductUpdate(price=Decimal("6.00")))

    @pytest.mark.asyncio
    async def test_turning_off_product_tracking_cascades_to_all_variants(self, db: AsyncSession, H):
        """Turning off allow_inventory_tracking must not silently orphan a
        variant that was already tracked — every stock check ANDs both
        flags, so a variant left at tracks_inventory=True with the product
        untracked would just stop being enforced with no visible signal,
        and "Enable tracking" would never re-offer it since the column
        already reads True. The cascade only stops tracking going forward;
        it must not delete any stock/history rows."""
        svc = ProductService(db)
        product = await svc.create(H["cat_a"].id, H["tenant_a"].id, ProductCreate(
            product_code="DRINK_01", name="Pepsi", price=Decimal("100.00"),
            allow_inventory_tracking=True,
        ))
        group = await VariantOptionGroupService(db).create(
            H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name=f"Size {uuid4().hex[:6]}"),
        )
        await VariantOptionGroupService(db).attach_to_product(
            product.id, H["tenant_a"].id,
            ProductVariantOptionGroupAttach(option_group_id=group.id, is_required=False,
                                             usage_type="specification"),
        )
        half_litre = await VariantOptionService(db).create(
            group.id, H["tenant_a"].id, VariantOptionCreate(name="500ml"),
        )
        litre = await VariantOptionService(db).create(
            group.id, H["tenant_a"].id, VariantOptionCreate(name="1L"),
        )
        v1 = await VariantService(db).create(
            H["tenant_a"].id, product.id, [half_litre.id], sale_price=Decimal("100.00"),
            tracks_inventory=True, opening_stock_by_branch={H["branch_a"].id: 10},
        )
        v2 = await VariantService(db).create(
            H["tenant_a"].id, product.id, [litre.id], sale_price=Decimal("180.00"),
            tracks_inventory=True, opening_stock_by_branch={H["branch_a"].id: 5},
        )

        await svc.update(product.id, H["tenant_a"].id, ProductUpdate(allow_inventory_tracking=False))

        refreshed_v1 = await db.get(Variant, v1.id)
        refreshed_v2 = await db.get(Variant, v2.id)
        assert refreshed_v1.tracks_inventory is False
        assert refreshed_v2.tracks_inventory is False

        # History is preserved, not deleted, by the cascade.
        from sqlalchemy import select as sa_select
        from models.variant_branch_stock import VariantBranchStock
        stock_row = await db.scalar(
            sa_select(VariantBranchStock).where(VariantBranchStock.variant_id == v1.id)
        )
        assert stock_row is not None
        assert stock_row.stock_quantity == 10

    @pytest.mark.asyncio
    async def test_get_wrong_tenant_raises(self, db: AsyncSession, H):
        svc = ProductService(db)
        with pytest.raises(NotFoundError):
            await svc.get(H["prod_a"].id, H["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_create_under_wrong_tenant_category_raises(
        self, db: AsyncSession, H
    ):
        svc = ProductService(db)
        data = ProductCreate(
            product_code="BAD_01", name="Bad Product", price=Decimal("1.00")
        )
        with pytest.raises(NotFoundError):
            await svc.create(H["cat_b"].id, H["tenant_a"].id, data)

    @pytest.mark.asyncio
    async def test_list_scoped_to_category(self, db: AsyncSession, H):
        svc = ProductService(db)
        products = await svc.list(H["cat_a"].id, H["tenant_a"].id)
        ids = [p.id for p in products]
        assert H["prod_a"].id in ids
        assert H["prod_b"].id not in ids

    @pytest.mark.asyncio
    async def test_list_cross_tenant_category_raises(self, db: AsyncSession, H):
        svc = ProductService(db)
        with pytest.raises(NotFoundError):
            await svc.list(H["cat_b"].id, H["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_update_price_via_default_variant(self, db: AsyncSession, H):
        """There is no Product.price to PATCH — price lives on the default
        Variant's sale_price (spec D1); ProductResponse.price is a read-through."""
        prod_svc = ProductService(db)
        variant_svc = VariantService(db)

        variant = await variant_svc.get(H["tenant_a"].id, H["prod_a"].default_variant_id)
        variant.sale_price = Decimal("11.99")
        await db.flush()

        updated = await prod_svc.get(H["prod_a"].id, H["tenant_a"].id)
        assert updated.price == Decimal("11.99")

    @pytest.mark.asyncio
    async def test_update_name_wrong_tenant_raises(self, db: AsyncSession, H):
        svc = ProductService(db)
        with pytest.raises(NotFoundError):
            await svc.update(
                H["prod_a"].id, H["tenant_b"].id, ProductUpdate(name="X")
            )

    @pytest.mark.asyncio
    async def test_activate_deactivate(self, db: AsyncSession, H):
        svc = ProductService(db)
        deactivated = await svc.deactivate(H["prod_a"].id, H["tenant_a"].id)
        assert deactivated.is_active is False

        activated = await svc.activate(H["prod_a"].id, H["tenant_a"].id)
        assert activated.is_active is True

    @pytest.mark.asyncio
    async def test_inactive_product_hidden_from_list(self, db: AsyncSession, H):
        svc = ProductService(db)
        await svc.deactivate(H["prod_a"].id, H["tenant_a"].id)
        products = await svc.list(H["cat_a"].id, H["tenant_a"].id)
        assert not any(p.id == H["prod_a"].id for p in products)

    @pytest.mark.asyncio
    async def test_include_inactive_flag(self, db: AsyncSession, H):
        svc = ProductService(db)
        await svc.deactivate(H["prod_a"].id, H["tenant_a"].id)
        products = await svc.list(
            H["cat_a"].id, H["tenant_a"].id, include_inactive=True
        )
        assert any(p.id == H["prod_a"].id for p in products)

    @pytest.mark.asyncio
    async def test_delete_makes_product_invisible(self, db: AsyncSession, H):
        svc = ProductService(db)
        data = ProductCreate(
            product_code="DEL_01", name="To Delete", price=Decimal("5.00")
        )
        created = await svc.create(H["cat_a"].id, H["tenant_a"].id, data)
        await svc.delete(created.id, H["tenant_a"].id)
        with pytest.raises(NotFoundError):
            await svc.get(created.id, H["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_delete_wrong_tenant_raises(self, db: AsyncSession, H):
        svc = ProductService(db)
        with pytest.raises(NotFoundError):
            await svc.delete(H["prod_a"].id, H["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_generate_sku_uses_category_prefix(self, db: AsyncSession, H):
        """H["cat_a"] is named "Burgers" and none of its seeded products carry
        a sku, so the first suggestion should be the category-prefixed seq 1."""
        svc = ProductService(db)
        sku = await svc.generate_sku(H["cat_a"].id, H["tenant_a"].id)
        assert sku == "BUR-0001"

    @pytest.mark.asyncio
    async def test_generate_sku_skips_existing_collision(self, db: AsyncSession, H):
        svc = ProductService(db)
        await svc.create(H["cat_a"].id, H["tenant_a"].id, ProductCreate(
            product_code="SKU_TAKEN", name="Already has BUR-0001",
            price=Decimal("1.00"), sku="BUR-0001",
        ))
        sku = await svc.generate_sku(H["cat_a"].id, H["tenant_a"].id)
        assert sku == "BUR-0002"

    @pytest.mark.asyncio
    async def test_generate_sku_wrong_tenant_category_raises(self, db: AsyncSession, H):
        svc = ProductService(db)
        with pytest.raises(NotFoundError):
            await svc.generate_sku(H["cat_b"].id, H["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_generate_sku_scoped_per_business_not_just_category(self, db: AsyncSession, H):
        """Two different categories in the same business sharing a 3-letter
        prefix must not collide with each other's sequence."""
        from models.category import Category
        from uuid import uuid4
        other_cat = Category(id=uuid4(), business_id=H["biz_a"].id, name="Burritos", is_active=True)
        db.add(other_cat)
        await db.flush()
        svc = ProductService(db)
        first = await svc.generate_sku(H["cat_a"].id, H["tenant_a"].id)
        assert first == "BUR-0001"
        await svc.create(H["cat_a"].id, H["tenant_a"].id, ProductCreate(
            product_code="SKU_SCOPE_1", name="First", price=Decimal("1.00"), sku=first,
        ))
        # A different category with the same 3-letter prefix continues the
        # shared BUR- count instead of restarting at 0001.
        second = await svc.generate_sku(other_cat.id, H["tenant_a"].id)
        assert second == "BUR-0002"


# ════════════════════════════════════════════════════════════════
# VariantOptionGroupService — single-select, shared at Business level
# ════════════════════════════════════════════════════════════════

class TestVariantOptionGroupService:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("name", ["Color", " colors ", "COLOUR", "Colours"])
    async def test_color_names_are_allowed_as_variant_groups(self, db: AsyncSession, H, name):
        # Colors now join the same shareable Variant Option Group / Inventory
        # Component mechanism as RAM/Storage instead of being separate
        # product-level metadata — a group literally named "Color(s)" is no
        # longer special-cased or rejected.
        created = await VariantOptionGroupService(db).create(
            H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name=name),
        )
        assert created.name == name

    @pytest.mark.asyncio
    async def test_create_and_get(self, db: AsyncSession, H):
        svc = VariantOptionGroupService(db)
        data = VariantOptionGroupCreate(name="Crust")
        created = await svc.create(H["biz_a"].id, H["tenant_a"].id, data)

        assert created.name == "Crust"
        assert created.business_id == H["biz_a"].id
        assert created.is_active is True

        fetched = await svc.get(created.id, H["tenant_a"].id)
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_get_wrong_tenant_raises(self, db: AsyncSession, H):
        svc = VariantOptionGroupService(db)
        with pytest.raises(NotFoundError):
            await svc.get(H["og_a"].id, H["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_create_under_wrong_tenant_business_raises(
        self, db: AsyncSession, H
    ):
        svc = VariantOptionGroupService(db)
        with pytest.raises(NotFoundError):
            await svc.create(
                H["biz_b"].id, H["tenant_a"].id, VariantOptionGroupCreate(name="X")
            )

    @pytest.mark.asyncio
    async def test_list_scoped_to_business(self, db: AsyncSession, H):
        svc = VariantOptionGroupService(db)
        groups = await svc.list(H["biz_a"].id, H["tenant_a"].id)
        ids = [g.id for g in groups]
        assert H["og_a"].id in ids
        assert H["og_b"].id not in ids

    @pytest.mark.asyncio
    async def test_list_cross_tenant_business_raises(self, db: AsyncSession, H):
        svc = VariantOptionGroupService(db)
        with pytest.raises(NotFoundError):
            await svc.list(H["biz_b"].id, H["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_update_name(self, db: AsyncSession, H):
        svc = VariantOptionGroupService(db)
        updated = await svc.update(
            H["og_a"].id, H["tenant_a"].id, VariantOptionGroupUpdate(name="Size Updated"),
        )
        assert updated.name == "Size Updated"

    @pytest.mark.asyncio
    async def test_existing_variant_group_can_be_renamed_to_color(self, db: AsyncSession, H):
        updated = await VariantOptionGroupService(db).update(
            H["og_a"].id, H["tenant_a"].id, VariantOptionGroupUpdate(name="Color"),
        )
        assert updated.name == "Color"

    @pytest.mark.asyncio
    async def test_update_wrong_tenant_raises(self, db: AsyncSession, H):
        svc = VariantOptionGroupService(db)
        with pytest.raises(NotFoundError):
            await svc.update(
                H["og_a"].id, H["tenant_b"].id, VariantOptionGroupUpdate(name="X")
            )

    @pytest.mark.asyncio
    async def test_activate_deactivate(self, db: AsyncSession, H):
        svc = VariantOptionGroupService(db)
        deactivated = await svc.deactivate(H["og_a"].id, H["tenant_a"].id)
        assert deactivated.is_active is False

        activated = await svc.activate(H["og_a"].id, H["tenant_a"].id)
        assert activated.is_active is True

    @pytest.mark.asyncio
    async def test_delete_makes_group_invisible(self, db: AsyncSession, H):
        svc = VariantOptionGroupService(db)
        created = await svc.create(
            H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name="Temp Group")
        )
        await svc.delete(created.id, H["tenant_a"].id)
        with pytest.raises(NotFoundError):
            await svc.get(created.id, H["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_attach_to_product_and_list_for_product(self, db: AsyncSession, H):
        svc = VariantOptionGroupService(db)
        group = await svc.create(H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name="Crust"))
        attached = await svc.attach_to_product(
            H["prod_a"].id, H["tenant_a"].id,
            ProductVariantOptionGroupAttach(option_group_id=group.id, is_required=True),
        )
        assert attached.option_group_id == group.id

        links = await svc.list_for_product(H["prod_a"].id, H["tenant_a"].id)
        # prod_a already has og_a attached via the H fixture, plus this new one.
        group_ids = [link.option_group_id for link in links]
        assert group.id in group_ids
        assert H["og_a"].id in group_ids

    @pytest.mark.asyncio
    async def test_attach_wrong_tenant_product_raises(self, db: AsyncSession, H):
        svc = VariantOptionGroupService(db)
        group = await svc.create(H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name="Crust"))
        with pytest.raises(NotFoundError):
            await svc.attach_to_product(
                H["prod_b"].id, H["tenant_a"].id,
                ProductVariantOptionGroupAttach(option_group_id=group.id),
            )

    @pytest.mark.asyncio
    async def test_detach_unused_group_succeeds_even_though_product_has_other_variants(self, db: AsyncSession, H):
        """A product always has at least its zero-option default Variant
        (spec D1) — that alone must never block detaching a group whose own
        options no live Variant actually references (e.g. attached, then
        never used to create anything). Only a group actually in use should
        block detachment."""
        svc = VariantOptionGroupService(db)
        group = await svc.create(H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name="Unused"))
        attached = await svc.attach_to_product(
            H["prod_a"].id, H["tenant_a"].id,
            ProductVariantOptionGroupAttach(option_group_id=group.id, is_required=True),
        )
        # prod_a already has a real Variant (H["variant_a"]) from the fixture,
        # referencing a DIFFERENT group's option — this must not block.
        await svc.detach_from_product(H["prod_a"].id, H["tenant_a"].id, attached.id)
        links = await svc.list_for_product(H["prod_a"].id, H["tenant_a"].id)
        assert group.id not in [link.option_group_id for link in links]

    @pytest.mark.asyncio
    async def test_detach_group_actually_in_use_is_blocked(self, db: AsyncSession, H):
        svc = VariantOptionGroupService(db)
        with pytest.raises(ConflictError, match="Remove this product's variants"):
            await svc.detach_from_product(H["prod_a"].id, H["tenant_a"].id, H["pvog_a"].id)


# ════════════════════════════════════════════════════════════════
# VariantOptionService — no price field (spec D1: pricing lives on Variant)
# ════════════════════════════════════════════════════════════════

class TestVariantOptionService:

    @pytest.mark.asyncio
    async def test_create_and_get(self, db: AsyncSession, H):
        svc = VariantOptionService(db)
        data = VariantOptionCreate(name="Extra Large", display_order=1)
        created = await svc.create(H["og_a"].id, H["tenant_a"].id, data)

        assert created.name == "Extra Large"
        assert created.option_group_id == H["og_a"].id

        fetched = await svc.get(created.id, H["tenant_a"].id)
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_get_wrong_tenant_raises(self, db: AsyncSession, H):
        svc = VariantOptionService(db)
        with pytest.raises(NotFoundError):
            await svc.get(H["opt_a"].id, H["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_create_under_wrong_tenant_group_raises(
        self, db: AsyncSession, H
    ):
        svc = VariantOptionService(db)
        with pytest.raises(NotFoundError):
            await svc.create(
                H["og_b"].id, H["tenant_a"].id, VariantOptionCreate(name="X")
            )

    @pytest.mark.asyncio
    async def test_list_scoped_to_option_group(self, db: AsyncSession, H):
        svc = VariantOptionService(db)
        options = await svc.list(H["og_a"].id, H["tenant_a"].id)
        ids = [o.id for o in options]
        assert H["opt_a"].id in ids
        assert H["opt_b"].id not in ids

    @pytest.mark.asyncio
    async def test_list_cross_tenant_group_raises(self, db: AsyncSession, H):
        svc = VariantOptionService(db)
        with pytest.raises(NotFoundError):
            await svc.list(H["og_b"].id, H["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_update_name(self, db: AsyncSession, H):
        svc = VariantOptionService(db)
        updated = await svc.update(
            H["opt_a"].id, H["tenant_a"].id, VariantOptionUpdate(name="Renamed"),
        )
        assert updated.name == "Renamed"

    @pytest.mark.asyncio
    async def test_update_wrong_tenant_raises(self, db: AsyncSession, H):
        svc = VariantOptionService(db)
        with pytest.raises(NotFoundError):
            await svc.update(
                H["opt_a"].id, H["tenant_b"].id, VariantOptionUpdate(name="X")
            )

    @pytest.mark.asyncio
    async def test_activate_deactivate(self, db: AsyncSession, H):
        svc = VariantOptionService(db)
        deactivated = await svc.deactivate(H["opt_a"].id, H["tenant_a"].id)
        assert deactivated.is_active is False

        activated = await svc.activate(H["opt_a"].id, H["tenant_a"].id)
        assert activated.is_active is True

    @pytest.mark.asyncio
    async def test_delete_makes_option_invisible(self, db: AsyncSession, H):
        svc = VariantOptionService(db)
        created = await svc.create(
            H["og_a"].id, H["tenant_a"].id, VariantOptionCreate(name="Temp Option"),
        )
        await svc.delete(created.id, H["tenant_a"].id)
        with pytest.raises(NotFoundError):
            await svc.get(created.id, H["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_delete_wrong_tenant_raises(self, db: AsyncSession, H):
        svc = VariantOptionService(db)
        with pytest.raises(NotFoundError):
            await svc.delete(H["opt_a"].id, H["tenant_b"].id)


# ════════════════════════════════════════════════════════════════
# AddonGroupService — multi-select, price-delta, never generates SKUs
# ════════════════════════════════════════════════════════════════

class TestAddonGroupService:

    @pytest.mark.asyncio
    async def test_create_and_get(self, db: AsyncSession, H):
        svc = AddonGroupService(db)
        data = AddonGroupCreate(name="Toppings", selection_type="multiple", min_select=0, max_select=3)
        created = await svc.create(H["biz_a"].id, H["tenant_a"].id, data)

        assert created.name == "Toppings"
        assert created.selection_type == "multiple"
        assert created.max_select == 3
        assert created.business_id == H["biz_a"].id

        fetched = await svc.get(created.id, H["tenant_a"].id)
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_min_greater_than_max_rejected_by_schema(self):
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            AddonGroupCreate(name="Bad", min_select=3, max_select=1)

    @pytest.mark.asyncio
    async def test_get_wrong_tenant_raises(self, db: AsyncSession, H):
        svc = AddonGroupService(db)
        group = await svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Sauces"))
        with pytest.raises(NotFoundError):
            await svc.get(group.id, H["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_create_under_wrong_tenant_business_raises(
        self, db: AsyncSession, H
    ):
        svc = AddonGroupService(db)
        with pytest.raises(NotFoundError):
            await svc.create(H["biz_b"].id, H["tenant_a"].id, AddonGroupCreate(name="X"))

    @pytest.mark.asyncio
    async def test_list_scoped_to_business(self, db: AsyncSession, H):
        svc = AddonGroupService(db)
        a = await svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="A Group"))
        groups = await svc.list(H["biz_a"].id, H["tenant_a"].id)
        assert a.id in [g.id for g in groups]

    @pytest.mark.asyncio
    async def test_update_name(self, db: AsyncSession, H):
        svc = AddonGroupService(db)
        group = await svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Old"))
        updated = await svc.update(group.id, H["tenant_a"].id, AddonGroupUpdate(name="New"))
        assert updated.name == "New"

    @pytest.mark.asyncio
    async def test_delete_makes_group_invisible(self, db: AsyncSession, H):
        svc = AddonGroupService(db)
        group = await svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Temp"))
        await svc.delete(group.id, H["tenant_a"].id)
        with pytest.raises(NotFoundError):
            await svc.get(group.id, H["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_attach_to_product_and_list_for_product(self, db: AsyncSession, H):
        svc = AddonGroupService(db)
        group = await svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Toppings"))
        attached = await svc.attach_to_product(
            H["prod_a"].id, H["tenant_a"].id,
            ProductAddonGroupAttach(addon_group_id=group.id),
        )
        assert attached.addon_group_id == group.id

        links = await svc.list_for_product(H["prod_a"].id, H["tenant_a"].id)
        assert group.id in [link.addon_group_id for link in links]

    @pytest.mark.asyncio
    async def test_attach_twice_raises_conflict(self, db: AsyncSession, H):
        from core.exceptions import ConflictError
        svc = AddonGroupService(db)
        group = await svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Toppings"))
        await svc.attach_to_product(
            H["prod_a"].id, H["tenant_a"].id, ProductAddonGroupAttach(addon_group_id=group.id),
        )
        with pytest.raises(ConflictError):
            await svc.attach_to_product(
                H["prod_a"].id, H["tenant_a"].id, ProductAddonGroupAttach(addon_group_id=group.id),
            )

    @pytest.mark.asyncio
    async def test_attach_wrong_tenant_product_raises(self, db: AsyncSession, H):
        svc = AddonGroupService(db)
        group = await svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Toppings"))
        with pytest.raises(NotFoundError):
            await svc.attach_to_product(
                H["prod_b"].id, H["tenant_a"].id, ProductAddonGroupAttach(addon_group_id=group.id),
            )


# ════════════════════════════════════════════════════════════════
# AddonItemService — priced, multi-select-eligible items
# ════════════════════════════════════════════════════════════════

class TestAddonItemService:

    @pytest.mark.asyncio
    async def test_create_and_get(self, db: AsyncSession, H):
        group_svc = AddonGroupService(db)
        item_svc = AddonItemService(db)
        group = await group_svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Toppings"))

        data = AddonItemCreate(name="Extra Cheese", price_delta=Decimal("2.50"), display_order=1)
        created = await item_svc.create(group.id, H["tenant_a"].id, data)

        assert created.name == "Extra Cheese"
        assert created.price_delta == Decimal("2.50")
        assert created.addon_group_id == group.id

        fetched = await item_svc.get(created.id, H["tenant_a"].id)
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_get_wrong_tenant_raises(self, db: AsyncSession, H):
        group_svc = AddonGroupService(db)
        item_svc = AddonItemService(db)
        group = await group_svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Toppings"))
        item = await item_svc.create(group.id, H["tenant_a"].id, AddonItemCreate(name="Bacon"))
        with pytest.raises(NotFoundError):
            await item_svc.get(item.id, H["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_create_under_wrong_tenant_group_raises(self, db: AsyncSession, H):
        group_svc = AddonGroupService(db)
        item_svc = AddonItemService(db)
        group = await group_svc.create(H["biz_b"].id, H["tenant_b"].id, AddonGroupCreate(name="Toppings"))
        with pytest.raises(NotFoundError):
            await item_svc.create(group.id, H["tenant_a"].id, AddonItemCreate(name="X"))

    @pytest.mark.asyncio
    async def test_list_scoped_to_addon_group(self, db: AsyncSession, H):
        group_svc = AddonGroupService(db)
        item_svc = AddonItemService(db)
        group = await group_svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Toppings"))
        item = await item_svc.create(group.id, H["tenant_a"].id, AddonItemCreate(name="Olives"))
        items = await item_svc.list(group.id, H["tenant_a"].id)
        assert item.id in [i.id for i in items]

    @pytest.mark.asyncio
    async def test_update_price_delta(self, db: AsyncSession, H):
        group_svc = AddonGroupService(db)
        item_svc = AddonItemService(db)
        group = await group_svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Toppings"))
        item = await item_svc.create(group.id, H["tenant_a"].id, AddonItemCreate(name="Bacon", price_delta=Decimal("1.00")))
        updated = await item_svc.update(item.id, H["tenant_a"].id, AddonItemUpdate(price_delta=Decimal("3.00")))
        assert updated.price_delta == Decimal("3.00")

    @pytest.mark.asyncio
    async def test_update_wrong_tenant_raises(self, db: AsyncSession, H):
        group_svc = AddonGroupService(db)
        item_svc = AddonItemService(db)
        group = await group_svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Toppings"))
        item = await item_svc.create(group.id, H["tenant_a"].id, AddonItemCreate(name="Bacon"))
        with pytest.raises(NotFoundError):
            await item_svc.update(item.id, H["tenant_b"].id, AddonItemUpdate(name="X"))

    @pytest.mark.asyncio
    async def test_default_selected_flag(self, db: AsyncSession, H):
        group_svc = AddonGroupService(db)
        item_svc = AddonItemService(db)
        group = await group_svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Toppings"))
        item = await item_svc.create(
            group.id, H["tenant_a"].id, AddonItemCreate(name="Lettuce", default_selected=True),
        )
        assert item.default_selected is True

    @pytest.mark.asyncio
    async def test_delete_makes_item_invisible(self, db: AsyncSession, H):
        group_svc = AddonGroupService(db)
        item_svc = AddonItemService(db)
        group = await group_svc.create(H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Toppings"))
        item = await item_svc.create(group.id, H["tenant_a"].id, AddonItemCreate(name="Temp"))
        await item_svc.delete(item.id, H["tenant_a"].id)
        with pytest.raises(NotFoundError):
            await item_svc.get(item.id, H["tenant_a"].id)


# ════════════════════════════════════════════════════════════════
# Full hierarchy relationship tests
# ════════════════════════════════════════════════════════════════

class TestMenuHierarchyRelationships:
    """
    Verifies the full chain can be built via services: category → product →
    Variant Option Group (single-select) with Variant Options, plus an
    independently-attached Add-on Group (multi-select) with priced items —
    confirming the two systems never interfere with each other (spec A1/D4).
    """

    @pytest.mark.asyncio
    async def test_full_chain_create_and_traverse(self, db: AsyncSession, H):
        cat_svc = CategoryService(db)
        prod_svc = ProductService(db)
        vog_svc = VariantOptionGroupService(db)
        vopt_svc = VariantOptionService(db)
        addon_group_svc = AddonGroupService(db)
        addon_item_svc = AddonItemService(db)

        # Category
        cat = await cat_svc.create(
            H["biz_a"].id, H["tenant_a"].id, CategoryCreate(name="Drinks")
        )

        # Product under category (zero-option default variant seeded automatically)
        prod = await prod_svc.create(
            cat.id,
            H["tenant_a"].id,
            ProductCreate(
                product_code="SHAKE_01",
                name="Milkshake",
                price=Decimal("6.00"),
            ),
        )

        # Variant Option Group (single-select) attached to the product
        vog = await vog_svc.create(
            H["biz_a"].id, H["tenant_a"].id, VariantOptionGroupCreate(name="Flavour"),
        )
        from schemas.variant_option_group import ProductVariantOptionGroupAttach
        await vog_svc.attach_to_product(
            prod.id, H["tenant_a"].id,
            ProductVariantOptionGroupAttach(option_group_id=vog.id, is_required=True),
        )
        opt1 = await vopt_svc.create(vog.id, H["tenant_a"].id, VariantOptionCreate(name="Chocolate"))
        opt2 = await vopt_svc.create(vog.id, H["tenant_a"].id, VariantOptionCreate(name="Vanilla"))

        # Add-on Group (multi-select, priced) attached to the same product —
        # structurally independent of the Variant Option Group above.
        addons = await addon_group_svc.create(
            H["biz_a"].id, H["tenant_a"].id, AddonGroupCreate(name="Extras", selection_type="multiple"),
        )
        await addon_group_svc.attach_to_product(
            prod.id, H["tenant_a"].id, ProductAddonGroupAttach(addon_group_id=addons.id),
        )
        await addon_item_svc.create(
            addons.id, H["tenant_a"].id, AddonItemCreate(name="Whipped Cream", price_delta=Decimal("1.00")),
        )

        # Traverse back via the services
        vog_links = await vog_svc.list_for_product(prod.id, H["tenant_a"].id)
        assert vog.id in [link.option_group_id for link in vog_links]

        options = await vopt_svc.list(vog.id, H["tenant_a"].id)
        opt_names = {o.name for o in options}
        assert "Chocolate" in opt_names
        assert "Vanilla" in opt_names

        addon_links = await addon_group_svc.list_for_product(prod.id, H["tenant_a"].id)
        assert addons.id in [link.addon_group_id for link in addon_links]

        addon_items = await addon_item_svc.list(addons.id, H["tenant_a"].id)
        assert {i.name for i in addon_items} == {"Whipped Cream"}

        # The Add-on Group must never appear in the product's Variant Option
        # Group listing, and vice versa — the two systems are structurally
        # separate (spec A1).
        assert addons.id not in [link.option_group_id for link in vog_links]

    @pytest.mark.asyncio
    async def test_cross_tenant_cannot_add_option_to_other_tenant_group(
        self, db: AsyncSession, H
    ):
        """Tenant A cannot add a Variant Option to Tenant B's option group."""
        svc = VariantOptionService(db)
        with pytest.raises(NotFoundError):
            await svc.create(
                H["og_b"].id,
                H["tenant_a"].id,
                VariantOptionCreate(name="Infiltrate"),
            )

    @pytest.mark.asyncio
    async def test_cross_tenant_cannot_add_group_to_other_tenant_business(
        self, db: AsyncSession, H
    ):
        """Tenant A cannot create a Variant Option Group under Tenant B's business."""
        svc = VariantOptionGroupService(db)
        with pytest.raises(NotFoundError):
            await svc.create(
                H["biz_b"].id,
                H["tenant_a"].id,
                VariantOptionGroupCreate(name="Infiltrate"),
            )

    @pytest.mark.asyncio
    async def test_cross_tenant_cannot_add_product_to_other_tenant_category(
        self, db: AsyncSession, H
    ):
        """Tenant A cannot add a product to Tenant B's category."""
        svc = ProductService(db)
        with pytest.raises(NotFoundError):
            await svc.create(
                H["cat_b"].id,
                H["tenant_a"].id,
                ProductCreate(
                    product_code="INF_01",
                    name="Infiltrate",
                    price=Decimal("1.00"),
                ),
            )
