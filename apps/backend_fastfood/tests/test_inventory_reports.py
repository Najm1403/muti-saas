# tests/test_inventory_reports.py
#
# InventoryReportService — tenant-wide stock report (current/in/out/low),
# the stock-movement ledger, and the branch-transfer register. Unlike
# VariantService.history() (one variant at a time), these span the whole
# tenant, so tenant isolation is the main thing worth locking down here
# alongside each report's own filtering semantics.

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.inventory_report_service import InventoryReportService
from services.variant_service import VariantService


async def _make_trackable(db, H):
    H["prod_a"].allow_inventory_tracking = True
    H["variant_a"].tracks_inventory = True
    H["variant_a"].cost_price = Decimal("5.00")
    await db.flush()


# ── Stock report ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stock_report_computes_value_and_category(db, H):
    await _make_trackable(db, H)
    svc = VariantService(db, created_by=H["user_a"].id)
    # increase (not set_stock) so the "manual_increase" row counts as a
    # stock-in event for last_stock_in — set_stock writes "manual_set",
    # which is an ambiguous correction (could be up or down), not a receipt.
    await svc.adjust_stock(H["tenant_a"].id, H["variant_a"].id, "increase", 10,
                            note="seed", branch_id=H["branch_a"].id)

    rows = await InventoryReportService(db).stock_report(tenant_id=H["tenant_a"].id)
    row = next(r for r in rows if r.sku == H["prod_a"].product_code)
    assert row.category_name == "Burgers"
    assert row.current_stock == 10
    assert row.stock_value == Decimal("50.00")  # 10 * 5.00
    assert row.last_stock_in is not None


@pytest.mark.asyncio
async def test_stock_report_status_filters(db, H):
    await _make_trackable(db, H)
    svc = VariantService(db, created_by=H["user_a"].id)
    await svc.set_stock(H["tenant_a"].id, H["variant_a"].id, 0, "seed", branch_id=H["branch_a"].id)

    all_rows = await InventoryReportService(db).stock_report(tenant_id=H["tenant_a"].id, status="all")
    in_rows = await InventoryReportService(db).stock_report(tenant_id=H["tenant_a"].id, status="in_stock")
    out_rows = await InventoryReportService(db).stock_report(tenant_id=H["tenant_a"].id, status="out_of_stock")
    low_rows = await InventoryReportService(db).stock_report(tenant_id=H["tenant_a"].id, status="low_stock")

    assert any(r.sku == H["prod_a"].product_code for r in all_rows)
    assert not any(r.sku == H["prod_a"].product_code for r in in_rows)
    assert any(r.sku == H["prod_a"].product_code for r in out_rows)
    # low_stock includes zero-stock items (threshold default 5, 0 <= 5) —
    # same convention as variant-inventory.js's client-side filter.
    assert any(r.sku == H["prod_a"].product_code for r in low_rows)


@pytest.mark.asyncio
async def test_stock_report_never_leaks_other_tenant(db, H):
    await _make_trackable(db, H)
    H["prod_b"].allow_inventory_tracking = True
    H["variant_b"].tracks_inventory = True
    await db.flush()

    rows = await InventoryReportService(db).stock_report(tenant_id=H["tenant_a"].id)
    assert all(r.sku != H["prod_b"].product_code for r in rows)


@pytest.mark.asyncio
async def test_stock_report_excludes_untracked_variants(db, H):
    # Neither allow_inventory_tracking nor tracks_inventory flipped on.
    rows = await InventoryReportService(db).stock_report(tenant_id=H["tenant_a"].id)
    assert all(r.sku != H["prod_a"].product_code for r in rows)


