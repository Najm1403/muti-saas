# tests/test_refunds_report.py
#
# Tenant dashboard "Reports & Analytics" visibility into returns and
# cancellations — previously the only trace of either was a bare
# `cancelled_sales` COUNT in SalesSummary, with no currency amount, no
# refunded-sales count, and no dedicated section anywhere (see
# services/tenant_report_service.py::get_refunds_summary/get_returned_products
# and schemas/tenant_report.py::RefundsSummary/ReturnedProductItem).

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from models.branch import Branch
from models.refund import Refund
from models.refund_item import RefundItem
from models.sale import Sale
from models.sale_item import SaleItem
from services.tenant_report_service import TenantReportService


async def _isolated_branch(db, H):
    """A fresh branch, since H["branch_a"] already carries seeded sales/
    refunds from the shared fixture that would otherwise pollute these
    tenant-wide (not per-shift) aggregates."""
    branch = Branch(
        id=uuid4(), business_id=H["biz_a"].id, branch_code=f"BR-{uuid4().hex[:6]}",
        name="Isolated Branch", is_active=True,
    )
    db.add(branch)
    await db.flush()
    return branch


def _sale(H, branch, *, number, status, total):
    return Sale(
        id=uuid4(), branch_id=branch.id, device_id=H["device_a"].id,
        user_id=H["user_a"].id, sale_number=number,
        sold_at=datetime.now(timezone.utc), subtotal=total,
        discount=Decimal("0.00"), tax_amount=Decimal("0.00"),
        total=total, status=status,
    )


def _sale_item(H, sale, *, name, qty, unit_price):
    return SaleItem(
        id=uuid4(), sale_id=sale.id, variant_id=H["prod_a"].default_variant_id,
        product_id=H["prod_a"].id, product_name=name,
        quantity=qty, unit_price=unit_price, discount=Decimal("0.00"),
        total=unit_price * qty,
    )


def _refund(H, branch, sale, *, refund_type, amount, breakdown):
    return Refund(
        id=uuid4(), sale_id=sale.id, branch_id=branch.id,
        device_id=H["device_a"].id, refund_number=f"R-{uuid4().hex[:8]}",
        refunded_at=datetime.now(timezone.utc), amount=amount,
        refund_method=next(iter(breakdown)), payment_breakdown=breakdown,
        status="COMPLETED", refund_type=refund_type,
        processed_by_user_id=H["user_a"].id,
    )


@pytest.mark.asyncio
async def test_refunds_summary_splits_returns_and_cancellations(db, H):
    branch = await _isolated_branch(db, H)
    returned_sale = _sale(H, branch, number="RET-001", status="COMPLETED", total=Decimal("50.00"))
    cancelled_sale = _sale(H, branch, number="CAN-001", status="CANCELLED", total=Decimal("30.00"))
    db.add_all([returned_sale, cancelled_sale])
    await db.flush()

    item = _sale_item(H, returned_sale, name="Burger", qty=Decimal("1"), unit_price=Decimal("20.00"))
    db.add(item)
    await db.flush()

    return_refund = _refund(
        H, branch, returned_sale, refund_type="RETURN", amount=Decimal("20.00"),
        breakdown={"Cash": "20.00"},
    )
    cancel_refund = _refund(
        H, branch, cancelled_sale, refund_type="CANCEL", amount=Decimal("30.00"),
        breakdown={"Credit Card": "30.00"},
    )
    db.add_all([return_refund, cancel_refund])
    await db.flush()
    db.add(RefundItem(
        id=uuid4(), refund_id=return_refund.id, sale_item_id=item.id,
        product_name="Burger", quantity=Decimal("1"),
        unit_price=Decimal("20.00"), amount=Decimal("20.00"),
    ))
    await db.flush()

    svc = TenantReportService(db)
    refunds = await svc.get_refunds_summary(H["tenant_a"].id, None, None, branch.id)
    assert refunds.refund_count == 1
    assert refunds.refund_total == Decimal("20.00")
    assert refunds.refunds_by_payment_method["Cash"] == Decimal("20.00")
    assert refunds.cancellation_count == 1
    assert refunds.cancellation_total == Decimal("30.00")
    assert refunds.cancellations_by_payment_method["Credit Card"] == Decimal("30.00")

    # The main summary KPI now surfaces both without needing a second call.
    summary = await svc.get_summary(H["tenant_a"].id, None, None, branch.id)
    assert summary.refund_total == Decimal("20.00")
    assert summary.cancellation_total == Decimal("30.00")
    assert summary.cancelled_sales == 1


