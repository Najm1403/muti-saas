from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select

from core.exceptions import ValidationError
from models.cashier_session import CashierSession
from models.refund import Refund
from models.sale import Sale
from schemas.pos_sale import PosSaleCreate, PosSaleItemCreate, PosSalePaymentCreate
from schemas.refund import PosCancelCreate, PosReturnCreate, PosReturnItemCreate
from services.pos_return_service import PosReturnService
from services.pos_sale_service import PosSaleService


async def _session(db, H):
    row = CashierSession(
        device_id=H["device_a"].id,
        user_id=H["user_a"].id,
        branch_id=H["branch_a"].id,
        tenant_id=H["tenant_a"].id,
        opened_at=datetime.now(timezone.utc),
        opening_cash=Decimal("0"),
        status="OPEN",
    )
    db.add(row)
    await db.flush()
    return row


async def _sale(db, H, session, quantity=1):
    H["pvog_a"].is_required = False
    await db.flush()
    total = Decimal("10") * quantity
    data = PosSaleCreate(
        sale_number=f"RET-{session.id}-{quantity}",
        sold_at=datetime.now(timezone.utc),
        session_id=session.id,
        subtotal=total,
        total=total,
        items=[PosSaleItemCreate(
            variant_id=H["prod_a"].default_variant_id,
            product_id=H["prod_a"].id,
            product_name=H["prod_a"].name,
            quantity=quantity,
            unit_price=Decimal("10"),
            total=total,
        )],
        payments=[PosSalePaymentCreate(payment_method="Cash", amount=total)],
    )
    return await PosSaleService(db).create(
        data, H["branch_a"].id, H["device_a"].id,
        H["user_a"].id, H["tenant_a"].id,
    )


@pytest.mark.asyncio
async def test_cancel_is_full_same_shift_reversal_and_cannot_repeat(db, H):
    session = await _session(db, H)
    receipt = await _sale(db, H, session)
    service = PosReturnService(db)
    with patch("api.dependencies.get_user_permissions", new=AsyncMock(return_value={"sales.cancel"})):
        result = await service.cancel(
            sale_id=receipt.sale_id,
            data=PosCancelCreate(reason="Duplicate bill"),
            tenant_id=H["tenant_a"].id,
            branch_id=H["branch_a"].id,
            device_id=H["device_a"].id,
            user_id=H["user_a"].id,
        )
        assert result.refund_type == "CANCEL"
        assert result.amount == Decimal("10")
        assert await db.scalar(select(Sale.status).where(Sale.id == receipt.sale_id)) == "CANCELLED"
        refund = await db.scalar(select(Refund).where(Refund.id == result.id))
        assert refund.processed_by_user_id == H["user_a"].id
        assert refund.session_id == session.id
        with pytest.raises(ValidationError):
            await service.cancel(
                sale_id=receipt.sale_id,
                data=PosCancelCreate(reason="Again"),
                tenant_id=H["tenant_a"].id,
                branch_id=H["branch_a"].id,
                device_id=H["device_a"].id,
                user_id=H["user_a"].id,
            )


@pytest.mark.asyncio
async def test_partial_return_uses_server_price_and_full_return_closes_sale(db, H):
    session = await _session(db, H)
    receipt = await _sale(db, H, session, quantity=2)
    line = receipt.items[0]
    service = PosReturnService(db)
    with patch("api.dependencies.get_user_permissions", new=AsyncMock(return_value={"sales.cancel"})):
        first = await service.return_items(
            sale_id=receipt.sale_id,
            data=PosReturnCreate(reason="Customer return", items=[
                PosReturnItemCreate(sale_item_id=line.id, quantity=1)
            ]),
            tenant_id=H["tenant_a"].id,
            branch_id=H["branch_a"].id,
            device_id=H["device_a"].id,
            user_id=H["user_a"].id,
        )
        assert first.amount == Decimal("10")
        assert await db.scalar(select(Sale.status).where(Sale.id == receipt.sale_id)) == "COMPLETED"

        second = await service.return_items(
            sale_id=receipt.sale_id,
            data=PosReturnCreate(items=[
                PosReturnItemCreate(sale_item_id=line.id, quantity=1)
            ]),
            tenant_id=H["tenant_a"].id,
            branch_id=H["branch_a"].id,
            device_id=H["device_a"].id,
            user_id=H["user_a"].id,
        )
        assert second.amount == Decimal("10")
        assert await db.scalar(select(Sale.status).where(Sale.id == receipt.sale_id)) == "REFUNDED"

        with pytest.raises(ValidationError):
            await service.return_items(
                sale_id=receipt.sale_id,
                data=PosReturnCreate(items=[
                    PosReturnItemCreate(sale_item_id=line.id, quantity=1)
                ]),
                tenant_id=H["tenant_a"].id,
                branch_id=H["branch_a"].id,
                device_id=H["device_a"].id,
                user_id=H["user_a"].id,
            )


