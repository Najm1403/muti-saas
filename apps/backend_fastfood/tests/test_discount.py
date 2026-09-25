# tests/test_discount.py
#
# Replaces the old "Free Guest" all-or-nothing comp mechanism with a general
# manual discount, gated by the `sales.discount` permission (granted via a
# tenant Role, same as sales.create/sales.cancel — not a one-off User flag).
#
#   1. A manual discount (no promotion_id/deal_id) is denied without the
#      permission and allowed with it — full OR partial amount, not just 100%.
#   2. A Promotion/Deal-driven discount needs no per-cashier grant at all —
#      it's business-configured, and OfferService.validate()'s promotion_id/
#      deal_id branch is mutually exclusive with the manual-discount branch.
#   3. "Free Guest" is retired: no longer a recognised payment method.

from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from core.exceptions import ForbiddenError, ValidationError
from models.permission import Permission
from models.promotion import Promotion
from models.role import Role
from models.role_permission import RolePermission
from models.sale import Sale
from models.user_role import UserRole
from schemas.pos_sale import PosSaleCreate, PosSaleItemCreate, PosSalePaymentCreate
from services.pos_sale_service import PosSaleService


async def _grant(db, user_id, tenant_id, *codes, role_name="Discounter"):
    role = Role(id=uuid4(), tenant_id=tenant_id, name=role_name, is_active=True)
    db.add(role)
    await db.flush()
    db.add(UserRole(id=uuid4(), user_id=user_id, role_id=role.id))
    for code in codes:
        pid = await db.scalar(select(Permission.id).where(Permission.code == code))
        db.add(RolePermission(id=uuid4(), role_id=role.id, permission_id=pid))
    await db.flush()
    return role


def _payload(H, *, discount, total, promotion_id=None, deal_id=None):
    return PosSaleCreate(
        sale_number="DISC-" + uuid4().hex[:12], sold_at=datetime.now(timezone.utc),
        subtotal=Decimal("10.00"), discount=discount, total=total,
        promotion_id=promotion_id, deal_id=deal_id,
        items=[PosSaleItemCreate(
            variant_id=H["prod_a"].default_variant_id, product_id=H["prod_a"].id,
            product_name="Item", quantity=1, unit_price=Decimal("10.00"), discount=0, total=Decimal("10.00"))],
        payments=[PosSalePaymentCreate(payment_method="Cash", amount=total)],
    )


async def _submit(db, H, data):
    return await PosSaleService(db).create(data, H["branch_a"].id, H["device_a"].id, H["user_a"].id, H["tenant_a"].id)


# ── manual discount, gated by sales.discount ────────────────

class TestManualDiscount:
    @pytest.mark.asyncio
    async def test_denied_without_permission(self, db, H):
        data = _payload(H, discount=Decimal("2.00"), total=Decimal("8.00"))
        with pytest.raises(ValidationError):
            await _submit(db, H, data)
        assert await db.scalar(select(Sale.id).where(Sale.sale_number == data.sale_number)) is None

    @pytest.mark.asyncio
    async def test_allowed_with_permission_partial(self, db, H):
        await _grant(db, H["user_a"].id, H["tenant_a"].id, "sales.discount")
        receipt = await _submit(db, H, _payload(H, discount=Decimal("2.00"), total=Decimal("8.00")))
        assert Decimal(receipt.discount) == Decimal("2.00")
        assert Decimal(receipt.total) == Decimal("8.00")

    @pytest.mark.asyncio
    async def test_allowed_with_permission_full(self, db, H):
        """A manual discount can still zero the whole order — it's just no
        longer the ONLY way to give any discount at all. No special payment
        method needed: a $0 total is paid with an ordinary $0 Cash tender."""
        await _grant(db, H["user_a"].id, H["tenant_a"].id, "sales.discount")
        data = _payload(H, discount=Decimal("10.00"), total=Decimal("0.00"))
        data.payments = [PosSalePaymentCreate(payment_method="Cash", amount=Decimal("0"))]
        receipt = await _submit(db, H, data)
        assert Decimal(receipt.total) == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_zero_payment_cannot_cover_a_real_total(self, db, H):
        """A $0 payment is only valid when the SALE's total is also $0 — the
        sum of payments must still cover a non-zero total (unchanged rule,
        now enforced once at the sale level instead of per-payment)."""
        data = _payload(H, discount=Decimal("0.00"), total=Decimal("10.00"))
        data.payments = [PosSalePaymentCreate(payment_method="Cash", amount=Decimal("0"))]
        with pytest.raises(ValidationError):
            await _submit(db, H, data)

    @pytest.mark.asyncio
    async def test_revoked_permission_denies_again(self, db, H):
        role = await _grant(db, H["user_a"].id, H["tenant_a"].id, "sales.discount")
        await _submit(db, H, _payload(H, discount=Decimal("1.00"), total=Decimal("9.00")))
        await db.execute(
            RolePermission.__table__.delete().where(RolePermission.role_id == role.id)
        )
        await db.flush()
        with pytest.raises(ValidationError):
            await _submit(db, H, _payload(H, discount=Decimal("1.00"), total=Decimal("9.00")))

    @pytest.mark.asyncio
    async def test_wildcard_permission_holder_always_allowed(self, db, H):
        await _grant(db, H["user_a"].id, H["tenant_a"].id, role_name="Admin")
        # "Admin"/"Owner"/"Manager" role NAMES resolve to {"*"} regardless of
        # explicit RolePermission rows — see api.dependencies.get_user_permissions.
        receipt = await _submit(db, H, _payload(H, discount=Decimal("3.00"), total=Decimal("7.00")))
        assert Decimal(receipt.discount) == Decimal("3.00")


