# tests/test_attendance.py
#
# Attendance (clock-in/out) — independent of CashierSession, tenant-isolated,
# and the pos.operate permission gate on cashier-token issuance that ships
# alongside it (see docs/ATTENDANCE.md).

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.main import app
from core.exceptions import NotFoundError, ValidationError
from core.security import create_access_token, hash_password
from db.session import get_db
from models.attendance_record import AttendanceRecord
from models.employee import Employee
from models.permission import Permission
from models.role import Role
from models.role_permission import RolePermission
from models.user_role import UserRole
from schemas.attendance import AttendanceCorrection, AttendanceManualCreate
from services.attendance_service import AttendanceService


async def _grant(db, user_id, tenant_id, *codes, role_name="Operator"):
    role = Role(id=uuid4(), tenant_id=tenant_id, name=role_name, is_active=True)
    db.add(role)
    await db.flush()
    db.add(UserRole(id=uuid4(), user_id=user_id, role_id=role.id))
    for code in codes:
        pid = await db.scalar(select(Permission.id).where(Permission.code == code))
        db.add(RolePermission(id=uuid4(), role_id=role.id, permission_id=pid))
    await db.flush()
    return role


async def _employee_for(db, user, tenant_id, branch_id=None, *, pin=None, full_name=None):
    emp = Employee(
        id=uuid4(), tenant_id=tenant_id, employee_no=f"EMP-{uuid4().hex[:6]}", seq=1,
        user_id=user.id if user else None, branch_id=branch_id,
        full_name=full_name or (user.full_name if user else "Test Employee"),
        pin_hash=hash_password(pin) if pin else None,
    )
    db.add(emp)
    await db.flush()
    return emp


# ── punch toggle — Employee PIN, independent of any User account ────

@pytest.mark.asyncio
async def test_punch_toggles_clock_in_and_out(db, H):
    # No linked User at all — an employee with no login can still punch
    # using their own attendance PIN, which is the whole point of this flow.
    emp = await _employee_for(db, None, H["tenant_a"].id, H["branch_a"].id, pin="1234")
    svc = AttendanceService(db)

    clocked_in = await svc.punch(
        tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id, device_id=H["device_a"].id,
        employee_id=emp.id, pin="1234",
    )
    assert clocked_in.action == "clocked_in"
    assert clocked_in.employee_id == emp.id
    assert clocked_in.clock_out_at is None

    clocked_out = await svc.punch(
        tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id, device_id=H["device_a"].id,
        employee_id=emp.id, pin="1234",
    )
    assert clocked_out.action == "clocked_out"
    assert clocked_out.id == clocked_in.id
    assert clocked_out.clock_out_at is not None

    # A third punch opens a brand new record — not the same row twice.
    reopened = await svc.punch(
        tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id, device_id=H["device_a"].id,
        employee_id=emp.id, pin="1234",
    )
    assert reopened.action == "clocked_in"
    assert reopened.id != clocked_in.id


@pytest.mark.asyncio
async def test_punch_rejects_wrong_pin(db, H):
    emp = await _employee_for(db, None, H["tenant_a"].id, H["branch_a"].id, pin="1234")
    svc = AttendanceService(db)
    with pytest.raises(ValidationError):
        await svc.punch(
            tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id, device_id=H["device_a"].id,
            employee_id=emp.id, pin="9999",
        )


@pytest.mark.asyncio
async def test_punch_rejects_employee_with_no_pin_set(db, H):
    emp = await _employee_for(db, None, H["tenant_a"].id, H["branch_a"].id)  # no pin
    svc = AttendanceService(db)
    with pytest.raises(ValidationError, match="no attendance PIN"):
        await svc.punch(
            tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id, device_id=H["device_a"].id,
            employee_id=emp.id, pin="1234",
        )


@pytest.mark.asyncio
async def test_punch_rejects_unknown_employee(db, H):
    svc = AttendanceService(db)
    with pytest.raises(ValidationError, match="Employee not found"):
        await svc.punch(
            tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id, device_id=H["device_a"].id,
            employee_id=uuid4(), pin="1234",
        )


