# tests/test_hr.py
#
# Tenant HR module:
#   1. employee CRUD + auto "EMP-0001" numbering + tenant isolation
#   2. salary payment CRUD, net computation, one-row-per-period guard
#   3. payroll register (paid / pending / unpaid) + analytics
#   4. permission resolution + require_permission gate

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select

from api.dependencies import CurrentUser, get_user_permissions, require_permission
from core.exceptions import ConflictError, ForbiddenError, NotFoundError
from models.permission import Permission
from models.role import Role
from models.role_permission import RolePermission
from models.user_role import UserRole
from schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    SalaryPaymentCreate,
    SalaryPaymentUpdate,
)
from services.hr_service import HRService


@pytest_asyncio.fixture
async def svc(db):
    return HRService(db)


async def _grant(db, user_id, tenant_id, *codes, role_name="Staff"):
    role = Role(id=uuid4(), tenant_id=tenant_id, name=role_name, is_active=True)
    db.add(role)
    await db.flush()
    db.add(UserRole(id=uuid4(), user_id=user_id, role_id=role.id))
    for code in codes:
        pid = await db.scalar(select(Permission.id).where(Permission.code == code))
        db.add(RolePermission(id=uuid4(), role_id=role.id, permission_id=pid))
    await db.flush()
    return role


def _emp(**kw):
    base = dict(full_name="Jane Doe", designation="Cashier", department="Front",
                monthly_salary=Decimal("40000"))
    base.update(kw)
    return EmployeeCreate(**base)


# ── 1. employee CRUD + numbering + isolation ─────────────────

class TestEmployees:
    @pytest.mark.asyncio
    async def test_auto_numbering_per_tenant(self, svc, two_tenants):
        a, b = two_tenants["tenant_a"].id, two_tenants["tenant_b"].id
        e1 = await svc.create_employee(a, _emp(full_name="A One"))
        e2 = await svc.create_employee(a, _emp(full_name="A Two"))
        f1 = await svc.create_employee(b, _emp(full_name="B One"))
        assert e1.employee_no == "EMP-0001"
        assert e2.employee_no == "EMP-0002"
        assert f1.employee_no == "EMP-0001"          # each tenant starts at 1

    @pytest.mark.asyncio
    async def test_numbering_not_recycled_after_archive(self, svc, two_tenants):
        a = two_tenants["tenant_a"].id
        e1 = await svc.create_employee(a, _emp(full_name="One"))
        await svc.delete_employee(e1.id, a)
        e2 = await svc.create_employee(a, _emp(full_name="Two"))
        assert e2.employee_no == "EMP-0002"

    @pytest.mark.asyncio
    async def test_isolation(self, svc, two_tenants):
        a, b = two_tenants["tenant_a"].id, two_tenants["tenant_b"].id
        e = await svc.create_employee(a, _emp())
        assert await svc.list_employees(b) == []
        with pytest.raises(NotFoundError):
            await svc.get_employee(e.id, b)
        with pytest.raises(NotFoundError):
            await svc.update_employee(e.id, b, EmployeeUpdate(full_name="X"))

    @pytest.mark.asyncio
    async def test_update_and_filter(self, svc, two_tenants):
        a = two_tenants["tenant_a"].id
        e = await svc.create_employee(a, _emp(department="Kitchen"))
        await svc.update_employee(e.id, a, EmployeeUpdate(status="on_leave"))
        assert (await svc.list_employees(a, status="on_leave"))[0].id == e.id
        assert (await svc.list_employees(a, status="active")) == []
        assert "Kitchen" in await svc.departments(a)

    @pytest.mark.asyncio
    async def test_bad_branch_rejected(self, svc, two_tenants):
        a = two_tenants["tenant_a"].id
        with pytest.raises(NotFoundError):
            await svc.create_employee(a, _emp(branch_id=uuid4()))


# ── 2. salary payments ──────────────────────────────────────

