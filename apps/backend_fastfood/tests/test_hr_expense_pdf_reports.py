# tests/test_hr_expense_pdf_reports.py
#
# Smoke-level coverage for the server-side PDF exports added to the
# Employees, Salaries and Expenses tenant-dashboard pages (reportlab, real
# A4 documents — see services/pdf_report_service.py), matching the pattern
# already covered for Inventory in test_pdf_reports.py. Confirms each route
# returns a genuine, non-trivial PDF, that its filters narrow the rows the
# same way the on-screen table does, and that route registration order
# doesn't let "/pdf" get swallowed by a "/{id}" route (a real footgun for
# any router that adds a static path alongside a UUID path param).

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from schemas.employee import EmployeeCreate, SalaryPaymentCreate
from schemas.expense import ExpenseCategoryCreate, ExpenseCreate
from services.expense_service import ExpenseService
from services.hr_service import HRService
from tests.test_pdf_reports import _assert_pdf, _get, _grant_admin


@pytest.mark.asyncio
async def test_employee_register_pdf(db, H):
    H["user_a"].all_branches = True
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)
    hr = HRService(db)
    await hr.create_employee(H["tenant_a"].id, EmployeeCreate(
        full_name="Jane Doe", designation="Cashier", department="Front",
        monthly_salary=Decimal("40000"),
    ))
    await hr.create_employee(H["tenant_a"].id, EmployeeCreate(
        full_name="Amir Khan", designation="Cook", department="Kitchen",
        monthly_salary=Decimal("35000"), status="on_leave",
    ))

    all_rows = _assert_pdf(await _get(db, H, "/api/v1/employees/pdf"))
    filtered = _assert_pdf(await _get(db, H, "/api/v1/employees/pdf?status=on_leave"))
    # The filtered export (1 row) must be a smaller document than the full
    # one (2 rows) — a cheap but real signal that the status filter actually
    # reached the query instead of being silently ignored.
    assert len(filtered) < len(all_rows)


@pytest.mark.asyncio
async def test_employee_register_pdf_route_not_swallowed_by_id_route(db, H):
    """'/employees/pdf' must resolve to the PDF export, not fall into
    '/employees/{id}' and 422 on trying to parse "pdf" as a UUID — the
    route order in api/v1/employees.py is what prevents that."""
    H["user_a"].all_branches = True
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)
    resp = await _get(db, H, "/api/v1/employees/pdf")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_payroll_register_pdf(db, H):
    H["user_a"].all_branches = True
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)
    hr = HRService(db)
    emp = await hr.create_employee(H["tenant_a"].id, EmployeeCreate(
        full_name="Jane Doe", monthly_salary=Decimal("40000"),
    ))
    today = date.today()
    await hr.create_payment(
        tenant_id=H["tenant_a"].id, recorded_by=H["user_a"].id,
        data=SalaryPaymentCreate(
            employee_id=emp.id, period_month=today.month, period_year=today.year,
            gross_amount=Decimal("40000"), status="paid", payment_date=today,
        ),
    )

    empty = _assert_pdf(await _get(
        db, H, f"/api/v1/salaries/register/pdf?month={today.month}&year={today.year}&status=pending",
    ))
    full = _assert_pdf(await _get(
        db, H, f"/api/v1/salaries/register/pdf?month={today.month}&year={today.year}",
    ))
    assert len(full) > len(empty)


@pytest.mark.asyncio
async def test_expense_register_pdf(db, H):
    H["user_a"].all_branches = True
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)
    svc = ExpenseService(db)
    cat = await svc.create_category(H["tenant_a"].id, ExpenseCategoryCreate(name="Utilities"))
    today = date.today()
    await svc.create(
        tenant_id=H["tenant_a"].id, recorded_by=H["user_a"].id,
        data=ExpenseCreate(category_id=cat.id, amount=Decimal("1500.00"), expense_date=today, vendor="K-Electric"),
    )

    empty = _assert_pdf(await _get(
        db, H, f"/api/v1/expenses/pdf?date_from={today.isoformat()}&date_to={today.isoformat()}&payment_method=Bank",
    ))
    full = _assert_pdf(await _get(db, H, "/api/v1/expenses/pdf"))
    assert len(full) > len(empty)


@pytest.mark.asyncio
async def test_expense_register_pdf_empty_selection_still_renders(db, H):
    H["user_a"].all_branches = True
    await _grant_admin(db, H["user_a"].id, H["tenant_a"].id)
    resp = await _get(db, H, "/api/v1/expenses/pdf?payment_method=Cheque")
    _assert_pdf(resp)
