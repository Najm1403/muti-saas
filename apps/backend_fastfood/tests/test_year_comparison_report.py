# tests/test_year_comparison_report.py
#
# Tenant dashboard "Year Comparison" tab — a dedicated multi-year KPI
# snapshot (sales, revenue, refunds, avg order value, monthly curve, YoY
# growth %), separate from the single-line /reports/yearly trend that only
# ever fed the old bundled "Year-over-Year Overview" table (see
# services/tenant_report_service.py::get_year_comparison).

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from models.branch import Branch
from models.sale import Sale
from services.tenant_report_service import TenantReportService


async def _isolated_branch(db, H):
    branch = Branch(
        id=uuid4(), business_id=H["biz_a"].id, branch_code=f"BR-{uuid4().hex[:6]}",
        name="Isolated Branch", is_active=True,
    )
    db.add(branch)
    await db.flush()
    return branch


def _sale(H, branch, *, number, year, total, month=6):
    return Sale(
        id=uuid4(), branch_id=branch.id, device_id=H["device_a"].id,
        user_id=H["user_a"].id, sale_number=number,
        sold_at=datetime(year, month, 15, 12, 0, tzinfo=timezone.utc),
        subtotal=total, discount=Decimal("0.00"), tax_amount=Decimal("0.00"),
        total=total, status="COMPLETED",
    )


@pytest.mark.asyncio
async def test_year_comparison_returns_only_requested_years(db, H):
    branch = await _isolated_branch(db, H)
    db.add_all([
        _sale(H, branch, number="Y1-001", year=2023, total=Decimal("100.00")),
        _sale(H, branch, number="Y2-001", year=2026, total=Decimal("200.00")),
    ])
    await db.flush()

    svc = TenantReportService(db)
    points = await svc.get_year_comparison(H["tenant_a"].id, [2023, 2026], branch.id)

    assert [p.year for p in points] == [2023, 2026]
    for p in points:
        assert len(p.monthly) == 12
        assert [m.month for m in p.monthly] == list(range(1, 13))
    assert points[0].total_revenue == Decimal("100.00")
    assert points[1].total_revenue == Decimal("200.00")


@pytest.mark.asyncio
async def test_year_comparison_computes_growth_pct(db, H):
    branch = await _isolated_branch(db, H)
    db.add_all([
        _sale(H, branch, number="G1-001", year=2025, total=Decimal("100.00")),
        _sale(H, branch, number="G2-001", year=2026, total=Decimal("150.00")),
    ])
    await db.flush()

    svc = TenantReportService(db)
    points = await svc.get_year_comparison(H["tenant_a"].id, [2025, 2026], branch.id)

    by_year = {p.year: p for p in points}
    # 2025 has no 2024 data — prior-year revenue is 0, so growth stays unknown
    # rather than reporting a meaningless "infinite" percentage.
    assert by_year[2025].revenue_growth_pct is None
    assert by_year[2026].revenue_growth_pct == Decimal("50.00")


@pytest.mark.asyncio
async def test_year_comparison_month_revenue_lands_in_correct_bucket(db, H):
    branch = await _isolated_branch(db, H)
    db.add_all([
        _sale(H, branch, number="M1-001", year=2026, total=Decimal("30.00"), month=3),
        _sale(H, branch, number="M2-001", year=2026, total=Decimal("70.00"), month=11),
    ])
    await db.flush()

    svc = TenantReportService(db)
    points = await svc.get_year_comparison(H["tenant_a"].id, [2026], branch.id)

    monthly = {m.month: m.revenue for m in points[0].monthly}
    assert monthly[3] == Decimal("30.00")
    assert monthly[11] == Decimal("70.00")
    assert monthly[1] == Decimal("0.00")


@pytest.mark.asyncio
async def test_year_comparison_endpoints_reachable_over_http(db, H):
    from tests.test_pdf_reports import _get, _grant_admin

    H["user_a"].all_branches = True
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)

    resp = await _get(db, H, "/api/v1/reports/year-comparison?years=2025&years=2026")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert [p["year"] for p in body] == [2025, 2026]

    resp = await _get(db, H, "/api/v1/reports/year-comparison/pdf?years=2025&years=2026")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:5] == b"%PDF-"


@pytest.mark.asyncio
async def test_year_comparison_rejects_no_years_or_too_many(db, H):
    from tests.test_pdf_reports import _get, _grant_admin

    H["user_a"].all_branches = True
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)

    resp = await _get(db, H, "/api/v1/reports/year-comparison")
    assert resp.status_code == 422

    too_many = "&".join(f"years={y}" for y in range(2010, 2022))  # 12 years
    resp = await _get(db, H, f"/api/v1/reports/year-comparison?{too_many}")
    assert resp.status_code == 422
