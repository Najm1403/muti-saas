# tests/test_shift_variance.py
#
# Tenant dashboard "Cash Shortages" visibility — previously the only place a
# shift's cash variance (closing cash vs. expected cash) was ever visible
# was the cashier's own device at the moment they closed it (never stored,
# never surfaced to a tenant admin). See
# services/cashier_session_service.py::list_variance and
# GET /api/v1/reports/shifts.

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from models.branch import Branch
from models.device import Device, DeviceStatus
from schemas.pos_session import SessionCloseRequest, SessionOpenRequest
from services.cashier_session_service import CashierSessionService


async def _open_and_close(svc, device_id, user_id, branch_id, tenant_id, *, opening, closing):
    await svc.open(
        device_id, user_id, branch_id, tenant_id,
        SessionOpenRequest(opening_cash=opening),
    )
    return await svc.close(
        device_id, user_id, tenant_id,
        SessionCloseRequest(closing_cash=closing),
    )


@pytest.mark.asyncio
async def test_list_variance_reports_shortage_overage_and_balanced(db, H):
    svc = CashierSessionService(db)

    short = await _open_and_close(
        svc, H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        opening=Decimal("100.00"), closing=Decimal("80.00"),
    )
    assert short.variance == Decimal("-20.00")

    rows = await svc.list_variance(H["tenant_a"].id, branch_id=H["branch_a"].id)
    row = next(r for r in rows if r.id == short.session.id)
    assert row.opening_cash == Decimal("100.00")
    assert row.closing_cash == Decimal("80.00")
    assert row.expected_cash == Decimal("100.00")
    assert row.variance == Decimal("-20.00")
    assert row.branch_name == H["branch_a"].name
    assert row.device_id == H["device_a"].id


@pytest.mark.asyncio
async def test_list_variance_shortages_only_filters_out_overage_and_balanced(db, H):
    svc = CashierSessionService(db)

    await _open_and_close(
        svc, H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        opening=Decimal("50.00"), closing=Decimal("50.00"),  # balanced
    )
    overage = await _open_and_close(
        svc, H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        opening=Decimal("50.00"), closing=Decimal("60.00"),  # over
    )
    short = await _open_and_close(
        svc, H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        opening=Decimal("50.00"), closing=Decimal("30.00"),  # short
    )

    rows = await svc.list_variance(
        H["tenant_a"].id, branch_id=H["branch_a"].id, shortages_only=True,
    )
    ids = {r.id for r in rows}
    assert short.session.id in ids
    assert overage.session.id not in ids
    assert all(r.variance < 0 for r in rows)


@pytest.mark.asyncio
async def test_list_variance_scoped_by_allowed_branch_ids(db, H):
    other_branch = Branch(
        id=uuid4(), business_id=H["biz_a"].id, branch_code="BR_A3",
        name="Alpha Third", is_active=True,
    )
    other_device = Device(
        id=uuid4(), branch_id=other_branch.id, device_code="POS-OTHERBR",
        letter="A", name="Other Branch POS", device_type="POS",
        status=DeviceStatus.ACTIVE,
    )
    db.add_all([other_branch, other_device])
    await db.flush()

    svc = CashierSessionService(db)
    in_scope = await _open_and_close(
        svc, H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        opening=Decimal("10.00"), closing=Decimal("5.00"),
    )
    out_of_scope = await _open_and_close(
        svc, other_device.id, H["user_a"].id, other_branch.id, H["tenant_a"].id,
        opening=Decimal("10.00"), closing=Decimal("5.00"),
    )

    rows = await svc.list_variance(
        H["tenant_a"].id, allowed_branch_ids={H["branch_a"].id},
    )
    ids = {r.id for r in rows}
    assert in_scope.session.id in ids
    assert out_of_scope.session.id not in ids


@pytest.mark.asyncio
async def test_list_variance_only_includes_closed_sessions(db, H):
    svc = CashierSessionService(db)
    await svc.open(
        H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("40.00")),
    )
    rows = await svc.list_variance(H["tenant_a"].id, branch_id=H["branch_a"].id)
    assert rows == []


@pytest.mark.asyncio
async def test_list_variance_respects_date_range(db, H):
    svc = CashierSessionService(db)
    recent = await _open_and_close(
        svc, H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        opening=Decimal("10.00"), closing=Decimal("10.00"),
    )

    old_cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    rows = await svc.list_variance(
        H["tenant_a"].id, branch_id=H["branch_a"].id, date_from=old_cutoff,
    )
    assert any(r.id == recent.session.id for r in rows)

    future_cutoff = datetime.now(timezone.utc) + timedelta(days=1)
    rows = await svc.list_variance(
        H["tenant_a"].id, branch_id=H["branch_a"].id, date_from=future_cutoff,
    )
    assert rows == []


@pytest.mark.asyncio
async def test_shift_variance_endpoint_reachable_and_branch_scoped(db, H):
    from models.user_branch import UserBranch
    from tests.test_pdf_reports import _get, _grant_admin

    second_branch = Branch(
        id=uuid4(), business_id=H["biz_a"].id, branch_code="BR_A4",
        name="Alpha Fourth", is_active=True,
    )
    db.add(second_branch)
    await db.flush()

    H["user_a"].all_branches = False
    db.add(UserBranch(user_id=H["user_a"].id, branch_id=H["branch_a"].id))
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)
    await db.flush()

    svc = CashierSessionService(db)
    await _open_and_close(
        svc, H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        opening=Decimal("15.00"), closing=Decimal("10.00"),
    )

    resp = await _get(db, H, "/api/v1/reports/shifts")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert any(item["variance"] == "-5.00" for item in body)

    # Not assigned to second_branch — must be rejected, not silently ignored.
    resp = await _get(db, H, f"/api/v1/reports/shifts?branch_id={second_branch.id}")
    assert resp.status_code == 403