@pytest.mark.asyncio
async def test_punch_records_linked_user_id_when_present(db, H):
    # An employee who *is* also a User still carries that cross-reference on
    # the resulting record, even though the punch itself only needs the PIN.
    emp = await _employee_for(db, H["user_a"], H["tenant_a"].id, H["branch_a"].id, pin="1234")
    svc = AttendanceService(db)
    await svc.punch(
        tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id, device_id=H["device_a"].id,
        employee_id=emp.id, pin="1234",
    )
    row = await db.scalar(select(AttendanceRecord).where(AttendanceRecord.employee_id == emp.id))
    assert row.user_id == H["user_a"].id


# ── staff list (attendance kiosk grid) ──────────────────────────

@pytest.mark.asyncio
async def test_list_staff_includes_branch_and_unassigned_employees(db, H):
    branch_emp = await _employee_for(db, None, H["tenant_a"].id, H["branch_a"].id, pin="1234")
    hq_emp = await _employee_for(db, None, H["tenant_a"].id, None, pin="1234")
    other_branch_emp = await _employee_for(db, None, H["tenant_a"].id, H["branch_b"].id, pin="1234")

    svc = AttendanceService(db)
    staff = await svc.list_staff(tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id)
    ids = {s.employee_id for s in staff}
    assert branch_emp.id in ids
    assert hq_emp.id in ids
    assert other_branch_emp.id not in ids


@pytest.mark.asyncio
async def test_list_staff_excludes_inactive_employees(db, H):
    emp = await _employee_for(db, None, H["tenant_a"].id, H["branch_a"].id, pin="1234")
    emp.status = "terminated"
    await db.flush()
    svc = AttendanceService(db)
    staff = await svc.list_staff(tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id)
    assert emp.id not in {s.employee_id for s in staff}


# ── database-level integrity: one open record per employee ─────

@pytest.mark.asyncio
async def test_db_rejects_two_simultaneous_open_records(db, H):
    emp = await _employee_for(db, H["user_a"], H["tenant_a"].id, H["branch_a"].id)
    now = datetime.now(timezone.utc)
    db.add(AttendanceRecord(
        tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id, employee_id=emp.id,
        clock_in_at=now, method="manual", source="dashboard",
    ))
    await db.flush()
    db.add(AttendanceRecord(
        tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id, employee_id=emp.id,
        clock_in_at=now + timedelta(minutes=1), method="manual", source="dashboard",
    ))
    with pytest.raises(IntegrityError):
        await db.flush()


# ── tenant isolation ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_manual_create_rejects_cross_tenant_employee(db, H):
    emp_b = await _employee_for(db, H["user_b"], H["tenant_b"].id, H["branch_b"].id)
    svc = AttendanceService(db)
    with pytest.raises(NotFoundError):
        await svc.manual_create(
            tenant_id=H["tenant_a"].id, recorded_by_user_id=H["user_a"].id,
            data=AttendanceManualCreate(
                employee_id=emp_b.id, branch_id=H["branch_a"].id,
                clock_in_at=datetime.now(timezone.utc), notes="cross-tenant attempt",
            ),
        )


@pytest.mark.asyncio
async def test_manual_create_rejects_cross_tenant_branch(db, H):
    emp_a = await _employee_for(db, H["user_a"], H["tenant_a"].id, H["branch_a"].id)
    svc = AttendanceService(db)
    with pytest.raises(NotFoundError):
        await svc.manual_create(
            tenant_id=H["tenant_a"].id, recorded_by_user_id=H["user_a"].id,
            data=AttendanceManualCreate(
                employee_id=emp_a.id, branch_id=H["branch_b"].id,
                clock_in_at=datetime.now(timezone.utc), notes="cross-tenant branch attempt",
            ),
        )


