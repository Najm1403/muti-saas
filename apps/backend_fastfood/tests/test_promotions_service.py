# tests/test_promotions_service.py
#
# Tests promotion CRUD and the evaluate() business logic.
#
# Evaluate coverage:
#   - PERCENTAGE, FLAT_AMOUNT, BXGY, FREE_ITEM discount types
#   - Auto-applied vs code-gated promotions
#   - Trigger conditions: min_qty, min_amount, trigger_product, trigger_category
#   - Validity window: valid_from / valid_until
#   - Max uses exhaustion
#   - Tenant isolation on all operations

from __future__ import annotations

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError
from models.business import Business
from models.business_template import BusinessTemplate
from models.category import Category
from models.product import Product
from models.promotion import Promotion
from models.tenant import Tenant
from schemas.promotion import (
    CartItem,
    PromotionCreate,
    PromotionEvaluateRequest,
    PromotionUpdate,
)
from services.promotion_service import PromotionService


# ── Fixture ────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def PS(db: AsyncSession):
    """Two tenants with businesses, categories, and products for evaluation tests."""
    tpl = BusinessTemplate(id=uuid4(), name=f"PS Template {uuid4().hex[:8]}", config={})
    db.add(tpl)
    await db.flush()

    tenant_a = Tenant(id=uuid4(), name="PromoAlpha", tenant_code="P_ALPHA", is_active=True, business_template_id=tpl.id)
    tenant_b = Tenant(id=uuid4(), name="PromoBeta",  tenant_code="P_BETA",  is_active=True, business_template_id=tpl.id)
    db.add_all([tenant_a, tenant_b])

    biz_a = Business(id=uuid4(), tenant_id=tenant_a.id, name="Biz A", is_active=True)
    biz_b = Business(id=uuid4(), tenant_id=tenant_b.id, name="Biz B", is_active=True)
    db.add_all([biz_a, biz_b])

    cat_a = Category(id=uuid4(), business_id=biz_a.id, name="Burgers", display_order=0, is_active=True)
    cat_b = Category(id=uuid4(), business_id=biz_b.id, name="Pizzas",  display_order=0, is_active=True)
    db.add_all([cat_a, cat_b])

    prod_a = Product(id=uuid4(), category_id=cat_a.id, product_code="PA",
                     name="Burger", display_order=0, is_active=True)
    prod_b = Product(id=uuid4(), category_id=cat_b.id, product_code="PB",
                     name="Pizza",  display_order=0, is_active=True)
    db.add_all([prod_a, prod_b])

    await db.flush()
    yield dict(
        tenant_a=tenant_a, tenant_b=tenant_b,
        cat_a=cat_a, cat_b=cat_b,
        prod_a=prod_a, prod_b=prod_b,
    )


# ── Helper ────────────────────────────────────────────────────

def make_cart(items: list[dict], promo_code: str | None = None) -> PromotionEvaluateRequest:
    cart_items = [CartItem(**i) for i in items]
    total = sum(i.unit_price * i.quantity for i in cart_items)
    return PromotionEvaluateRequest(items=cart_items, promo_code=promo_code, order_total=total)


# ══════════════════════════════════════════════════════════════
# CRUD
# ══════════════════════════════════════════════════════════════

