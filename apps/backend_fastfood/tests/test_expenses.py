# tests/test_expenses.py
#
# Covers the Expenses module:
#   1. category + expense CRUD, tenant isolation
#   2. monitor summary aggregation
#   3. "category in use" guard
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
from schemas.expense import ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCreate
from services.expense_service import ExpenseService


@pytest_asyncio.fixture
async def svc(db):
    return ExpenseService(db)


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


# ── 1. CRUD + isolation ──────────────────────────────────────

class TestCrud:
    @pytest.mark.asyncio
    async def test_category_and_expense_roundtrip(self, svc, two_tenants):
        a = two_tenants["tenant_a"].id
        cat = await svc.create_category(a, ExpenseCategoryCreate(name="Rent", monthly_budget=Decimal("50000")))
        assert cat.name == "Rent" and cat.monthly_budget == Decimal("50000.00")

        exp = await svc.create(
            a, two_tenants["user_a"].id,
            ExpenseCreate(category_id=cat.id, amount=Decimal("1200.00"),
                          expense_date=date(2026, 9, 1), payment_method="Bank", vendor="LL"),
        )
        assert exp.category_name == "Rent"
        assert exp.recorded_by == two_tenants["user_a"].id

        listed = await svc.list(a)
        assert len(listed) == 1 and listed[0].id == exp.id

        cats = await svc.list_categories(a)
        assert cats[0].expense_count == 1

    @pytest.mark.asyncio
    async def test_duplicate_category_rejected(self, svc, two_tenants):
        a = two_tenants["tenant_a"].id
        await svc.create_category(a, ExpenseCategoryCreate(name="Utilities"))
        with pytest.raises(ConflictError):
            await svc.create_category(a, ExpenseCategoryCreate(name="Utilities"))

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, svc, two_tenants):
        a, b = two_tenants["tenant_a"].id, two_tenants["tenant_b"].id
        cat = await svc.create_category(a, ExpenseCategoryCreate(name="Rent"))
        exp = await svc.create(
            a, two_tenants["user_a"].id,
            ExpenseCreate(category_id=cat.id, amount=Decimal("10"), expense_date=date(2026, 9, 1)),
        )
        assert await svc.list(b) == []
        with pytest.raises(NotFoundError):
            await svc.get(exp.id, b)
        with pytest.raises(NotFoundError):
            await svc.update_category(cat.id, b, ExpenseCategoryUpdate(name="X"))

    @pytest.mark.asyncio
    async def test_delete_category_in_use_blocked(self, svc, two_tenants):
        a = two_tenants["tenant_a"].id
        cat = await svc.create_category(a, ExpenseCategoryCreate(name="Rent"))
        await svc.create(a, two_tenants["user_a"].id,
                         ExpenseCreate(category_id=cat.id, amount=Decimal("5"), expense_date=date(2026, 9, 1)))
        with pytest.raises(ConflictError):
            await svc.delete_category(cat.id, a)


# ── 2. summary ───────────────────────────────────────────────

class TestSummary:
    @pytest.mark.asyncio
    async def test_aggregation(self, svc, two_tenants):
        a, uid = two_tenants["tenant_a"].id, two_tenants["user_a"].id
        rent = await svc.create_category(a, ExpenseCategoryCreate(name="Rent", monthly_budget=Decimal("1000")))
        food = await svc.create_category(a, ExpenseCategoryCreate(name="Food"))
        for cat, amt, d, m in [
            (rent, "600", date(2026, 8, 5), "Cash"),
            (rent, "600", date(2026, 9, 5), "Bank"),
            (food, "150", date(2026, 9, 6), "Cash"),
        ]:
            await svc.create(a, uid, ExpenseCreate(
                category_id=cat.id, amount=Decimal(amt), expense_date=d, payment_method=m))

        s = await svc.summary(a, date(2026, 1, 1), date(2026, 12, 31))
        assert s.total == Decimal("1350.00")
        assert s.count == 3
        cats = {c.name: c for c in s.by_category}
        assert cats["Rent"].total == Decimal("1200.00") and cats["Rent"].budget == Decimal("1000.00")
        assert cats["Food"].total == Decimal("150.00")
        months = {p.month: p.total for p in s.by_month}
        assert months["2026-08"] == Decimal("600.00") and months["2026-09"] == Decimal("750.00")
        methods = {m.method: m.total for m in s.by_payment_method}
        assert methods["Cash"] == Decimal("750.00") and methods["Bank"] == Decimal("600.00")


# ── 3. permissions ───────────────────────────────────────────

class TestPermissions:
    @pytest.mark.asyncio
    async def test_plain_user_has_no_permissions(self, db, two_tenants):
        perms = await get_user_permissions(db, two_tenants["user_a"].id, two_tenants["tenant_a"].id)
        assert perms == set()

    @pytest.mark.asyncio
    async def test_granting_view_only(self, db, two_tenants):
        u, t = two_tenants["user_a"].id, two_tenants["tenant_a"].id
        await _grant(db, u, t, "expenses.view")
        perms = await get_user_permissions(db, u, t)
        assert perms == {"expenses.view"}

        view_dep = require_permission("expenses.view")
        manage_dep = require_permission("expenses.manage")
        cu = CurrentUser(user_id=u, tenant_id=t)
        assert (await view_dep(current_user=cu, db=db)) is cu
        with pytest.raises(ForbiddenError) as ei:
            await manage_dep(current_user=cu, db=db)
        assert ei.value.code == "PERMISSION_DENIED"

    @pytest.mark.asyncio
    async def test_admin_role_bypasses(self, db, two_tenants):
        u, t = two_tenants["user_a"].id, two_tenants["tenant_a"].id
        await _grant(db, u, t, role_name="Admin")
        perms = await get_user_permissions(db, u, t)
        assert perms == {"*"}
        dep = require_permission("expenses.manage")
        assert (await dep(current_user=CurrentUser(user_id=u, tenant_id=t), db=db)).user_id == u

    @pytest.mark.asyncio
    async def test_all_branches_does_not_grant_admin(self, db, two_tenants):
        u = two_tenants["user_a"]
        u.all_branches = True
        await db.flush()
        perms = await get_user_permissions(db, u.id, two_tenants["tenant_a"].id)
        assert perms == set()