@pytest.mark.asyncio
async def test_list_never_returns_another_tenants_records(db, H):
    emp_a = await _employee_for(db, H["user_a"], H["tenant_a"].id, H["branch_a"].id)
    emp_b = await _employee_for(db, H["user_b"], H["tenant_b"].id, H["branch_b"].id)
    now = datetime.now(timezone.utc)
    db.add_all([
        AttendanceRecord(tenant_id=H["tenant_a"].id, branch_id=H["branch_a"].id, employee_id=emp_a.id,
                          clock_in_at=now, method="manual", source="dashboard"),
        AttendanceRecord(tenant_id=H["tenant_b"].id, branch_id=H["branch_b"].id, employee_id=emp_b.id,
                          clock_in_at=now, method="manual", source="dashboard"),
    ])
    await db.flush()

    svc = AttendanceService(db)
    rows = await svc.list(tenant_id=H["tenant_a"].id)
    assert len(rows) == 1
    assert rows[0].employee_id == emp_a.id
    assert all(r.tenant_id == H["tenant_a"].id for r in rows)


@pytest.mark.asyncio
async def test_correct_rejects_cross_tenant_record_id(db, H):
    emp_b = await _employee_for(db, H["user_b"], H["tenant_b"].id, H["branch_b"].id)
    record = AttendanceRecord(
        tenant_id=H["tenant_b"].id, branch_id=H["branch_b"].id, employee_id=emp_b.id,
        clock_in_at=datetime.now(timezone.utc), method="manual", source="dashboard",
    )
    db.add(record)
    await db.flush()

    svc = AttendanceService(db)
    with pytest.raises(NotFoundError):
        await svc.correct(
            tenant_id=H["tenant_a"].id, recorded_by_user_id=H["user_a"].id, id=record.id,
            data=AttendanceCorrection(notes="tenant A trying to edit tenant B's record"),
        )


# ── pos.operate permission gate on cashier-token issuance ───────

async def _allow_branch(db, user):
    """H's users aren't assigned to any branch by default; the login
    endpoints require it (GAP 3 branch-assignment check) before even
    reaching the pos.operate gate under test here."""
    user.all_branches = True
    await db.flush()


async def _staff_pin_login(db, user_id, pin, device_token):
    async def override():
        yield db
    app.dependency_overrides[get_db] = override
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test.local") as client:
            return await client.post(
                "/api/v1/pos/auth/staff-pin",
                json={"user_id": str(user_id), "pin": pin},
                headers={"Authorization": "Bearer " + device_token},
            )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_staff_pin_login_denied_without_pos_operate(db, H):
    from core.security import create_device_token
    await _allow_branch(db, H["user_a"])
    device_token = create_device_token(
        device_id=H["device_a"].id, branch_id=H["branch_a"].id, tenant_id=H["tenant_a"].id,
    )
    resp = await _staff_pin_login(db, H["user_a"].id, "Test1234!", device_token)
    assert resp.status_code == 403
    assert resp.json().get("code") == "POS_ACCESS_DENIED"


@pytest.mark.asyncio
async def test_staff_pin_login_allowed_with_pos_operate(db, H):
    from core.security import create_device_token
    await _allow_branch(db, H["user_a"])
    await _grant(db, H["user_a"].id, H["tenant_a"].id, "pos.operate")
    device_token = create_device_token(
        device_id=H["device_a"].id, branch_id=H["branch_a"].id, tenant_id=H["tenant_a"].id,
    )
    resp = await _staff_pin_login(db, H["user_a"].id, "Test1234!", device_token)
    assert resp.status_code == 200
    assert "cashier_token" in resp.json()


@pytest.mark.asyncio
async def test_staff_pin_login_allowed_for_admin_wildcard_role(db, H):
    from core.security import create_device_token
    await _allow_branch(db, H["user_a"])
    await _grant(db, H["user_a"].id, H["tenant_a"].id, role_name="Admin")
    device_token = create_device_token(
        device_id=H["device_a"].id, branch_id=H["branch_a"].id, tenant_id=H["tenant_a"].id,
    )
    resp = await _staff_pin_login(db, H["user_a"].id, "Test1234!", device_token)
    assert resp.status_code == 200
