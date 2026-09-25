"""Cashier shift session lifecycle — open/close/current/history.

Covers the cross-cashier handoff fix: a session opened by one cashier must
never be silently handed to a different cashier logging into the same
device (get_current is scoped by user_id, not just device_id), while the
device-wide "only one open session at a time" invariant is preserved.

Also covers the cross-device exclusivity fix: the same cashier must not be
able to sign in (cashier_login/staff_pin_login) on a second device while a
shift is already open on a first one — see get_open_elsewhere() and
api/v1/pos/auth.py::_assert_no_open_shift_elsewhere().
"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from core.exceptions import NotFoundError, ValidationError
from core.security import create_device_token, hash_password
from db.session import get_db
from models.device import Device, DeviceStatus
from models.permission import Permission
from models.role import Role
from models.role_permission import RolePermission
from models.user import User
from models.user_role import UserRole
from schemas.pos_session import SessionCloseRequest, SessionOpenRequest
from services.cashier_session_service import CashierSessionService


@pytest_asyncio.fixture
async def second_cashier(db, H):
    """A second user on Tenant A, assigned to the same branch as user_a."""
    user = User(
        id=uuid4(), tenant_id=H["tenant_a"].id, username="alpha_user_2",
        full_name="Alpha User Two", password_hash=hash_password("Test1234!"),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


@pytest.mark.asyncio
async def test_open_close_and_current_round_trip(db, H):
    svc = CashierSessionService(db)
    opened = await svc.open(
        H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("100.00")),
    )
    assert opened.status == "OPEN"

    current = await svc.get_current(H["device_a"].id, H["user_a"].id, H["tenant_a"].id)
    assert current.id == opened.id

    closed = await svc.close(
        H["device_a"].id, H["user_a"].id, H["tenant_a"].id,
        SessionCloseRequest(closing_cash=Decimal("100.00")),
    )
    assert closed.session.status == "CLOSED"
    assert closed.variance == Decimal("0.00")


@pytest.mark.asyncio
async def test_second_cashier_never_inherits_first_cashiers_open_session(db, H, second_cashier):
    svc = CashierSessionService(db)
    await svc.open(
        H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("50.00")),
    )

    # Cashier B logs into the same device — must NOT see cashier A's session.
    with pytest.raises(NotFoundError):
        await svc.get_current(H["device_a"].id, second_cashier.id, H["tenant_a"].id)

    # B also can't open a new one while the device already has A's shift open —
    # the device-wide invariant is unaffected by the get_current fix.
    with pytest.raises(ValidationError, match="already open on this device"):
        await svc.open(
            H["device_a"].id, second_cashier.id, H["branch_a"].id, H["tenant_a"].id,
            SessionOpenRequest(opening_cash=Decimal("0.00")),
        )

    # Nor can B close A's session.
    with pytest.raises(ValidationError, match="only close your own session"):
        await svc.close(
            H["device_a"].id, second_cashier.id, H["tenant_a"].id,
            SessionCloseRequest(closing_cash=Decimal("50.00")),
        )

    # A still sees their own session as current, unaffected.
    current = await svc.get_current(H["device_a"].id, H["user_a"].id, H["tenant_a"].id)
    assert current.user_id == H["user_a"].id


@pytest.mark.asyncio
async def test_shift_number_format_and_daily_sequence(db, H):
    """YYMMDD + device letter + a per-device sequence starting at 1 each
    day, e.g. "260924A1", then "260924A2" for that device's next shift the
    same day — see CashierSessionService._next_shift_number()."""
    svc = CashierSessionService(db)
    today_prefix = datetime.now(timezone.utc).strftime("%y%m%d") + H["device_a"].letter

    first = await svc.open(
        H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("100.00")),
    )
    assert first.shift_number == f"{today_prefix}1"

    await svc.close(
        H["device_a"].id, H["user_a"].id, H["tenant_a"].id,
        SessionCloseRequest(closing_cash=Decimal("100.00")),
    )
    second = await svc.open(
        H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("50.00")),
    )
    assert second.shift_number == f"{today_prefix}2"


@pytest.mark.asyncio
async def test_shift_number_sequence_is_independent_per_device(db, H, device_b_same_branch):
    """A second device at the same branch gets its own daily sequence,
    keyed off its own letter — it doesn't continue device A's count."""
    svc = CashierSessionService(db)
    today = datetime.now(timezone.utc).strftime("%y%m%d")

    a1 = await svc.open(
        H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("10.00")),
    )
    assert a1.shift_number == f"{today}{H['device_a'].letter}1"

    b1 = await svc.open(
        device_b_same_branch.id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("10.00")),
    )
    assert b1.shift_number == f"{today}{device_b_same_branch.letter}1"


@pytest.mark.asyncio
async def test_history_lists_closed_sessions_and_summary_survives_close(db, H):
    svc = CashierSessionService(db)
    opened = await svc.open(
        H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("20.00")),
    )
    closed = await svc.close(
        H["device_a"].id, H["user_a"].id, H["tenant_a"].id,
        SessionCloseRequest(closing_cash=Decimal("20.00")),
    )

    history = await svc.list_history(H["user_a"].id, H["tenant_a"].id)
    assert any(s.id == opened.id for s in history)
    assert all(s.status == "CLOSED" for s in history)

    # The reconciliation summary is still reachable by id after close —
    # unlike summary(), which requires an OPEN session.
    detail = await svc.history_summary(closed.session.id, H["user_a"].id, H["tenant_a"].id)
    assert detail.session.id == closed.session.id
    assert detail.summary.opening_cash == Decimal("20.00")


@pytest.mark.asyncio
async def test_history_summary_is_owner_scoped(db, H, second_cashier):
    svc = CashierSessionService(db)
    opened = await svc.open(
        H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("10.00")),
    )
    closed = await svc.close(
        H["device_a"].id, H["user_a"].id, H["tenant_a"].id,
        SessionCloseRequest(closing_cash=Decimal("10.00")),
    )

    with pytest.raises(NotFoundError):
        await svc.history_summary(closed.session.id, second_cashier.id, H["tenant_a"].id)

    with pytest.raises(NotFoundError):
        await svc.history_summary(closed.session.id, H["user_a"].id, H["tenant_b"].id)


# ── Cross-device exclusivity ─────────────────────────────────────

@pytest_asyncio.fixture
async def device_b_same_branch(db, H):
    """A second device at H's own branch_a (H["device_a"]'s branch)."""
    device = Device(
        id=uuid4(), branch_id=H["branch_a"].id, device_code="POS-SECOND", letter="B",
        name="Second POS", device_type="POS", status=DeviceStatus.ACTIVE,
    )
    db.add(device)
    await db.flush()
    return device


@pytest.mark.asyncio
async def test_get_open_elsewhere_ignores_same_device(db, H, device_b_same_branch):
    svc = CashierSessionService(db)
    await svc.open(
        H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("100.00")),
    )

    same_device = await svc.get_open_elsewhere(H["user_a"].id, H["device_a"].id, H["tenant_a"].id)
    assert same_device is None

    other_device = await svc.get_open_elsewhere(H["user_a"].id, device_b_same_branch.id, H["tenant_a"].id)
    assert other_device is not None
    assert other_device.device_id == H["device_a"].id


@pytest.mark.asyncio
async def test_get_open_elsewhere_survives_more_than_one_match(db, H, device_b_same_branch):
    """If a login race (or legacy data) ever leaves this cashier with two
    simultaneously OPEN sessions on different devices — the exact state
    this method exists to detect and block on the *next* login — it must
    return one of them, not crash with MultipleResultsFound and lock the
    cashier out of logging in anywhere."""
    device_c = Device(
        id=uuid4(), branch_id=H["branch_a"].id, device_code="POS-THIRD", letter="C",
        name="Third POS", device_type="POS", status=DeviceStatus.ACTIVE,
    )
    db.add(device_c)
    await db.flush()

    svc = CashierSessionService(db)
    await svc.open(
        H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("100.00")),
    )
    await svc.open(
        device_b_same_branch.id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("50.00")),
    )

    result = await svc.get_open_elsewhere(H["user_a"].id, device_c.id, H["tenant_a"].id)
    assert result is not None
    assert result.device_id in {H["device_a"].id, device_b_same_branch.id}


async def _grant_pos_operate(db, user_id, tenant_id):
    role = Role(id=uuid4(), tenant_id=tenant_id, name="Cashier", is_active=True)
    db.add(role)
    await db.flush()
    db.add(UserRole(id=uuid4(), user_id=user_id, role_id=role.id))
    pid = await db.scalar(select(Permission.id).where(Permission.code == "pos.operate"))
    db.add(RolePermission(id=uuid4(), role_id=role.id, permission_id=pid))
    await db.flush()


async def _cashier_login(db, username, password, device_token):
    async def override():
        yield db
    app.dependency_overrides[get_db] = override
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test.local") as client:
            return await client.post(
                "/api/v1/pos/auth/cashier",
                json={"username": username, "password": password},
                headers={"Authorization": "Bearer " + device_token},
            )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_blocked_on_second_device_with_open_shift(db, H, device_b_same_branch):
    H["user_a"].all_branches = True
    await _grant_pos_operate(db, H["user_a"].id, H["tenant_a"].id)

    svc = CashierSessionService(db)
    await svc.open(
        H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("100.00")),
    )

    device_b_token = create_device_token(
        device_id=device_b_same_branch.id, branch_id=H["branch_a"].id, tenant_id=H["tenant_a"].id,
    )
    resp = await _cashier_login(db, H["user_a"].username, "Test1234!", device_b_token)
    assert resp.status_code == 403
    assert resp.json().get("code") == "SHIFT_OPEN_ELSEWHERE"


@pytest.mark.asyncio
async def test_login_allowed_on_same_device_with_own_open_shift(db, H, device_b_same_branch):
    H["user_a"].all_branches = True
    await _grant_pos_operate(db, H["user_a"].id, H["tenant_a"].id)

    svc = CashierSessionService(db)
    await svc.open(
        H["device_a"].id, H["user_a"].id, H["branch_a"].id, H["tenant_a"].id,
        SessionOpenRequest(opening_cash=Decimal("100.00")),
    )

    device_a_token = create_device_token(
        device_id=H["device_a"].id, branch_id=H["branch_a"].id, tenant_id=H["tenant_a"].id,
    )
    resp = await _cashier_login(db, H["user_a"].username, "Test1234!", device_a_token)
    assert resp.status_code == 200
