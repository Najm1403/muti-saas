# tests/test_employee_user_link.py
#
# A User (POS/dashboard login) can only be created by promoting an existing,
# active Employee — see UserService.create(). This is the fix for the
# attendance "no employee record is linked" bug: previously nothing ever set
# Employee.user_id, so every PIN punch failed. Now the link is a byproduct of
# how a User is created at all, and Employee itself carries an independent
# attendance PIN so employees who never become Users can still clock in/out
# (see tests/test_attendance.py).

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select

from core.exceptions import ConflictError, NotFoundError, ValidationError
from models.employee import Employee
from schemas.employee import EmployeeSetPin, EmployeeUpdate
from schemas.user import UserCreate
from services.hr_service import HRService
from services.user_service import UserService


async def _employee(db, tenant_id, *, status="active", user_id=None, full_name="Ada Cashier"):
    emp = Employee(
        id=uuid4(), tenant_id=tenant_id, employee_no=f"EMP-{uuid4().hex[:6]}", seq=1,
        full_name=full_name, status=status, user_id=user_id,
    )
    db.add(emp)
    await db.flush()
    return emp


@pytest.mark.asyncio
async def test_create_user_links_employee_and_derives_full_name(db, H):
    emp = await _employee(db, H["tenant_a"].id, full_name="Ada Cashier")
    svc = UserService(db)

    user = await svc.create(
        tenant_id=H["tenant_a"].id,
        data=UserCreate(employee_id=emp.id, username="ada_cashier", password="Passw0rd!"),
    )
    assert user.full_name == "Ada Cashier"

    await db.refresh(emp)
    assert emp.user_id == user.id


@pytest.mark.asyncio
async def test_create_user_rejects_unknown_employee(db, H):
    svc = UserService(db)
    with pytest.raises(NotFoundError):
        await svc.create(
            tenant_id=H["tenant_a"].id,
            data=UserCreate(employee_id=uuid4(), username="ghost", password="Passw0rd!"),
        )


@pytest.mark.asyncio
async def test_create_user_rejects_cross_tenant_employee(db, H):
    emp_b = await _employee(db, H["tenant_b"].id)
    svc = UserService(db)
    with pytest.raises(NotFoundError):
        await svc.create(
            tenant_id=H["tenant_a"].id,
            data=UserCreate(employee_id=emp_b.id, username="sneaky", password="Passw0rd!"),
        )


@pytest.mark.asyncio
async def test_create_user_rejects_inactive_employee(db, H):
    emp = await _employee(db, H["tenant_a"].id, status="terminated")
    svc = UserService(db)
    with pytest.raises(ValidationError, match="active"):
        await svc.create(
            tenant_id=H["tenant_a"].id,
            data=UserCreate(employee_id=emp.id, username="exstaff", password="Passw0rd!"),
        )


@pytest.mark.asyncio
async def test_create_user_rejects_already_linked_employee(db, H):
    emp = await _employee(db, H["tenant_a"].id)
    svc = UserService(db)
    await svc.create(
        tenant_id=H["tenant_a"].id,
        data=UserCreate(employee_id=emp.id, username="first_link", password="Passw0rd!"),
    )
    with pytest.raises(ValidationError, match="already linked"):
        await svc.create(
            tenant_id=H["tenant_a"].id,
            data=UserCreate(employee_id=emp.id, username="second_link", password="Passw0rd!"),
        )


@pytest.mark.asyncio
async def test_list_employees_unlinked_filter(db, H):
    linked = await _employee(db, H["tenant_a"].id, full_name="Linked One")
    svc = UserService(db)
    await svc.create(
        tenant_id=H["tenant_a"].id,
        data=UserCreate(employee_id=linked.id, username="linked_one", password="Passw0rd!"),
    )
    unlinked = await _employee(db, H["tenant_a"].id, full_name="Unlinked One")

    hr = HRService(db)
    results = await hr.list_employees(tenant_id=H["tenant_a"].id, unlinked=True)
    ids = {r.id for r in results}
    assert unlinked.id in ids
    assert linked.id not in ids


# ── Employee.user_id uniqueness (defense in depth alongside the DB constraint) ──

@pytest.mark.asyncio
async def test_employee_update_rejects_linking_to_already_linked_user(db, H):
    emp1 = await _employee(db, H["tenant_a"].id, full_name="First")
    emp2 = await _employee(db, H["tenant_a"].id, full_name="Second")
    svc = UserService(db)
    user = await svc.create(
        tenant_id=H["tenant_a"].id,
        data=UserCreate(employee_id=emp1.id, username="only_one", password="Passw0rd!"),
    )

    hr = HRService(db)
    with pytest.raises(ConflictError):
        await hr.update_employee(
            id=emp2.id, tenant_id=H["tenant_a"].id,
            data=EmployeeUpdate(user_id=user.id),
        )


# ── Employee attendance PIN ─────────────────────────────────────

@pytest.mark.asyncio
async def test_set_employee_pin_updates_has_pin(db, H):
    emp = await _employee(db, H["tenant_a"].id)
    hr = HRService(db)
    before = await hr.get_employee(emp.id, H["tenant_a"].id)
    assert before.has_pin is False

    after = await hr.set_pin(emp.id, H["tenant_a"].id, "4321")
    assert after.has_pin is True

    row = await db.scalar(select(Employee).where(Employee.id == emp.id))
    assert row.pin_hash is not None