@pytest.mark.asyncio
async def test_refunded_sale_counted_in_summary(db, H):
    branch = await _isolated_branch(db, H)
    sale = _sale(H, branch, number="REFUNDED-001", status="REFUNDED", total=Decimal("15.00"))
    db.add(sale)
    await db.flush()

    svc = TenantReportService(db)
    summary = await svc.get_summary(H["tenant_a"].id, None, None, branch.id)
    assert summary.refunded_sales == 1
    # A fully-refunded sale contributes nothing to net revenue...
    assert summary.total_revenue == Decimal("0.00")
    # ...but its original amount still counts toward gross sales — refund
    # detail belongs in the dedicated Refunds report, not hidden by zeroing
    # the headline "how much did we sell" figure.
    assert summary.gross_sales == Decimal("15.00")


@pytest.mark.asyncio
async def test_returned_products_ranks_by_amount(db, H):
    branch = await _isolated_branch(db, H)
    sale = _sale(H, branch, number="MULTI-RET-001", status="COMPLETED", total=Decimal("70.00"))
    db.add(sale)
    await db.flush()
    burger = _sale_item(H, sale, name="Burger", qty=Decimal("2"), unit_price=Decimal("20.00"))
    fries = _sale_item(H, sale, name="Fries", qty=Decimal("1"), unit_price=Decimal("10.00"))
    db.add_all([burger, fries])
    await db.flush()

    refund = _refund(H, branch, sale, refund_type="RETURN", amount=Decimal("50.00"), breakdown={"Cash": "50.00"})
    db.add(refund)
    await db.flush()
    db.add_all([
        RefundItem(id=uuid4(), refund_id=refund.id, sale_item_id=burger.id,
                   product_name="Burger", quantity=Decimal("2"), unit_price=Decimal("20.00"),
                   amount=Decimal("40.00")),
        RefundItem(id=uuid4(), refund_id=refund.id, sale_item_id=fries.id,
                   product_name="Fries", quantity=Decimal("1"), unit_price=Decimal("10.00"),
                   amount=Decimal("10.00")),
    ])
    await db.flush()

    svc = TenantReportService(db)
    top = await svc.get_returned_products(H["tenant_a"].id, None, None, branch.id)
    assert [(p.product_name, p.amount_returned) for p in top] == [
        ("Burger", Decimal("40.00")),
        ("Fries", Decimal("10.00")),
    ]
    assert top[0].quantity_returned == Decimal("2")
    assert top[0].times_returned == 1


@pytest.mark.asyncio
async def test_refunds_summary_scoped_by_cashier_and_session(db, H):
    branch = await _isolated_branch(db, H)
    sale = _sale(H, branch, number="SESSION-SCOPED-001", status="COMPLETED", total=Decimal("20.00"))
    db.add(sale)
    await db.flush()
    refund = _refund(H, branch, sale, refund_type="RETURN", amount=Decimal("20.00"), breakdown={"Cash": "20.00"})
    other_user_id = uuid4()
    db.add(refund)
    await db.flush()

    svc = TenantReportService(db)
    scoped_to_correct_user = await svc.get_refunds_summary(
        H["tenant_a"].id, None, None, branch.id, user_id=H["user_a"].id,
    )
    assert scoped_to_correct_user.refund_count == 1

    scoped_to_other_user = await svc.get_refunds_summary(
        H["tenant_a"].id, None, None, branch.id, user_id=other_user_id,
    )
    assert scoped_to_other_user.refund_count == 0


@pytest.mark.asyncio
async def test_refunds_endpoints_reachable_over_http(db, H):
    from tests.test_pdf_reports import _get, _grant_admin

    H["user_a"].all_branches = True
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)
    resp = await _get(db, H, "/api/v1/reports/refunds")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "refund_count" in body and "cancellation_total" in body

    resp = await _get(db, H, "/api/v1/reports/returned-products")
    assert resp.status_code == 200, resp.text
    assert isinstance(resp.json(), list)