@pytest.mark.asyncio
async def test_split_payment_returns_preserve_payment_method_breakdown(db, H):
    session = await _session(db, H)
    H["pvog_a"].is_required = False
    await db.flush()
    data = PosSaleCreate(
        sale_number=f"SPLIT-{session.id}", sold_at=datetime.now(timezone.utc),
        session_id=session.id, subtotal=20, total=20,
        items=[PosSaleItemCreate(
            variant_id=H["prod_a"].default_variant_id,
            product_id=H["prod_a"].id, product_name=H["prod_a"].name,
            quantity=2, unit_price=10, total=20,
        )],
        payments=[
            PosSalePaymentCreate(payment_method="Cash", amount=10),
            PosSalePaymentCreate(payment_method="Credit Card", amount=10),
        ],
    )
    receipt = await PosSaleService(db).create(
        data, H["branch_a"].id, H["device_a"].id,
        H["user_a"].id, H["tenant_a"].id,
    )
    service = PosReturnService(db)
    with patch("api.dependencies.get_user_permissions", new=AsyncMock(return_value={"sales.cancel"})):
        first = await service.return_items(
            sale_id=receipt.sale_id,
            data=PosReturnCreate(items=[PosReturnItemCreate(
                sale_item_id=receipt.items[0].id, quantity=1)]),
            tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id,
            device_id=H["device_a"].id, user_id=H["user_a"].id,
        )
        first_row = await db.scalar(select(Refund).where(Refund.id == first.id))
        assert first_row.payment_breakdown == {"Cash": "10.00"}

        second = await service.return_items(
            sale_id=receipt.sale_id,
            data=PosReturnCreate(items=[PosReturnItemCreate(
                sale_item_id=receipt.items[0].id, quantity=1)]),
            tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id,
            device_id=H["device_a"].id, user_id=H["user_a"].id,
        )
        second_row = await db.scalar(select(Refund).where(Refund.id == second.id))
        assert second_row.payment_breakdown == {"Credit Card": "10.00"}


# ── _redistribute: rounding adjustment must never go negative ──────────

def test_redistribute_spreads_a_shortfall_larger_than_the_last_line():
    """The exact bug shape: target is capped below sum(raw) by more than
    the last line's own share (e.g. an earlier partial refund already
    consumed some of the sale's remaining total) — the old code did
    raw[-1] += (target - sum(raw)) unconditionally, which drove a small
    last line negative instead of spreading the shortfall."""
    raw = [Decimal("5.00"), Decimal("0.02")]
    target = Decimal("4.50")  # shortfall of 0.52 — more than raw[-1]'s 0.02
    result = PosReturnService._redistribute(raw, target)
    assert all(v >= 0 for v in result)
    assert sum(result, Decimal(0)) == target
    assert result == [Decimal("4.50"), Decimal("0.00")]


def test_redistribute_adds_small_surplus_to_last_line():
    """Ordinary case: sum(raw) undershoots target by a cent or two of
    rounding slack — still fine to add it all to the last line."""
    raw = [Decimal("1.00"), Decimal("1.00")]
    target = Decimal("2.01")
    assert PosReturnService._redistribute(raw, target) == [Decimal("1.00"), Decimal("1.01")]


def test_redistribute_noop_when_already_matching():
    raw = [Decimal("3.00"), Decimal("2.00")]
    assert PosReturnService._redistribute(raw, Decimal("5.00")) == raw


def test_redistribute_handles_empty_raw():
    assert PosReturnService._redistribute([], Decimal("5.00")) == []


# ── _payment_breakdown: sub-cent leftovers must not be silently dropped ─

@pytest.mark.asyncio
async def test_payment_breakdown_folds_subcent_shortfall_into_largest_method(db, H):
    svc = PosReturnService(db)
    sale = SimpleNamespace(id=uuid4(), payments=[
        SimpleNamespace(payment_method="Cash", amount=Decimal("6.665")),
        SimpleNamespace(payment_method="Card", amount=Decimal("3.33")),
    ])
    result = await svc._payment_breakdown(sale, Decimal("10.00"))
    assert sum(result.values(), Decimal(0)) == Decimal("10.00")
    assert result == {"Cash": Decimal("6.67"), "Card": Decimal("3.33")}


@pytest.mark.asyncio
async def test_payment_breakdown_still_raises_when_nothing_available(db, H):
    svc = PosReturnService(db)
    sale = SimpleNamespace(id=uuid4(), payments=[])
    with pytest.raises(ValidationError):
        await svc._payment_breakdown(sale, Decimal("5.00"))
