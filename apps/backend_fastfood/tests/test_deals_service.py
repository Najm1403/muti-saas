# tests/test_deals_service.py
#
# Tests DealService: CRUD, deal_code uniqueness, item sub-CRUD,
# tenant isolation, and branch assignment.

from __future__ import annotations

import pytest
import pytest_asyncio
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError
from models.branch import Branch
from models.business import Business
from models.business_template import BusinessTemplate
from models.deal import Deal
from models.deal_item import DealItem
from models.product import Product
from models.category import Category
from models.tenant import Tenant
from schemas.deal import (
    DealCreate,
    DealItemCreate,
    DealItemUpdate,
    DealUpdate,
)
from services.deal_service import DealService


# ── Fixture ────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def DS(db: AsyncSession):
    """Two tenants, each with a business, branch, category, and product."""
    tpl = BusinessTemplate(id=uuid4(), name=f"DS Template {uuid4().hex[:8]}", config={})
    db.add(tpl)
    await db.flush()

    tenant_a = Tenant(id=uuid4(), name="DealAlpha", tenant_code="D_ALPHA", is_active=True, business_template_id=tpl.id)
    tenant_b = Tenant(id=uuid4(), name="DealBeta",  tenant_code="D_BETA",  is_active=True, business_template_id=tpl.id)
    db.add_all([tenant_a, tenant_b])

    biz_a = Business(id=uuid4(), tenant_id=tenant_a.id, name="Biz A", is_active=True)
    biz_b = Business(id=uuid4(), tenant_id=tenant_b.id, name="Biz B", is_active=True)
    db.add_all([biz_a, biz_b])

    branch_a = Branch(id=uuid4(), business_id=biz_a.id, branch_code="DB_A", name="Branch A", is_active=True)
    branch_b = Branch(id=uuid4(), business_id=biz_b.id, branch_code="DB_B", name="Branch B", is_active=True)
    db.add_all([branch_a, branch_b])

    cat_a = Category(id=uuid4(), business_id=biz_a.id, name="Cat A", display_order=0, is_active=True)
    cat_b = Category(id=uuid4(), business_id=biz_b.id, name="Cat B", display_order=0, is_active=True)
    db.add_all([cat_a, cat_b])

    prod_a = Product(id=uuid4(), category_id=cat_a.id, product_code="DP_A",
                     name="Prod A", display_order=0, is_active=True)
    prod_b = Product(id=uuid4(), category_id=cat_b.id, product_code="DP_B",
                     name="Prod B", display_order=0, is_active=True)
    db.add_all([prod_a, prod_b])

    await db.flush()
    yield dict(
        tenant_a=tenant_a, tenant_b=tenant_b,
        branch_a=branch_a, branch_b=branch_b,
        cat_a=cat_a, cat_b=cat_b,
        prod_a=prod_a, prod_b=prod_b,
    )


# ══════════════════════════════════════════════════════════════
# Deal CRUD
# ══════════════════════════════════════════════════════════════