class TestPromotionCRUD:

    @pytest.mark.asyncio
    async def test_create_promotion(self, db, PS):
        svc = PromotionService(db)
        result = await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="10% Off", type="PERCENTAGE", discount_value=Decimal("10.00")
        ))
        assert result.id is not None
        assert result.name == "10% Off"
        assert result.type == "PERCENTAGE"
        assert result.discount_value == Decimal("10.00")
        assert result.is_active is True
        assert result.tenant_id == PS["tenant_a"].id

    @pytest.mark.asyncio
    async def test_create_sets_used_count_zero(self, db, PS):
        svc = PromotionService(db)
        result = await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Test", type="FLAT_AMOUNT", discount_value=Decimal("5.00")
        ))
        assert result.used_count == 0

    @pytest.mark.asyncio
    async def test_promo_code_unique_within_tenant(self, db, PS):
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="First", type="FLAT_AMOUNT", discount_value=Decimal("5.00"), promo_code="SAVE5"
        ))
        with pytest.raises(ConflictError):
            await svc.create(PS["tenant_a"].id, PromotionCreate(
                name="Second", type="FLAT_AMOUNT", discount_value=Decimal("3.00"), promo_code="SAVE5"
            ))

    @pytest.mark.asyncio
    async def test_same_promo_code_allowed_in_different_tenants(self, db, PS):
        svc = PromotionService(db)
        r_a = await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="A Promo", type="FLAT_AMOUNT", discount_value=Decimal("5.00"), promo_code="SHARED"
        ))
        r_b = await svc.create(PS["tenant_b"].id, PromotionCreate(
            name="B Promo", type="FLAT_AMOUNT", discount_value=Decimal("5.00"), promo_code="SHARED"
        ))
        assert r_a.id != r_b.id

    @pytest.mark.asyncio
    async def test_get_promotion(self, db, PS):
        svc = PromotionService(db)
        created = await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Get Me", type="PERCENTAGE", discount_value=Decimal("15.00")
        ))
        fetched = await svc.get(created.id, PS["tenant_a"].id)
        assert fetched.id == created.id
        assert fetched.name == "Get Me"

    @pytest.mark.asyncio
    async def test_get_wrong_tenant_raises(self, db, PS):
        svc = PromotionService(db)
        created = await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Mine", type="PERCENTAGE", discount_value=Decimal("10.00")
        ))
        with pytest.raises(NotFoundError):
            await svc.get(created.id, PS["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_list_scoped_to_tenant(self, db, PS):
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="A Only", type="PERCENTAGE", discount_value=Decimal("5.00")
        ))
        await svc.create(PS["tenant_b"].id, PromotionCreate(
            name="B Only", type="FLAT_AMOUNT", discount_value=Decimal("3.00")
        ))
        promos_a = await svc.list(PS["tenant_a"].id)
        names_a = [p.name for p in promos_a]
        assert "A Only" in names_a
        assert "B Only" not in names_a

    @pytest.mark.asyncio
    async def test_update_promotion(self, db, PS):
        svc = PromotionService(db)
        created = await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Old Name", type="PERCENTAGE", discount_value=Decimal("10.00")
        ))
        updated = await svc.update(created.id, PS["tenant_a"].id,
                                   PromotionUpdate(name="New Name"))
        assert updated.name == "New Name"
        assert updated.discount_value == Decimal("10.00")  # unchanged

    @pytest.mark.asyncio
    async def test_delete_soft(self, db, PS):
        svc = PromotionService(db)
        created = await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Delete Me", type="PERCENTAGE", discount_value=Decimal("5.00")
        ))
        await svc.delete(created.id, PS["tenant_a"].id)
        with pytest.raises(NotFoundError):
            await svc.get(created.id, PS["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_delete_wrong_tenant_raises(self, db, PS):
        svc = PromotionService(db)
        created = await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Mine", type="PERCENTAGE", discount_value=Decimal("5.00")
        ))
        with pytest.raises(NotFoundError):
            await svc.delete(created.id, PS["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_deleted_not_in_list(self, db, PS):
        svc = PromotionService(db)
        created = await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Gone", type="PERCENTAGE", discount_value=Decimal("5.00")
        ))
        await svc.delete(created.id, PS["tenant_a"].id)
        promos = await svc.list(PS["tenant_a"].id)
        assert created.id not in [p.id for p in promos]


# ══════════════════════════════════════════════════════════════
# Evaluate — discount type logic
# ══════════════════════════════════════════════════════════════

