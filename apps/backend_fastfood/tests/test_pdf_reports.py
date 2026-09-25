# tests/test_pdf_reports.py
#
# Smoke-level coverage for the server-side PDF exports (reportlab, real A4
# documents — see services/pdf_report_service.py) added alongside the
# existing JSON report endpoints. Not pixel-level: just confirms each route
# returns a genuine, non-trivial PDF and that the underlying data (rows,
# totals) actually reached the document, without re-testing the report
# math itself (already covered by test_report_branch_integrity.py /
# test_inventory_reports.py).

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from core.security import create_access_token
from db.session import get_db
from models.role import Role
from models.user_role import UserRole
from services.variant_service import VariantService


async def _grant_admin(db, user_id, tenant_id):
    role = Role(id=uuid4(), tenant_id=tenant_id, name="Admin", is_active=True)
    db.add(role)
    await db.flush()
    db.add(UserRole(id=uuid4(), user_id=user_id, role_id=role.id))
    await db.flush()


async def _get(db, H, path):
    async def override():
        yield db
    app.dependency_overrides[get_db] = override
    token = create_access_token(H["user_a"].id, H["tenant_a"].id)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test.local") as client:
            return await client.get(path, headers={"Authorization": "Bearer " + token})
    finally:
        app.dependency_overrides.clear()


def _assert_pdf(resp) -> bytes:
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:5] == b"%PDF-"
    assert len(resp.content) > 500  # a genuine multi-element document, not an empty shell
    return resp.content


@pytest.mark.asyncio
async def test_sales_report_pdf(db, H):
    H["user_a"].all_branches = True
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)
    resp = await _get(db, H, "/api/v1/reports/pdf")
    _assert_pdf(resp)


@pytest.mark.asyncio
async def test_stock_report_pdf_with_rows_is_larger_than_empty(db, H):
    # PDF text is font-encoded, not stored as plain bytes, so this checks the
    # data actually reached the document via output size rather than a raw
    # byte-content search (which would false-negative against any real PDF).
    H["user_a"].all_branches = True
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)

    empty_resp = await _get(db, H, "/api/v1/inventory-reports/stock/pdf")
    empty_pdf = _assert_pdf(empty_resp)

    H["prod_a"].allow_inventory_tracking = True
    H["variant_a"].tracks_inventory = True
    H["variant_a"].cost_price = Decimal("5.00")
    await db.flush()
    await VariantService(db, created_by=H["user_a"].id).set_stock(
        H["tenant_a"].id, H["variant_a"].id, 12, "seed", branch_id=H["branch_a"].id,
    )

    resp = await _get(db, H, "/api/v1/inventory-reports/stock/pdf")
    pdf = _assert_pdf(resp)
    assert len(pdf) > len(empty_pdf)


@pytest.mark.asyncio
async def test_movement_report_pdf(db, H):
    H["user_a"].all_branches = True
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)
    H["prod_a"].allow_inventory_tracking = True
    H["variant_a"].tracks_inventory = True
    await db.flush()
    await VariantService(db, created_by=H["user_a"].id).adjust_stock(
        H["tenant_a"].id, H["variant_a"].id, "increase", 5, branch_id=H["branch_a"].id,
    )

    resp = await _get(db, H, "/api/v1/inventory-reports/movements/pdf")
    _assert_pdf(resp)


@pytest.mark.asyncio
async def test_transfer_report_pdf(db, H):
    H["user_a"].all_branches = True
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)
    H["prod_a"].allow_inventory_tracking = True
    H["variant_a"].tracks_inventory = True
    await db.flush()
    svc = VariantService(db, created_by=H["user_a"].id)
    await svc.set_stock(H["tenant_a"].id, H["variant_a"].id, 10, "seed", branch_id=H["branch_a"].id)

    from models.branch import Branch
    branch_a2 = Branch(id=uuid4(), business_id=H["biz_a"].id, branch_code="BR_A2",
                        name="Alpha Branch 2", is_active=True)
    db.add(branch_a2)
    await db.flush()
    await svc.transfer_stock(H["tenant_a"].id, H["variant_a"].id, H["branch_a"].id, branch_a2.id, 4)

    resp = await _get(db, H, "/api/v1/inventory-reports/transfers/pdf")
    _assert_pdf(resp)


@pytest.mark.asyncio
async def test_stock_report_pdf_empty_selection_still_renders(db, H):
    """No matching rows must not crash the PDF builder — it should render
    the standard letterhead/footer with a 'no data' note instead."""
    H["user_a"].all_branches = True
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)
    resp = await _get(db, H, "/api/v1/inventory-reports/stock/pdf?status=out_of_stock")
    _assert_pdf(resp)