class TestDealCRUD:

    @pytest.mark.asyncio
    async def test_create_deal(self, db, DS):
        svc = DealService(db)
        result = await svc.create(DS["tenant_a"].id, DealCreate(
            name="Meal Deal", deal_code="MEAL1", display_order=0
        ))
        assert result.id is not None
        assert result.name == "Meal Deal"
        assert result.deal_code == "MEAL1"
        assert result.tenant_id == DS["tenant_a"].id
        assert result.is_active is True
        assert result.items == []

    @pytest.mark.asyncio
    async def test_deal_code_unique_within_tenant(self, db, DS):
        """Same deal_code cannot exist twice in the same tenant."""
        svc = DealService(db)
        await svc.create(DS["tenant_a"].id, DealCreate(name="First", deal_code="DUP", display_order=0))
        with pytest.raises(ConflictError):
            await svc.create(DS["tenant_a"].id, DealCreate(name="Second", deal_code="DUP", display_order=0))

    @pytest.mark.asyncio
    async def test_same_deal_code_allowed_in_different_tenants(self, db, DS):
        """Identical deal_code is allowed across separate tenants."""
        svc = DealService(db)
        r_a = await svc.create(DS["tenant_a"].id, DealCreate(name="A Deal", deal_code="SHARED", display_order=0))
        r_b = await svc.create(DS["tenant_b"].id, DealCreate(name="B Deal", deal_code="SHARED", display_order=0))
        assert r_a.id != r_b.id

    @pytest.mark.asyncio
    async def test_get_deal(self, db, DS):
        svc = DealService(db)
        created = await svc.create(DS["tenant_a"].id, DealCreate(name="Get Me", deal_code="GET1", display_order=0))
        fetched = await svc.get(created.id, DS["tenant_a"].id)
        assert fetched.id == created.id
        assert fetched.name == "Get Me"

    @pytest.mark.asyncio
    async def test_get_wrong_tenant_raises(self, db, DS):
        svc = DealService(db)
        created = await svc.create(DS["tenant_a"].id, DealCreate(name="Private", deal_code="PV1", display_order=0))
        with pytest.raises(NotFoundError):
            await svc.get(created.id, DS["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_list_deals_scoped_to_tenant(self, db, DS):
        svc = DealService(db)
        await svc.create(DS["tenant_a"].id, DealCreate(name="A Deal", deal_code="A1", display_order=0))
        await svc.create(DS["tenant_b"].id, DealCreate(name="B Deal", deal_code="B1", display_order=0))
        deals_a = await svc.list(DS["tenant_a"].id)
        names = [d.name for d in deals_a]
        assert "A Deal" in names
        assert "B Deal" not in names

    @pytest.mark.asyncio
    async def test_update_deal(self, db, DS):
        svc = DealService(db)
        created = await svc.create(DS["tenant_a"].id, DealCreate(name="Old", deal_code="UPD1", display_order=0))
        updated = await svc.update(created.id, DS["tenant_a"].id, DealUpdate(name="Updated"))
        assert updated.name == "Updated"
        assert updated.deal_code == "UPD1"  # unchanged

    @pytest.mark.asyncio
    async def test_update_deal_wrong_tenant_raises(self, db, DS):
        svc = DealService(db)
        created = await svc.create(DS["tenant_a"].id, DealCreate(name="Mine", deal_code="MY1", display_order=0))
        with pytest.raises(NotFoundError):
            await svc.update(created.id, DS["tenant_b"].id, DealUpdate(name="Hijacked"))

    @pytest.mark.asyncio
    async def test_delete_deal_soft(self, db, DS):
        svc = DealService(db)
        created = await svc.create(DS["tenant_a"].id, DealCreate(name="Delete Me", deal_code="DEL1", display_order=0))
        await svc.delete(created.id, DS["tenant_a"].id)
        with pytest.raises(NotFoundError):
            await svc.get(created.id, DS["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_delete_wrong_tenant_raises(self, db, DS):
        svc = DealService(db)
        created = await svc.create(DS["tenant_a"].id, DealCreate(name="Mine", deal_code="MY2", display_order=0))
        with pytest.raises(NotFoundError):
            await svc.delete(created.id, DS["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_deleted_deal_absent_from_list(self, db, DS):
        svc = DealService(db)
        created = await svc.create(DS["tenant_a"].id, DealCreate(name="Gone", deal_code="GN1", display_order=0))
        await svc.delete(created.id, DS["tenant_a"].id)
        deals = await svc.list(DS["tenant_a"].id)
        assert created.id not in [d.id for d in deals]

    @pytest.mark.asyncio
    async def test_create_with_fixed_price(self, db, DS):
        svc = DealService(db)
        result = await svc.create(DS["tenant_a"].id, DealCreate(
            name="Fixed Deal", deal_code="FX1",
            fixed_price=Decimal("25.00"), display_order=0
        ))
        assert result.fixed_price == Decimal("25.00")

    @pytest.mark.asyncio
    async def test_create_with_percentage_discount(self, db, DS):
        svc = DealService(db)
        result = await svc.create(DS["tenant_a"].id, DealCreate(
            name="10% Off", deal_code="PCT1",
            discount_value=Decimal("10.00"), discount_type="PERCENTAGE", display_order=0
        ))
        assert result.discount_value == Decimal("10.00")
        assert result.discount_type == "PERCENTAGE"

    @pytest.mark.asyncio
    async def test_toggle_is_active(self, db, DS):
        svc = DealService(db)
        created = await svc.create(DS["tenant_a"].id, DealCreate(name="Active", deal_code="ACT1", display_order=0))
        updated = await svc.update(created.id, DS["tenant_a"].id, DealUpdate(is_active=False))
        assert updated.is_active is False


# ══════════════════════════════════════════════════════════════
# Deal items sub-CRUD
# ══════════════════════════════════════════════════════════════

class TestDealItems:

    @pytest.mark.asyncio
    async def test_add_item_with_product(self, db, DS):
        svc = DealService(db)
        deal = await svc.create(DS["tenant_a"].id, DealCreate(name="Meal", deal_code="ML1", display_order=0))
        item = await svc.add_item(deal.id, DS["tenant_a"].id, DealItemCreate(
            product_id=DS["prod_a"].id, quantity=1
        ))
        assert item.deal_id == deal.id
        assert item.product_id == DS["prod_a"].id
        assert item.quantity == 1
        assert item.is_free is False

    @pytest.mark.asyncio
    async def test_add_item_with_category(self, db, DS):
        svc = DealService(db)
        deal = await svc.create(DS["tenant_a"].id, DealCreate(name="Cat Deal", deal_code="CD1", display_order=0))
        item = await svc.add_item(deal.id, DS["tenant_a"].id, DealItemCreate(
            category_id=DS["cat_a"].id, quantity=2
        ))
        assert item.category_id == DS["cat_a"].id
        assert item.quantity == 2

    @pytest.mark.asyncio
    async def test_add_item_marked_as_free(self, db, DS):
        svc = DealService(db)
        deal = await svc.create(DS["tenant_a"].id, DealCreate(name="Free Item", deal_code="FI1", display_order=0))
        item = await svc.add_item(deal.id, DS["tenant_a"].id, DealItemCreate(
            product_id=DS["prod_a"].id, quantity=1, is_free=True
        ))
        assert item.is_free is True

    @pytest.mark.asyncio
    async def test_add_item_wrong_tenant_raises(self, db, DS):
        svc = DealService(db)
        deal = await svc.create(DS["tenant_a"].id, DealCreate(name="Private Deal", deal_code="PD1", display_order=0))
        with pytest.raises(NotFoundError):
            await svc.add_item(deal.id, DS["tenant_b"].id, DealItemCreate(
                product_id=DS["prod_b"].id, quantity=1
            ))

    @pytest.mark.asyncio
    async def test_items_returned_with_get(self, db, DS):
        """get() returns the deal with its items eagerly loaded."""
        svc = DealService(db)
        deal = await svc.create(DS["tenant_a"].id, DealCreate(name="With Items", deal_code="WI1", display_order=0))
        await svc.add_item(deal.id, DS["tenant_a"].id, DealItemCreate(
            product_id=DS["prod_a"].id, quantity=2
        ))
        await svc.add_item(deal.id, DS["tenant_a"].id, DealItemCreate(
            category_id=DS["cat_a"].id, quantity=1
        ))
        fetched = await svc.get(deal.id, DS["tenant_a"].id)
        assert len(fetched.items) == 2

    @pytest.mark.asyncio
    async def test_update_item_quantity(self, db, DS):
        svc = DealService(db)
        deal = await svc.create(DS["tenant_a"].id, DealCreate(name="Update Items", deal_code="UI1", display_order=0))
        item = await svc.add_item(deal.id, DS["tenant_a"].id, DealItemCreate(
            product_id=DS["prod_a"].id, quantity=1
        ))
        updated = await svc.update_item(deal.id, item.id, DS["tenant_a"].id, DealItemUpdate(quantity=3))
        assert updated.quantity == 3
        assert updated.is_free is False  # unchanged

    @pytest.mark.asyncio
    async def test_update_item_is_free(self, db, DS):
        svc = DealService(db)
        deal = await svc.create(DS["tenant_a"].id, DealCreate(name="Mark Free", deal_code="MF1", display_order=0))
        item = await svc.add_item(deal.id, DS["tenant_a"].id, DealItemCreate(
            product_id=DS["prod_a"].id, quantity=1, is_free=False
        ))
        updated = await svc.update_item(deal.id, item.id, DS["tenant_a"].id, DealItemUpdate(is_free=True))
        assert updated.is_free is True

    @pytest.mark.asyncio
    async def test_remove_item_soft_delete(self, db, DS):
        svc = DealService(db)
        deal = await svc.create(DS["tenant_a"].id, DealCreate(name="Remove Item", deal_code="RI1", display_order=0))
        item = await svc.add_item(deal.id, DS["tenant_a"].id, DealItemCreate(
            product_id=DS["prod_a"].id, quantity=1
        ))
        await svc.remove_item(deal.id, item.id, DS["tenant_a"].id)
        # After removal, deal should have no items
        fetched = await svc.get(deal.id, DS["tenant_a"].id)
        assert len(fetched.items) == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent_item_raises(self, db, DS):
        svc = DealService(db)
        deal = await svc.create(DS["tenant_a"].id, DealCreate(name="No Items", deal_code="NI1", display_order=0))
        with pytest.raises(NotFoundError):
            await svc.remove_item(deal.id, uuid4(), DS["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_update_nonexistent_item_raises(self, db, DS):
        svc = DealService(db)
        deal = await svc.create(DS["tenant_a"].id, DealCreate(name="No Items 2", deal_code="NI2", display_order=0))
        with pytest.raises(NotFoundError):
            await svc.update_item(deal.id, uuid4(), DS["tenant_a"].id, DealItemUpdate(quantity=5))


# ══════════════════════════════════════════════════════════════
# Deal branch assignment (delegates to DealService)
# ══════════════════════════════════════════════════════════════

class TestDealBranchAssignmentBusinessLogic:

    @pytest.mark.asyncio
    async def test_deal_defaults_all_branches(self, db, DS):
        svc = DealService(db)
        deal = await svc.create(DS["tenant_a"].id, DealCreate(name="Everywhere", deal_code="EV1", display_order=0))
        result = await svc.get_branch_assignment(deal.id, DS["tenant_a"].id)
        assert result.all_branches is True

    @pytest.mark.asyncio
    async def test_restrict_deal_to_one_branch(self, db, DS):
        svc = DealService(db)
        deal = await svc.create(DS["tenant_a"].id, DealCreate(name="One Branch", deal_code="OB1", display_order=0))
        result = await svc.set_branch_assignment(
            deal.id, DS["tenant_a"].id,
            all_branches=False, branch_ids=[DS["branch_a"].id]
        )
        assert result.all_branches is False
        assert len(result.branches) == 1
        assert result.branches[0].id == DS["branch_a"].id

    @pytest.mark.asyncio
    async def test_deleted_deal_branch_assignment_raises(self, db, DS):
        """Cannot get branch assignment for a soft-deleted deal."""
        svc = DealService(db)
        deal = await svc.create(DS["tenant_a"].id, DealCreate(name="Del Deal", deal_code="DD1", display_order=0))
        await svc.delete(deal.id, DS["tenant_a"].id)
        with pytest.raises(NotFoundError):
            await svc.get_branch_assignment(deal.id, DS["tenant_a"].id)
