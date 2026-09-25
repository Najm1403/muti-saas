# tests/test_platform_hr.py
#
# Platform HR module (SaaS-company staff):
#   1. employee CRUD + auto "PLT-0001" numbering
#   2. salary payment CRUD, net computation, one-row-per-period guard
#   3. payroll register + analytics

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

from core.exceptions import ConflictError, NotFoundError
from schemas.platform_employee import (
    PlatformEmployeeCreate,
    PlatformEmployeeUpdate,
    PlatformSalaryPaymentCreate,
    PlatformSalaryPaymentUpdate,
)
from services.platform_hr_service import PlatformHRService


@pytest_asyncio.fixture
async def svc(db):
    return PlatformHRService(db)


def _emp(**kw):
    base = dict(full_name="Sam Platform", designation="Engineer", department="Product",
                monthly_salary=Decimal("120000"))
    base.update(kw)
    return PlatformEmployeeCreate(**base)


class TestEmployees:
    @pytest.mark.asyncio
    async def test_auto_numbering_global(self, svc):
        e1 = await svc.create_employee(_emp(full_name="One"))
        e2 = await svc.create_employee(_emp(full_name="Two"))
        assert e1.employee_no == "PLT-0001"
        assert e2.employee_no == "PLT-0002"

    @pytest.mark.asyncio
    async def test_numbering_not_recycled(self, svc):
        e1 = await svc.create_employee(_emp())
        await svc.delete_employee(e1.id)
        e2 = await svc.create_employee(_emp())
        assert e2.employee_no == "PLT-0002"

    @pytest.mark.asyncio
    async def test_update_and_filter(self, svc):
        e = await svc.create_employee(_emp(department="Sales"))
        await svc.update_employee(e.id, PlatformEmployeeUpdate(status="on_leave"))
        assert (await svc.list_employees(status="on_leave"))[0].id == e.id
        assert (await svc.list_employees(status="active")) == []
        assert "Sales" in await svc.departments()

    @pytest.mark.asyncio
    async def test_missing_employee(self, svc):
        with pytest.raises(NotFoundError):
            await svc.get_employee(uuid4())


class TestSalaryPayments:
    @pytest.mark.asyncio
    async def test_net_and_defaults(self, svc):
        e = await svc.create_employee(_emp(monthly_salary=Decimal("100000")))
        p = await svc.create_payment(None, PlatformSalaryPaymentCreate(
            platform_employee_id=e.id, period_month=9, period_year=2026,
            bonus=Decimal("10000"), deductions=Decimal("4000"),
        ))
        assert p.gross_amount == Decimal("100000.00")
        assert p.net_amount == Decimal("106000.00")
        assert p.status == "paid" and p.payment_date is not None
        assert p.period == "2026-09"

    @pytest.mark.asyncio
    async def test_one_row_per_period(self, svc):
        e = await svc.create_employee(_emp())
        await svc.create_payment(None, PlatformSalaryPaymentCreate(
            platform_employee_id=e.id, period_month=9, period_year=2026))
        with pytest.raises(ConflictError):
            await svc.create_payment(None, PlatformSalaryPaymentCreate(
                platform_employee_id=e.id, period_month=9, period_year=2026))

    @pytest.mark.asyncio
    async def test_update_recomputes_net(self, svc):
        e = await svc.create_employee(_emp(monthly_salary=Decimal("90000")))
        p = await svc.create_payment(None, PlatformSalaryPaymentCreate(
            platform_employee_id=e.id, period_month=1, period_year=2026))
        p2 = await svc.update_payment(p.id, PlatformSalaryPaymentUpdate(bonus=Decimal("1000")))
        assert p2.net_amount == Decimal("91000.00")


class TestRegisterAndSummary:
    @pytest.mark.asyncio
    async def test_register_statuses(self, svc):
        paid = await svc.create_employee(_emp(full_name="Paid", monthly_salary=Decimal("10000")))
        pend = await svc.create_employee(_emp(full_name="Pending", monthly_salary=Decimal("20000")))
        await svc.create_employee(_emp(full_name="Unpaid", monthly_salary=Decimal("30000")))

        await svc.create_payment(None, PlatformSalaryPaymentCreate(
            platform_employee_id=paid.id, period_month=6, period_year=2026, status="paid"))
        await svc.create_payment(None, PlatformSalaryPaymentCreate(
            platform_employee_id=pend.id, period_month=6, period_year=2026, status="pending"))

        reg = await svc.payroll_register(6, 2026)
        assert reg.headcount == 3
        assert (reg.paid_count, reg.pending_count, reg.unpaid_count) == (1, 1, 1)
        assert reg.net_paid_total == Decimal("10000.00")
        assert reg.net_pending_total == Decimal("20000.00")

    @pytest.mark.asyncio
    async def test_summary_shape(self, svc):
        e = await svc.create_employee(_emp(monthly_salary=Decimal("120000"), department="Eng"))
        today = date.today()
        await svc.create_payment(None, PlatformSalaryPaymentCreate(
            platform_employee_id=e.id, period_month=today.month, period_year=today.year, status="paid"))
        s = await svc.summary()
        assert s.headcount_active == 1
        assert s.monthly_commitment == Decimal("120000.00")
        assert s.this_month_net_paid == Decimal("120000.00")
        assert s.this_month_coverage_pct == 100.0
        assert len(s.by_month) == 6
        assert any(d.department == "Eng" for d in s.by_department)
