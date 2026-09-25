# tests/test_branch_assignment.py
#
# Tests the branch assignment feature for products, deals, promotions, and users.
#
# Core invariants verified:
#   1. New entities default to all_branches=True (no join rows needed).
#   2. Assigning specific branches sets all_branches=False + join rows.
#   3. Switching back to all_branches clears join rows.
#   4. Tenant isolation: service raises 404 when entity belongs to another tenant.
#   5. Branch isolation: branches from tenant B cannot interfere with tenant A data.

from __future__ import annotations

import pytest
import pytest_asyncio
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError
from core.security import hash_password
from models.branch import Branch
from models.business import Business
from models.business_template import BusinessTemplate
from models.category import Category
from models.deal import Deal
from models.deal_item import DealItem
from models.product import Product
from models.promotion import Promotion
from models.tenant import Tenant
from models.user import User
from services.deal_service import DealService
from services.product_service import ProductService
from services.promotion_service import PromotionService
from services.user_service import UserService


# ── Fixture: two tenants, each with 2 branches ───────────────

@pytest_asyncio.fixture
async def BA(db: AsyncSession):
    """
    Branch-assignment test hierarchy.

    Tenant A                    Tenant B
    ├─ Business A               ├─ Business B
    │  ├─ Branch A1 (primary)   │  ├─ Branch B1
    │  └─ Branch A2 (second)    │  └─ Branch B2
    ├─ Category A               ├─ Category B
    ├─ Product A                ├─ Product B
    ├─ Promotion A              ├─ Promotion B
    ├─ Deal A                   ├─ Deal B
    └─ User A                   └─ User B
    """
    hashed = hash_password("pass123")

    tpl = BusinessTemplate(id=uuid4(), name=f"BA Template {uuid4().hex[:8]}", config={})
    db.add(tpl)
    await db.flush()

    tenant_a = Tenant(id=uuid4(), name="Alpha", tenant_code="BA_ALPHA", is_active=True, business_template_id=tpl.id)
    tenant_b = Tenant(id=uuid4(), name="Beta",  tenant_code="BA_BETA",  is_active=True, business_template_id=tpl.id)
    db.add_all([tenant_a, tenant_b])

    biz_a = Business(id=uuid4(), tenant_id=tenant_a.id, name="Business A", is_active=True)
    biz_b = Business(id=uuid4(), tenant_id=tenant_b.id, name="Business B", is_active=True)
    db.add_all([biz_a, biz_b])

    branch_a1 = Branch(id=uuid4(), business_id=biz_a.id, branch_code="BA1", name="Alpha Branch 1", is_active=True)
    branch_a2 = Branch(id=uuid4(), business_id=biz_a.id, branch_code="BA2", name="Alpha Branch 2", is_active=True)
    branch_b1 = Branch(id=uuid4(), business_id=biz_b.id, branch_code="BB1", name="Beta Branch 1",  is_active=True)
    branch_b2 = Branch(id=uuid4(), business_id=biz_b.id, branch_code="BB2", name="Beta Branch 2",  is_active=True)
    db.add_all([branch_a1, branch_a2, branch_b1, branch_b2])

    cat_a = Category(id=uuid4(), business_id=biz_a.id, name="Burgers", display_order=0, is_active=True)
    cat_b = Category(id=uuid4(), business_id=biz_b.id, name="Pizzas",  display_order=0, is_active=True)
    db.add_all([cat_a, cat_b])

    prod_a = Product(id=uuid4(), category_id=cat_a.id, product_code="PA",
                     name="Burger", display_order=0, is_active=True)
    prod_b = Product(id=uuid4(), category_id=cat_b.id, product_code="PB",
                     name="Pizza",  display_order=0, is_active=True)
    db.add_all([prod_a, prod_b])

    promo_a = Promotion(id=uuid4(), tenant_id=tenant_a.id, name="10% Off", type="PERCENTAGE",
                        discount_value=Decimal("10.00"), is_active=True)
    promo_b = Promotion(id=uuid4(), tenant_id=tenant_b.id, name="Beta 5%", type="PERCENTAGE",
                        discount_value=Decimal("5.00"),  is_active=True)
    db.add_all([promo_a, promo_b])

    deal_a = Deal(id=uuid4(), tenant_id=tenant_a.id, name="Alpha Meal", deal_code="MEAL_A", is_active=True)
    deal_b = Deal(id=uuid4(), tenant_id=tenant_b.id, name="Beta Combo", deal_code="COMBO_B", is_active=True)
    db.add_all([deal_a, deal_b])

    user_a = User(id=uuid4(), tenant_id=tenant_a.id, username="alice",
                  full_name="Alice A", password_hash=hashed, is_active=True)
    user_b = User(id=uuid4(), tenant_id=tenant_b.id, username="bob",
                  full_name="Bob B",   password_hash=hashed, is_active=True)
    db.add_all([user_a, user_b])

    await db.flush()

    yield dict(
        tenant_a=tenant_a, tenant_b=tenant_b,
        branch_a1=branch_a1, branch_a2=branch_a2,
        branch_b1=branch_b1, branch_b2=branch_b2,
        prod_a=prod_a, prod_b=prod_b,
        promo_a=promo_a, promo_b=promo_b,
        deal_a=deal_a, deal_b=deal_b,
        user_a=user_a, user_b=user_b,
        cat_a=cat_a,
    )


