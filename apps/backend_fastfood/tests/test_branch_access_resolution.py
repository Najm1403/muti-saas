# tests/test_branch_access_resolution.py
#
# api/branch_access.py's per-resource branch resolution: before this fix,
# only "devices" and "sales" resources (plus the special-cased
# /refunds/sale/{sale_id}) were ever resolved to a branch from their "{id}"
# path param — every other branch-scoped module (employees, expenses,
# salaries) silently fell through to the unconditional "choose a branch"
# 403 for a branch-scoped user hitting GET/PATCH/DELETE /{id} without an
# explicit branch_id in the query string or body, even for a resource
# genuinely inside their own assigned branch. See
# _resolve_resource_branch's docstring for the reasoning.

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from api.branch_access import _resolve_resource_branch
from models.branch import Branch
from models.user_branch import UserBranch
from schemas.employee import EmployeeCreate, SalaryPaymentCreate
from schemas.expense import ExpenseCategoryCreate, ExpenseCreate
from services.expense_service import ExpenseService
from services.hr_service import HRService
from tests.test_deployment_regressions import call
from tests.test_hr import _grant


async def _second_branch(db, H):
    branch = Branch(
        id=uuid4(), business_id=H["biz_a"].id, branch_code=f"BR-{uuid4().hex[:6]}",
        name="Second Branch", is_active=True,
    )
    db.add(branch)
    await db.flush()
    return branch


async def _scope_user_to_branch(db, H, branch_id):
    H["user_a"].all_branches = False
    db.add(UserBranch(user_id=H["user_a"].id, branch_id=branch_id))
    await db.flush()


@pytest.mark.asyncio
async def test_resolve_resource_branch_covers_employees_expenses_salaries(db, H):
    hr = HRService(db)
    emp = await hr.create_employee(H["tenant_a"].id, EmployeeCreate(
        full_name="Jane", monthly_salary=Decimal("1000"), branch_id=H["branch_a"].id,
    ))
    exp_svc = ExpenseService(db)
    cat = await exp_svc.create_category(H["tenant_a"].id, ExpenseCategoryCreate(name="Utilities"))
    expense = await exp_svc.create(
        tenant_id=H["tenant_a"].id, recorded_by=H["user_a"].id,
        data=ExpenseCreate(category_id=cat.id, branch_id=H["branch_a"].id,
                            amount=Decimal("10"), expense_date=date.today()),
    )
    payment = await hr.create_payment(
        tenant_id=H["tenant_a"].id, recorded_by=H["user_a"].id,
        data=SalaryPaymentCreate(
            employee_id=emp.id, period_month=date.today().month, period_year=date.today().year,
            gross_amount=Decimal("1000"), status="paid",
        ),
    )

    assert await _resolve_resource_branch(db, "employees", "/api/v1/employees/x", emp.id) == H["branch_a"].id
    assert await _resolve_resource_branch(db, "expenses", "/api/v1/expenses/x", expense.id) == H["branch_a"].id
    assert await _resolve_resource_branch(db, "salaries", "/api/v1/salaries/x", payment.id) == H["branch_a"].id


@pytest.mark.asyncio
async def test_resolve_resource_branch_unhandled_module_returns_none(db, H):
    """A module this function doesn't know how to resolve must return None
    (not raise, not guess) — the caller falls back to an explicit
    branch_id, unchanged from before this function existed."""
    assert await _resolve_resource_branch(db, "reports", "/api/v1/reports/x", uuid4()) is None


@pytest.mark.asyncio
async def test_branch_scoped_user_can_view_employee_in_their_own_branch(db, H):
    await _scope_user_to_branch(db, H, H["branch_a"].id)
    await _grant(db, H["user_a"].id, H["tenant_a"].id, "employees.view")
    hr = HRService(db)
    emp = await hr.create_employee(H["tenant_a"].id, EmployeeCreate(
        full_name="Jane", monthly_salary=Decimal("1000"), branch_id=H["branch_a"].id,
    ))

    resp = await call(db, H, "GET", f"/api/v1/employees/{emp.id}")
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_branch_scoped_user_denied_employee_in_a_different_branch(db, H):
    other_branch = await _second_branch(db, H)
    await _scope_user_to_branch(db, H, H["branch_a"].id)
    await _grant(db, H["user_a"].id, H["tenant_a"].id, "employees.view")
    hr = HRService(db)
    emp = await hr.create_employee(H["tenant_a"].id, EmployeeCreate(
        full_name="Jane", monthly_salary=Decimal("1000"), branch_id=other_branch.id,
    ))

    resp = await call(db, H, "GET", f"/api/v1/employees/{emp.id}")
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_branch_scoped_user_can_view_expense_in_their_own_branch(db, H):
    await _scope_user_to_branch(db, H, H["branch_a"].id)
    await _grant(db, H["user_a"].id, H["tenant_a"].id, "expenses.view")
    exp_svc = ExpenseService(db)
    cat = await exp_svc.create_category(H["tenant_a"].id, ExpenseCategoryCreate(name="Utilities"))
    expense = await exp_svc.create(
        tenant_id=H["tenant_a"].id, recorded_by=H["user_a"].id,
        data=ExpenseCreate(category_id=cat.id, branch_id=H["branch_a"].id,
                            amount=Decimal("10"), expense_date=date.today()),
    )

    resp = await call(db, H, "GET", f"/api/v1/expenses/{expense.id}")
    assert resp.status_code == 200, resp.text