class TestEvaluateDiscountTypes:

    @pytest.mark.asyncio
    async def test_percentage_discount_applied(self, db, PS):
        """PERCENTAGE: discount_amount = order_total × rate / 100"""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="10%", type="PERCENTAGE", discount_value=Decimal("10.00")
        ))
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("100.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)

        assert len(results) == 1
        assert results[0].discount_amount == Decimal("10.00")
        assert results[0].type == "PERCENTAGE"

    @pytest.mark.asyncio
    async def test_percentage_calculated_on_order_total(self, db, PS):
        """PERCENTAGE: calculated on the full order total, not per-item."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="20%", type="PERCENTAGE", discount_value=Decimal("20.00")
        ))
        cart = make_cart([
            {"product_id": PS["prod_a"].id, "quantity": 2, "unit_price": Decimal("50.00")},
        ])  # total = 100
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert results[0].discount_amount == Decimal("20.00")

    @pytest.mark.asyncio
    async def test_flat_amount_discount_applied(self, db, PS):
        """FLAT_AMOUNT: discount_amount = discount_value (when < order total)."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="$15 Off", type="FLAT_AMOUNT", discount_value=Decimal("15.00")
        ))
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("100.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert results[0].discount_amount == Decimal("15.00")

    @pytest.mark.asyncio
    async def test_flat_amount_capped_at_order_total(self, db, PS):
        """FLAT_AMOUNT: discount cannot exceed the order total."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="$500 Off", type="FLAT_AMOUNT", discount_value=Decimal("500.00")
        ))
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("10.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        # Capped at order total (10.00), not 500
        assert results[0].discount_amount == Decimal("10.00")

    @pytest.mark.asyncio
    async def test_bxgy_returns_zero_discount_with_message(self, db, PS):
        """BXGY: discount_amount=0, message describes the reward."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Buy 2 Get 1", type="BXGY", discount_value=Decimal("0.00"),
            reward_product_id=PS["prod_a"].id, reward_quantity=1
        ))
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 2, "unit_price": Decimal("10.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert len(results) == 1
        assert results[0].discount_amount == Decimal("0")
        assert results[0].reward_product_id == PS["prod_a"].id
        assert results[0].reward_quantity == 1
        assert "free" in results[0].message.lower()

    @pytest.mark.asyncio
    async def test_free_item_returns_zero_discount(self, db, PS):
        """FREE_ITEM: discount_amount=0, cashier adds the free item."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Free Item", type="FREE_ITEM", discount_value=Decimal("0.00"),
            reward_product_id=PS["prod_a"].id, reward_quantity=2
        ))
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("10.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert results[0].discount_amount == Decimal("0")
        assert results[0].reward_quantity == 2


# ══════════════════════════════════════════════════════════════
# Evaluate — auto-applied vs code-gated
# ══════════════════════════════════════════════════════════════

class TestEvaluatePromoCodeGating:

    @pytest.mark.asyncio
    async def test_auto_applied_no_code_needed(self, db, PS):
        """promo_code=None → auto-applied, evaluated even with no code in cart."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Auto", type="PERCENTAGE", discount_value=Decimal("5.00")
            # promo_code not set → auto-applied
        ))
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("50.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert any(r.promotion_name == "Auto" for r in results)

    @pytest.mark.asyncio
    async def test_code_gated_not_applied_without_code(self, db, PS):
        """promo_code set → not applied if no code provided in cart."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Secret", type="FLAT_AMOUNT", discount_value=Decimal("10.00"), promo_code="SECRET10"
        ))
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("50.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)  # no promo_code in cart
        assert not any(r.promotion_name == "Secret" for r in results)

    @pytest.mark.asyncio
    async def test_code_gated_applied_with_correct_code(self, db, PS):
        """promo_code matches → promotion is applied."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Secret", type="FLAT_AMOUNT", discount_value=Decimal("10.00"), promo_code="SECRET10"
        ))
        cart = make_cart(
            [{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("50.00")}],
            promo_code="SECRET10"
        )
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert any(r.promotion_name == "Secret" for r in results)

    @pytest.mark.asyncio
    async def test_code_gated_not_applied_with_wrong_code(self, db, PS):
        """Wrong promo code → not applied."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Secret", type="FLAT_AMOUNT", discount_value=Decimal("10.00"), promo_code="SECRET10"
        ))
        cart = make_cart(
            [{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("50.00")}],
            promo_code="WRONGCODE"
        )
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert not any(r.promotion_name == "Secret" for r in results)

    @pytest.mark.asyncio
    async def test_multiple_promos_filtered_by_code(self, db, PS):
        """Auto-applied shows; code-gated shows only when code matches."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Auto5", type="PERCENTAGE", discount_value=Decimal("5.00")
        ))
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Code10", type="FLAT_AMOUNT", discount_value=Decimal("10.00"), promo_code="CODE10"
        ))
        cart = make_cart(
            [{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("50.00")}],
            promo_code="CODE10"
        )
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        names = [r.promotion_name for r in results]
        assert "Auto5" in names
        assert "Code10" in names