# ══════════════════════════════════════════════════════════════
# Product branch assignment
# ══════════════════════════════════════════════════════════════

class TestProductBranchAssignment:

    @pytest.mark.asyncio
    async def test_new_product_defaults_to_all_branches(self, db, BA):
        """Products are created with all_branches=True (available everywhere)."""
        assert BA["prod_a"].all_branches is True

    @pytest.mark.asyncio
    async def test_get_all_branches_returns_empty_list(self, db, BA):
        """When all_branches=True the branch list is empty (no restriction rows)."""
        svc = ProductService(db)
        result = await svc.get_branch_assignment(BA["prod_a"].id, BA["tenant_a"].id)
        assert result.all_branches is True
        assert result.branches == []

    @pytest.mark.asyncio
    async def test_set_specific_branches(self, db, BA):
        """Setting specific branches flips all_branches=False and returns those branches."""
        svc = ProductService(db)
        branch_ids = [BA["branch_a1"].id, BA["branch_a2"].id]
        result = await svc.set_branch_assignment(
            BA["prod_a"].id, BA["tenant_a"].id, all_branches=False, branch_ids=branch_ids
        )
        assert result.all_branches is False
        assert len(result.branches) == 2
        returned_ids = {b.id for b in result.branches}
        assert BA["branch_a1"].id in returned_ids
        assert BA["branch_a2"].id in returned_ids

    @pytest.mark.asyncio
    async def test_get_after_set_reflects_changes(self, db, BA):
        """get_branch_assignment returns the updated state after set."""
        svc = ProductService(db)
        await svc.set_branch_assignment(
            BA["prod_a"].id, BA["tenant_a"].id,
            all_branches=False, branch_ids=[BA["branch_a1"].id]
        )
        result = await svc.get_branch_assignment(BA["prod_a"].id, BA["tenant_a"].id)
        assert result.all_branches is False
        assert len(result.branches) == 1
        assert result.branches[0].id == BA["branch_a1"].id

    @pytest.mark.asyncio
    async def test_switch_back_to_all_branches_clears_rows(self, db, BA):
        """Switching from specific to all_branches clears join table rows."""
        svc = ProductService(db)
        # First restrict to specific branch
        await svc.set_branch_assignment(
            BA["prod_a"].id, BA["tenant_a"].id,
            all_branches=False, branch_ids=[BA["branch_a1"].id]
        )
        # Then switch back to all
        result = await svc.set_branch_assignment(
            BA["prod_a"].id, BA["tenant_a"].id,
            all_branches=True, branch_ids=[]
        )
        assert result.all_branches is True
        assert result.branches == []

        # Verify get also reflects all_branches=True
        fetched = await svc.get_branch_assignment(BA["prod_a"].id, BA["tenant_a"].id)
        assert fetched.all_branches is True

    @pytest.mark.asyncio
    async def test_get_wrong_tenant_raises_not_found(self, db, BA):
        """Tenant B cannot get branch assignment for Tenant A's product."""
        svc = ProductService(db)
        with pytest.raises(NotFoundError):
            await svc.get_branch_assignment(BA["prod_a"].id, BA["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_set_wrong_tenant_raises_not_found(self, db, BA):
        """Tenant B cannot set branch assignment for Tenant A's product."""
        svc = ProductService(db)
        with pytest.raises(NotFoundError):
            await svc.set_branch_assignment(
                BA["prod_a"].id, BA["tenant_b"].id,
                all_branches=False, branch_ids=[BA["branch_b1"].id]
            )

    @pytest.mark.asyncio
    async def test_set_single_branch(self, db, BA):
        """Can restrict a product to exactly one branch."""
        svc = ProductService(db)
        result = await svc.set_branch_assignment(
            BA["prod_a"].id, BA["tenant_a"].id,
            all_branches=False, branch_ids=[BA["branch_a2"].id]
        )
        assert result.all_branches is False
        assert len(result.branches) == 1
        assert result.branches[0].branch_code == "BA2"

    @pytest.mark.asyncio
    async def test_set_all_branches_with_empty_list(self, db, BA):
        """all_branches=True with empty branch_ids is valid — no rows inserted."""
        svc = ProductService(db)
        result = await svc.set_branch_assignment(
            BA["prod_a"].id, BA["tenant_a"].id,
            all_branches=True, branch_ids=[]
        )
        assert result.all_branches is True
        assert result.branches == []

    @pytest.mark.asyncio
    async def test_reassign_replaces_previous_branches(self, db, BA):
        """Setting branches twice replaces, not appends, the join rows."""
        svc = ProductService(db)
        # First: assign branch_a1
        await svc.set_branch_assignment(
            BA["prod_a"].id, BA["tenant_a"].id,
            all_branches=False, branch_ids=[BA["branch_a1"].id]
        )
        # Then: reassign to branch_a2 only
        result = await svc.set_branch_assignment(
            BA["prod_a"].id, BA["tenant_a"].id,
            all_branches=False, branch_ids=[BA["branch_a2"].id]
        )
        assert len(result.branches) == 1
        assert result.branches[0].id == BA["branch_a2"].id


# ══════════════════════════════════════════════════════════════
# Deal branch assignment
# ══════════════════════════════════════════════════════════════

class TestDealBranchAssignment:

    @pytest.mark.asyncio
    async def test_new_deal_defaults_to_all_branches(self, db, BA):
        assert BA["deal_a"].all_branches is True

    @pytest.mark.asyncio
    async def test_set_specific_branch(self, db, BA):
        svc = DealService(db)
        result = await svc.set_branch_assignment(
            BA["deal_a"].id, BA["tenant_a"].id,
            all_branches=False, branch_ids=[BA["branch_a1"].id]
        )
        assert result.all_branches is False
        assert len(result.branches) == 1

    @pytest.mark.asyncio
    async def test_get_deal_wrong_tenant_raises(self, db, BA):
        svc = DealService(db)
        with pytest.raises(NotFoundError):
            await svc.get_branch_assignment(BA["deal_a"].id, BA["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_set_deal_wrong_tenant_raises(self, db, BA):
        svc = DealService(db)
        with pytest.raises(NotFoundError):
            await svc.set_branch_assignment(
                BA["deal_a"].id, BA["tenant_b"].id,
                all_branches=False, branch_ids=[BA["branch_b1"].id]
            )

    @pytest.mark.asyncio
    async def test_deal_two_branches_both_returned(self, db, BA):
        svc = DealService(db)
        result = await svc.set_branch_assignment(
            BA["deal_a"].id, BA["tenant_a"].id,
            all_branches=False,
            branch_ids=[BA["branch_a1"].id, BA["branch_a2"].id]
        )
        assert len(result.branches) == 2


# ══════════════════════════════════════════════════════════════
# Promotion branch assignment
# ══════════════════════════════════════════════════════════════

class TestPromotionBranchAssignment:

    @pytest.mark.asyncio
    async def test_new_promotion_defaults_to_all_branches(self, db, BA):
        assert BA["promo_a"].all_branches is True

    @pytest.mark.asyncio
    async def test_set_promotion_to_specific_branch(self, db, BA):
        svc = PromotionService(db)
        result = await svc.set_branch_assignment(
            BA["promo_a"].id, BA["tenant_a"].id,
            all_branches=False, branch_ids=[BA["branch_a1"].id]
        )
        assert result.all_branches is False
        assert result.branches[0].branch_code == "BA1"

    @pytest.mark.asyncio
    async def test_get_promotion_wrong_tenant_raises(self, db, BA):
        svc = PromotionService(db)
        with pytest.raises(NotFoundError):
            await svc.get_branch_assignment(BA["promo_a"].id, BA["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_set_promotion_wrong_tenant_raises(self, db, BA):
        svc = PromotionService(db)
        with pytest.raises(NotFoundError):
            await svc.set_branch_assignment(
                BA["promo_a"].id, BA["tenant_b"].id,
                all_branches=False, branch_ids=[BA["branch_b1"].id]
            )

    @pytest.mark.asyncio
    async def test_promotion_switch_all_then_specific(self, db, BA):
        svc = PromotionService(db)
        # Default is all
        r1 = await svc.get_branch_assignment(BA["promo_a"].id, BA["tenant_a"].id)
        assert r1.all_branches is True

        # Restrict
        r2 = await svc.set_branch_assignment(
            BA["promo_a"].id, BA["tenant_a"].id,
            all_branches=False, branch_ids=[BA["branch_a2"].id]
        )
        assert r2.all_branches is False

        # Back to all
        r3 = await svc.set_branch_assignment(
            BA["promo_a"].id, BA["tenant_a"].id,
            all_branches=True, branch_ids=[]
        )
        assert r3.all_branches is True
        assert r3.branches == []


# ══════════════════════════════════════════════════════════════
# User branch assignment
# ══════════════════════════════════════════════════════════════

class TestUserBranchAssignment:

    @pytest.mark.asyncio
    async def test_new_user_defaults_to_not_all_branches(self, db, BA):
        """Users default to all_branches=False (branch-specific by default)."""
        assert BA["user_a"].all_branches is False

    @pytest.mark.asyncio
    async def test_get_user_assignment_default_no_branches(self, db, BA):
        svc = UserService(db)
        result = await svc.get_branch_assignment(BA["user_a"].id, BA["tenant_a"].id)
        assert result.all_branches is False
        assert result.branches == []

    @pytest.mark.asyncio
    async def test_assign_user_to_specific_branch(self, db, BA):
        svc = UserService(db)
        result = await svc.set_branch_assignment(
            BA["user_a"].id, BA["tenant_a"].id,
            all_branches=False, branch_ids=[BA["branch_a1"].id]
        )
        assert result.all_branches is False
        assert len(result.branches) == 1
        assert result.branches[0].id == BA["branch_a1"].id

    @pytest.mark.asyncio
    async def test_assign_user_to_all_branches(self, db, BA):
        """Managers or owners can be assigned to all branches."""
        svc = UserService(db)
        result = await svc.set_branch_assignment(
            BA["user_a"].id, BA["tenant_a"].id,
            all_branches=True, branch_ids=[]
        )
        assert result.all_branches is True
        assert result.branches == []

    @pytest.mark.asyncio
    async def test_assign_user_to_both_branches(self, db, BA):
        svc = UserService(db)
        result = await svc.set_branch_assignment(
            BA["user_a"].id, BA["tenant_a"].id,
            all_branches=False,
            branch_ids=[BA["branch_a1"].id, BA["branch_a2"].id]
        )
        assert len(result.branches) == 2

    @pytest.mark.asyncio
    async def test_get_user_wrong_tenant_raises(self, db, BA):
        svc = UserService(db)
        with pytest.raises(NotFoundError):
            await svc.get_branch_assignment(BA["user_a"].id, BA["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_set_user_wrong_tenant_raises(self, db, BA):
        svc = UserService(db)
        with pytest.raises(NotFoundError):
            await svc.set_branch_assignment(
                BA["user_a"].id, BA["tenant_b"].id,
                all_branches=False, branch_ids=[BA["branch_b1"].id]
            )

    @pytest.mark.asyncio
    async def test_reassign_user_branch_replaces(self, db, BA):
        """Reassigning replaces previous branch assignment, no duplicates."""
        svc = UserService(db)
        await svc.set_branch_assignment(
            BA["user_a"].id, BA["tenant_a"].id,
            all_branches=False, branch_ids=[BA["branch_a1"].id]
        )
        result = await svc.set_branch_assignment(
            BA["user_a"].id, BA["tenant_a"].id,
            all_branches=False, branch_ids=[BA["branch_a2"].id]
        )
        assert len(result.branches) == 1
        assert result.branches[0].id == BA["branch_a2"].id

    @pytest.mark.asyncio
    async def test_tenant_b_user_isolated_from_tenant_a_branches(self, db, BA):
        """
        Tenant B's user cannot be seen by Tenant A — complete isolation.
        """
        svc = UserService(db)
        # Tenant A assigns their user to branch_a1
        await svc.set_branch_assignment(
            BA["user_a"].id, BA["tenant_a"].id,
            all_branches=False, branch_ids=[BA["branch_a1"].id]
        )
        # Tenant B cannot read that assignment
        with pytest.raises(NotFoundError):
            await svc.get_branch_assignment(BA["user_a"].id, BA["tenant_b"].id)