# ── per-user max_discount_percent cap ───────────────────────

class TestDiscountCap:
    @pytest.mark.asyncio
    async def test_within_cap_allowed(self, db, H):
        await _grant(db, H["user_a"].id, H["tenant_a"].id, "sales.discount")
        H["user_a"].max_discount_percent = Decimal("10")
        await db.flush()
        receipt = await _submit(db, H, _payload(H, discount=Decimal("1.00"), total=Decimal("9.00")))
        assert Decimal(receipt.discount) == Decimal("1.00")

    @pytest.mark.asyncio
    async def test_exceeds_cap_denied(self, db, H):
        await _grant(db, H["user_a"].id, H["tenant_a"].id, "sales.discount")
        H["user_a"].max_discount_percent = Decimal("10")
        await db.flush()
        data = _payload(H, discount=Decimal("2.00"), total=Decimal("8.00"))
        with pytest.raises(ValidationError):
            await _submit(db, H, data)
        assert await db.scalar(select(Sale.id).where(Sale.sale_number == data.sale_number)) is None

    @pytest.mark.asyncio
    async def test_no_cap_set_is_uncapped(self, db, H):
        await _grant(db, H["user_a"].id, H["tenant_a"].id, "sales.discount")
        # max_discount_percent left at its default (None) — no ceiling.
        receipt = await _submit(db, H, _payload(H, discount=Decimal("9.00"), total=Decimal("1.00")))
        assert Decimal(receipt.discount) == Decimal("9.00")

    @pytest.mark.asyncio
    async def test_wildcard_holder_bypasses_cap(self, db, H):
        await _grant(db, H["user_a"].id, H["tenant_a"].id, role_name="Admin")
        H["user_a"].max_discount_percent = Decimal("1")
        await db.flush()
        receipt = await _submit(db, H, _payload(H, discount=Decimal("5.00"), total=Decimal("5.00")))
        assert Decimal(receipt.discount) == Decimal("5.00")

    @pytest.mark.asyncio
    async def test_offer_discount_bypasses_cap(self, db, H):
        """A Promotion/Deal discount isn't a manual discount, so a low
        per-user cap (or no sales.discount permission at all) never applies."""
        H["user_a"].max_discount_percent = Decimal("1")
        await db.flush()
        promo = Promotion(
            id=uuid4(), tenant_id=H["tenant_a"].id, name="Everything $2 off",
            type="FLAT_AMOUNT", discount_value=Decimal("2.00"),
            is_active=True, all_branches=True,
        )
        db.add(promo)
        await db.flush()
        data = _payload(H, discount=Decimal("2.00"), total=Decimal("8.00"), promotion_id=promo.id)
        receipt = await _submit(db, H, data)
        assert Decimal(receipt.discount) == Decimal("2.00")


# ── Promotion-driven discount needs no per-cashier grant ────

class TestOfferDiscountNeedsNoPermission:
    @pytest.mark.asyncio
    async def test_promotion_discount_bypasses_permission_check(self, db, H):
        promo = Promotion(
            id=uuid4(), tenant_id=H["tenant_a"].id, name="Everything $2 off",
            type="FLAT_AMOUNT", discount_value=Decimal("2.00"),
            is_active=True, all_branches=True,
        )
        db.add(promo)
        await db.flush()
        # user_a has NO sales.discount permission at all here.
        data = _payload(H, discount=Decimal("2.00"), total=Decimal("8.00"), promotion_id=promo.id)
        receipt = await _submit(db, H, data)
        assert Decimal(receipt.discount) == Decimal("2.00")


# ── "Free Guest" is retired ─────────────────────────────────

class TestFreeGuestRetired:
    def test_free_guest_not_a_recognised_payment_method(self):
        with pytest.raises(Exception):
            PosSalePaymentCreate(payment_method="Free Guest", amount=Decimal("0"))


@pytest.fixture(autouse=True)
def plain_product_fixture(H):
    # These tests sell via the zero-option default Variant, so the attached
    # Variant Option Group must not be required.
    H["pvog_a"].is_required = False