# ── Movement report ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_movement_report_labels_and_scoping(db, H):
    await _make_trackable(db, H)
    svc = VariantService(db, created_by=H["user_a"].id)
    await svc.adjust_stock(H["tenant_a"].id, H["variant_a"].id, "increase", 8,
                            note="restock", branch_id=H["branch_a"].id)
    await svc.adjust_stock(H["tenant_a"].id, H["variant_a"].id, "decrease", 3,
                            note="damaged", branch_id=H["branch_a"].id)

    rows = await InventoryReportService(db).movement_report(tenant_id=H["tenant_a"].id)
    types = {r.movement_type for r in rows}
    assert "Manual increase" in types
    assert "Manual decrease" in types
    inc = next(r for r in rows if r.movement_type == "Manual increase")
    assert inc.quantity_change == 8
    assert inc.branch_name == "Alpha Branch"
    assert inc.recorded_by == "Alpha User"
    assert inc.note == "restock"


@pytest.mark.asyncio
async def test_movement_report_never_leaks_other_tenant(db, H):
    await _make_trackable(db, H)
    H["prod_b"].allow_inventory_tracking = True
    H["variant_b"].tracks_inventory = True
    await db.flush()
    svc_a = VariantService(db, created_by=H["user_a"].id)
    svc_b = VariantService(db, created_by=H["user_b"].id)
    await svc_a.adjust_stock(H["tenant_a"].id, H["variant_a"].id, "increase", 5,
                              branch_id=H["branch_a"].id)
    await svc_b.adjust_stock(H["tenant_b"].id, H["variant_b"].id, "increase", 5,
                              branch_id=H["branch_b"].id)

    rows = await InventoryReportService(db).movement_report(tenant_id=H["tenant_a"].id)
    assert all(r.sku != H["prod_b"].product_code for r in rows)


@pytest.mark.asyncio
async def test_movement_report_date_range_filter(db, H):
    await _make_trackable(db, H)
    svc = VariantService(db, created_by=H["user_a"].id)
    await svc.adjust_stock(H["tenant_a"].id, H["variant_a"].id, "increase", 4,
                            branch_id=H["branch_a"].id)

    from datetime import datetime, timedelta, timezone
    future = datetime.now(timezone.utc) + timedelta(days=1)
    rows = await InventoryReportService(db).movement_report(
        tenant_id=H["tenant_a"].id, date_from=future)
    assert rows == []


# ── Transfer report ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_transfer_report_pairs_out_and_in(db, H):
    await _make_trackable(db, H)
    svc = VariantService(db, created_by=H["user_a"].id)
    await svc.set_stock(H["tenant_a"].id, H["variant_a"].id, 20, "seed", branch_id=H["branch_a"].id)

    from models.branch import Branch
    branch_a2 = Branch(id=uuid4(), business_id=H["biz_a"].id, branch_code="BR_A2",
                        name="Alpha Branch 2", is_active=True)
    db.add(branch_a2)
    await db.flush()

    await svc.transfer_stock(H["tenant_a"].id, H["variant_a"].id, H["branch_a"].id, branch_a2.id,
                              6, note="restock branch 2")

    rows = await InventoryReportService(db).transfer_report(tenant_id=H["tenant_a"].id)
    assert len(rows) == 1
    row = rows[0]
    assert row.from_branch == "Alpha Branch"
    assert row.to_branch == "Alpha Branch 2"
    assert row.quantity == 6
    assert row.note == "restock branch 2"
    assert row.recorded_by == "Alpha User"


@pytest.mark.asyncio
async def test_transfer_report_never_leaks_other_tenant(db, H):
    await _make_trackable(db, H)
    svc = VariantService(db, created_by=H["user_a"].id)
    await svc.set_stock(H["tenant_a"].id, H["variant_a"].id, 20, "seed", branch_id=H["branch_a"].id)
    from models.branch import Branch
    branch_a2 = Branch(id=uuid4(), business_id=H["biz_a"].id, branch_code="BR_A2",
                        name="Alpha Branch 2", is_active=True)
    db.add(branch_a2)
    await db.flush()
    await svc.transfer_stock(H["tenant_a"].id, H["variant_a"].id, H["branch_a"].id, branch_a2.id, 6)

    rows = await InventoryReportService(db).transfer_report(tenant_id=H["tenant_b"].id)
    assert rows == []