class TestSalaryPayments:
    @pytest.mark.asyncio
    async def test_net_computation_and_defaults(self, svc, two_tenants):
        a, uid = two_tenants["tenant_a"].id, two_tenants["user_a"].id
        e = await svc.create_employee(a, _emp(monthly_salary=Decimal("40000")))
        p = await svc.create_payment(a, uid, SalaryPaymentCreate(
            employee_id=e.id, period_month=9, period_year=2026,
            bonus=Decimal("5000"), deductions=Decimal("2000"),
        ))
        assert p.gross_amount == Decimal("40000.00")     # defaulted from employee
        assert p.net_amount == Decimal("43000.00")       # 40000 + 5000 - 2000
        assert p.status == "paid" and p.payment_date is not None
        assert p.period == "2026-09"
        assert p.employee_no == "EMP-0001"

    @pytest.mark.asyncio
    async def test_one_row_per_period(self, svc, two_tenants):
        a, uid = two_tenants["tenant_a"].id, two_tenants["user_a"].id
        e = await svc.create_employee(a, _emp())
        await svc.create_payment(a, uid, SalaryPaymentCreate(
            employee_id=e.id, period_month=9, period_year=2026))
        with pytest.raises(ConflictError):
            await svc.create_payment(a, uid, SalaryPaymentCreate(
                employee_id=e.id, period_month=9, period_year=2026))

    @pytest.mark.asyncio
    async def test_update_recomputes_net(self, svc, two_tenants):
        a, uid = two_tenants["tenant_a"].id, two_tenants["user_a"].id
        e = await svc.create_employee(a, _emp(monthly_salary=Decimal("30000")))
        p = await svc.create_payment(a, uid, SalaryPaymentCreate(
            employee_id=e.id, period_month=1, period_year=2026))
        p2 = await svc.update_payment(p.id, a, SalaryPaymentUpdate(deductions=Decimal("1000")))
        assert p2.net_amount == Decimal("29000.00")

    @pytest.mark.asyncio
    async def test_pending_then_mark_paid(self, svc, two_tenants):
        a, uid = two_tenants["tenant_a"].id, two_tenants["user_a"].id
        e = await svc.create_employee(a, _emp())
        p = await svc.create_payment(a, uid, SalaryPaymentCreate(
            employee_id=e.id, period_month=2, period_year=2026, status="pending"))
        assert p.status == "pending" and p.payment_date is None
        p2 = await svc.update_payment(p.id, a, SalaryPaymentUpdate(status="paid"))
        assert p2.status == "paid" and p2.payment_date is not None

    @pytest.mark.asyncio
    async def test_salary_payment_tenant_isolation(self, svc, two_tenants):
        """Tenant B can never see, edit, delete or reference tenant A's payroll."""
        a, ua = two_tenants["tenant_a"].id, two_tenants["user_a"].id
        b, ub = two_tenants["tenant_b"].id, two_tenants["user_b"].id

        emp_a = await svc.create_employee(a, _emp(full_name="A Cook"))
        pay_a = await svc.create_payment(a, ua, SalaryPaymentCreate(
            employee_id=emp_a.id, period_month=6, period_year=2026, status="paid"))

        # B's list / get / mutate against A's rows
        assert await svc.list_payments(b) == []
        with pytest.raises(NotFoundError):
            await svc.get_payment(pay_a.id, b)
        with pytest.raises(NotFoundError):
            await svc.update_payment(pay_a.id, b, SalaryPaymentUpdate(bonus=Decimal("1")))
        with pytest.raises(NotFoundError):
            await svc.delete_payment(pay_a.id, b)
        # B cannot attach a payment to A's employee
        with pytest.raises(NotFoundError):
            await svc.create_payment(b, ub, SalaryPaymentCreate(
                employee_id=emp_a.id, period_month=7, period_year=2026))
        # B's register / summary never include A's employee
        reg_b = await svc.payroll_register(b, 6, 2026)
        assert all(r.employee_id != emp_a.id for r in reg_b.rows)


# ── 3. register + analytics ─────────────────────────────────

class TestPayrollRegister:
    @pytest.mark.asyncio
    async def test_register_statuses(self, svc, two_tenants):
        a, uid = two_tenants["tenant_a"].id, two_tenants["user_a"].id
        paid_emp = await svc.create_employee(a, _emp(full_name="Paid", monthly_salary=Decimal("10000")))
        pend_emp = await svc.create_employee(a, _emp(full_name="Pending", monthly_salary=Decimal("20000")))
        await svc.create_employee(a, _emp(full_name="Unpaid", monthly_salary=Decimal("30000")))

        await svc.create_payment(a, uid, SalaryPaymentCreate(
            employee_id=paid_emp.id, period_month=6, period_year=2026, status="paid"))
        await svc.create_payment(a, uid, SalaryPaymentCreate(
            employee_id=pend_emp.id, period_month=6, period_year=2026, status="pending"))

        reg = await svc.payroll_register(a, 6, 2026)
        assert reg.headcount == 3
        assert reg.paid_count == 1 and reg.pending_count == 1 and reg.unpaid_count == 1
        assert reg.net_paid_total == Decimal("10000.00")
        assert reg.net_pending_total == Decimal("20000.00")
        by_status = {r.full_name: r.status for r in reg.rows}
        assert by_status == {"Paid": "paid", "Pending": "pending", "Unpaid": "unpaid"}

    @pytest.mark.asyncio
    async def test_summary_shape(self, svc, two_tenants):
        a, uid = two_tenants["tenant_a"].id, two_tenants["user_a"].id
        e = await svc.create_employee(a, _emp(monthly_salary=Decimal("50000"), department="Ops"))
        today = date.today()
        await svc.create_payment(a, uid, SalaryPaymentCreate(
            employee_id=e.id, period_month=today.month, period_year=today.year, status="paid"))
        s = await svc.summary(a)
        assert s.headcount_active == 1
        assert s.monthly_commitment == Decimal("50000.00")
        assert s.this_month_net_paid == Decimal("50000.00")
        assert s.this_month_coverage_pct == 100.0
        assert len(s.by_month) == 6
        assert any(d.department == "Ops" for d in s.by_department)


# ── 4. permissions ─────────────────────────────────────────

class TestPermissions:
    @pytest.mark.asyncio
    async def test_view_only_blocks_manage(self, db, two_tenants):
        u, t = two_tenants["user_a"].id, two_tenants["tenant_a"].id
        await _grant(db, u, t, "employees.view", "salaries.view")
        perms = await get_user_permissions(db, u, t)
        assert perms == {"employees.view", "salaries.view"}

        cu = CurrentUser(user_id=u, tenant_id=t)
        assert (await require_permission("employees.view")(current_user=cu, db=db)) is cu
        with pytest.raises(ForbiddenError) as ei:
            await require_permission("salaries.manage")(current_user=cu, db=db)
        assert ei.value.code == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_admin_role_bypass(self, db, two_tenants):
        u, t = two_tenants["user_a"].id, two_tenants["tenant_a"].id
        await _grant(db, u, t, role_name="Owner")
        dep = require_permission("salaries.manage")
        assert (await dep(current_user=CurrentUser(user_id=u, tenant_id=t), db=db)).user_id == u