# ══════════════════════════════════════════════════════════════
# Evaluate — trigger conditions
# ══════════════════════════════════════════════════════════════

class TestEvaluateTriggers:

    @pytest.mark.asyncio
    async def test_trigger_min_qty_met(self, db, PS):
        """trigger_min_qty=2: applied when cart has ≥2 items."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="2+ Items 10%", type="PERCENTAGE", discount_value=Decimal("10.00"),
            trigger_min_qty=2
        ))
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 2, "unit_price": Decimal("10.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert any(r.promotion_name == "2+ Items 10%" for r in results)

    @pytest.mark.asyncio
    async def test_trigger_min_qty_not_met(self, db, PS):
        """trigger_min_qty=3: NOT applied when cart has only 1 item."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="3+ Items", type="PERCENTAGE", discount_value=Decimal("10.00"),
            trigger_min_qty=3
        ))
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("10.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert not any(r.promotion_name == "3+ Items" for r in results)

    @pytest.mark.asyncio
    async def test_trigger_min_amount_met(self, db, PS):
        """trigger_min_amount=50: applied when order_total ≥ 50."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Spend 50", type="FLAT_AMOUNT", discount_value=Decimal("5.00"),
            trigger_min_amount=Decimal("50.00")
        ))
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 5, "unit_price": Decimal("10.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert any(r.promotion_name == "Spend 50" for r in results)

    @pytest.mark.asyncio
    async def test_trigger_min_amount_not_met(self, db, PS):
        """trigger_min_amount=100: NOT applied when order_total < 100."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Spend 100", type="FLAT_AMOUNT", discount_value=Decimal("10.00"),
            trigger_min_amount=Decimal("100.00")
        ))
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("10.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert not any(r.promotion_name == "Spend 100" for r in results)

    @pytest.mark.asyncio
    async def test_trigger_product_present(self, db, PS):
        """trigger_product: applied when the trigger product is in cart."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="With Burger", type="FLAT_AMOUNT", discount_value=Decimal("2.00"),
            trigger_product_id=PS["prod_a"].id
        ))
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("10.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert any(r.promotion_name == "With Burger" for r in results)

    @pytest.mark.asyncio
    async def test_trigger_product_absent(self, db, PS):
        """trigger_product: NOT applied when trigger product is NOT in cart."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="With Burger", type="FLAT_AMOUNT", discount_value=Decimal("2.00"),
            trigger_product_id=PS["prod_a"].id
        ))
        # Cart has a different product (prod_b belongs to tenant_b, use a different id)
        other_id = uuid4()
        cart = PromotionEvaluateRequest(
            items=[CartItem(product_id=other_id, quantity=1, unit_price=Decimal("10.00"))],
            order_total=Decimal("10.00")
        )
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert not any(r.promotion_name == "With Burger" for r in results)

    @pytest.mark.asyncio
    async def test_trigger_category_present(self, db, PS):
        """trigger_category: applied when item's category_id matches."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Burger Category", type="PERCENTAGE", discount_value=Decimal("10.00"),
            trigger_category_id=PS["cat_a"].id
        ))
        cart = PromotionEvaluateRequest(
            items=[CartItem(
                product_id=PS["prod_a"].id, category_id=PS["cat_a"].id,
                quantity=1, unit_price=Decimal("10.00")
            )],
            order_total=Decimal("10.00")
        )
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert any(r.promotion_name == "Burger Category" for r in results)

    @pytest.mark.asyncio
    async def test_trigger_category_absent(self, db, PS):
        """trigger_category: NOT applied when no item has matching category_id."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="Burger Cat Only", type="PERCENTAGE", discount_value=Decimal("10.00"),
            trigger_category_id=PS["cat_a"].id
        ))
        # Cart item has no category_id
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("10.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert not any(r.promotion_name == "Burger Cat Only" for r in results)


# ══════════════════════════════════════════════════════════════
# Evaluate — validity window and max uses
# ══════════════════════════════════════════════════════════════

class TestEvaluateValidityAndLimits:

    @pytest.mark.asyncio
    async def test_valid_from_in_future_not_applied(self, db, PS):
        """Promotion starting tomorrow must not apply today."""
        future = datetime.now(timezone.utc) + timedelta(days=1)
        promo = Promotion(
            id=uuid4(), tenant_id=PS["tenant_a"].id,
            name="Future", type="PERCENTAGE", discount_value=Decimal("10.00"),
            is_active=True, valid_from=future
        )
        db.add(promo)
        await db.flush()

        svc = PromotionService(db)
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("50.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert not any(r.promotion_name == "Future" for r in results)

    @pytest.mark.asyncio
    async def test_valid_until_in_past_not_applied(self, db, PS):
        """Expired promotion must not apply."""
        past = datetime.now(timezone.utc) - timedelta(days=1)
        promo = Promotion(
            id=uuid4(), tenant_id=PS["tenant_a"].id,
            name="Expired", type="PERCENTAGE", discount_value=Decimal("10.00"),
            is_active=True, valid_until=past
        )
        db.add(promo)
        await db.flush()

        svc = PromotionService(db)
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("50.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert not any(r.promotion_name == "Expired" for r in results)

    @pytest.mark.asyncio
    async def test_active_within_validity_window_applied(self, db, PS):
        """Promotion within its validity window must apply."""
        past = datetime.now(timezone.utc) - timedelta(days=1)
        future = datetime.now(timezone.utc) + timedelta(days=1)
        promo = Promotion(
            id=uuid4(), tenant_id=PS["tenant_a"].id,
            name="Active Window", type="FLAT_AMOUNT", discount_value=Decimal("5.00"),
            is_active=True, valid_from=past, valid_until=future
        )
        db.add(promo)
        await db.flush()

        svc = PromotionService(db)
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("50.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert any(r.promotion_name == "Active Window" for r in results)

    @pytest.mark.asyncio
    async def test_max_uses_exhausted_not_applied(self, db, PS):
        """When used_count >= max_uses the promotion must not apply."""
        promo = Promotion(
            id=uuid4(), tenant_id=PS["tenant_a"].id,
            name="Exhausted", type="PERCENTAGE", discount_value=Decimal("10.00"),
            is_active=True, max_uses=5, used_count=5  # already exhausted
        )
        db.add(promo)
        await db.flush()

        svc = PromotionService(db)
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("50.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert not any(r.promotion_name == "Exhausted" for r in results)

    @pytest.mark.asyncio
    async def test_max_uses_not_yet_exhausted_applied(self, db, PS):
        """When used_count < max_uses the promotion still applies."""
        promo = Promotion(
            id=uuid4(), tenant_id=PS["tenant_a"].id,
            name="Still Valid", type="PERCENTAGE", discount_value=Decimal("10.00"),
            is_active=True, max_uses=10, used_count=9  # one use left
        )
        db.add(promo)
        await db.flush()

        svc = PromotionService(db)
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("50.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert any(r.promotion_name == "Still Valid" for r in results)

    @pytest.mark.asyncio
    async def test_inactive_promotion_not_applied(self, db, PS):
        """is_active=False promotions are never evaluated."""
        promo = Promotion(
            id=uuid4(), tenant_id=PS["tenant_a"].id,
            name="Inactive", type="PERCENTAGE", discount_value=Decimal("10.00"),
            is_active=False
        )
        db.add(promo)
        await db.flush()

        svc = PromotionService(db)
        cart = make_cart([{"product_id": PS["prod_a"].id, "quantity": 1, "unit_price": Decimal("50.00")}])
        results = await svc.evaluate(PS["tenant_a"].id, cart)
        assert not any(r.promotion_name == "Inactive" for r in results)

    @pytest.mark.asyncio
    async def test_tenant_isolation_in_evaluate(self, db, PS):
        """Tenant A's promotions must never appear in tenant B's evaluate call."""
        svc = PromotionService(db)
        await svc.create(PS["tenant_a"].id, PromotionCreate(
            name="A Only Promo", type="PERCENTAGE", discount_value=Decimal("10.00")
        ))
        cart = make_cart([{"product_id": PS["prod_b"].id, "quantity": 1, "unit_price": Decimal("50.00")}])
        results_b = await svc.evaluate(PS["tenant_b"].id, cart)
        assert not any(r.promotion_name == "A Only Promo" for r in results_b)
