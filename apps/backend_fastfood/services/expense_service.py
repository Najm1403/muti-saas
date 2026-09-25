# services/expense_service.py
#
# Tenant-scoped expense tracking: managed categories + individual records +
# a monitor summary (totals by month / category / branch / payment method).
# Soft-deletes throughout — nothing is hard-removed.

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError
from models.branch import Branch
from models.expense import Expense
from models.expense_category import ExpenseCategory
from models.business import Business
from models.user import User
from schemas.expense import (
    BranchBreakdown,
    CategoryBreakdown,
    ExpenseCategoryCreate,
    ExpenseCategoryResponse,
    ExpenseCategoryUpdate,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseSummary,
    ExpenseUpdate,
    MethodBreakdown,
    MonthPoint,
)

_ZERO = Decimal("0")


def _month_bounds(today: date) -> tuple[date, date]:
    start = today.replace(day=1)
    if start.month == 12:
        nxt = start.replace(year=start.year + 1, month=1)
    else:
        nxt = start.replace(month=start.month + 1)
    return start, nxt


class ExpenseService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Categories ───────────────────────────────────────────────

    async def _cat_or_404(self, id: UUID, tenant_id: UUID) -> ExpenseCategory:
        row = await self.db.execute(
            select(ExpenseCategory).where(
                ExpenseCategory.id == id,
                ExpenseCategory.tenant_id == tenant_id,
                ExpenseCategory.deleted_at.is_(None),
            )
        )
        cat = row.scalar_one_or_none()
        if not cat:
            raise NotFoundError("Expense category not found.")
        return cat

    async def _category_response(self, cat: ExpenseCategory) -> ExpenseCategoryResponse:
        m_start, m_end = _month_bounds(date.today())
        spent = await self.db.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.category_id == cat.id,
                Expense.deleted_at.is_(None),
                Expense.expense_date >= m_start,
                Expense.expense_date < m_end,
            )
        )
        count = await self.db.scalar(
            select(func.count(Expense.id)).where(
                Expense.category_id == cat.id, Expense.deleted_at.is_(None)
            )
        )
        return ExpenseCategoryResponse(
            **{
                "id": cat.id,
                "tenant_id": cat.tenant_id,
                "name": cat.name,
                "monthly_budget": cat.monthly_budget,
                "is_active": cat.is_active,
                "created_at": cat.created_at,
                "updated_at": cat.updated_at,
            },
            expense_count=int(count or 0),
            spent_this_month=Decimal(str(spent or 0)),
        )

    async def list_categories(self, tenant_id: UUID) -> list[ExpenseCategoryResponse]:
        rows = await self.db.execute(
            select(ExpenseCategory)
            .where(
                ExpenseCategory.tenant_id == tenant_id,
                ExpenseCategory.deleted_at.is_(None),
            )
            .order_by(ExpenseCategory.name)
        )
        return [await self._category_response(c) for c in rows.scalars().all()]

    async def create_category(
        self, tenant_id: UUID, data: ExpenseCategoryCreate
    ) -> ExpenseCategoryResponse:
        dup = await self.db.scalar(
            select(ExpenseCategory.id).where(
                ExpenseCategory.tenant_id == tenant_id,
                ExpenseCategory.name == data.name,
                ExpenseCategory.deleted_at.is_(None),
            )
        )
        if dup:
            raise ConflictError(f"A category named '{data.name}' already exists.")
        cat = ExpenseCategory(
            tenant_id=tenant_id, name=data.name, monthly_budget=data.monthly_budget
        )
        self.db.add(cat)
        await self.db.commit()
        await self.db.refresh(cat)
        return await self._category_response(cat)

    async def update_category(
        self, id: UUID, tenant_id: UUID, data: ExpenseCategoryUpdate
    ) -> ExpenseCategoryResponse:
        cat = await self._cat_or_404(id, tenant_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(cat, field, value)
        await self.db.commit()
        await self.db.refresh(cat)
        return await self._category_response(cat)

    async def delete_category(self, id: UUID, tenant_id: UUID) -> None:
        cat = await self._cat_or_404(id, tenant_id)
        in_use = await self.db.scalar(
            select(func.count(Expense.id)).where(
                Expense.category_id == cat.id, Expense.deleted_at.is_(None)
            )
        )
        if in_use:
            raise ConflictError(
                "This category is used by existing expenses. Reassign or delete them first."
            )
        cat.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    # ── Expenses ─────────────────────────────────────────────────

    async def _verify_branch(self, branch_id: UUID, tenant_id: UUID) -> None:
        ok = await self.db.scalar(
            select(Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Branch.id == branch_id,
                Business.tenant_id == tenant_id,
                Branch.deleted_at.is_(None),
                Business.deleted_at.is_(None),
            )
        )
        if not ok:
            raise NotFoundError("Branch not found.")

    def _base_select(self, tenant_id: UUID):
        return (
            select(
                Expense,
                ExpenseCategory.name.label("category_name"),
                Branch.name.label("branch_name"),
                User.full_name.label("recorded_by_name"),
            )
            .join(ExpenseCategory, Expense.category_id == ExpenseCategory.id)
            .outerjoin(Branch, Expense.branch_id == Branch.id)
            .outerjoin(User, Expense.recorded_by == User.id)
            .where(Expense.tenant_id == tenant_id, Expense.deleted_at.is_(None))
        )

    @staticmethod
    def _row_to_response(row) -> ExpenseResponse:
        e: Expense = row[0]
        return ExpenseResponse(
            id=e.id,
            tenant_id=e.tenant_id,
            category_id=e.category_id,
            category_name=row.category_name,
            branch_id=e.branch_id,
            branch_name=row.branch_name,
            amount=e.amount,
            expense_date=e.expense_date,
            payment_method=e.payment_method,
            vendor=e.vendor,
            reference=e.reference,
            note=e.note,
            recorded_by=e.recorded_by,
            recorded_by_name=row.recorded_by_name,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )

    async def list(
        self,
        tenant_id: UUID,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        category_id: UUID | None = None,
        branch_id: UUID | None = None,
        payment_method: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ExpenseResponse]:
        stmt = self._base_select(tenant_id)
        if date_from:
            stmt = stmt.where(Expense.expense_date >= date_from)
        if date_to:
            stmt = stmt.where(Expense.expense_date <= date_to)
        if category_id:
            stmt = stmt.where(Expense.category_id == category_id)
        if branch_id:
            stmt = stmt.where(Expense.branch_id == branch_id)
        if payment_method:
            stmt = stmt.where(Expense.payment_method == payment_method)
        stmt = stmt.order_by(Expense.expense_date.desc(), Expense.created_at.desc()).offset(skip).limit(limit)
        rows = await self.db.execute(stmt)
        return [self._row_to_response(r) for r in rows.all()]

    async def get(self, id: UUID, tenant_id: UUID) -> ExpenseResponse:
        rows = await self.db.execute(self._base_select(tenant_id).where(Expense.id == id))
        row = rows.first()
        if not row:
            raise NotFoundError("Expense not found.")
        return self._row_to_response(row)

    async def create(
        self, tenant_id: UUID, recorded_by: UUID, data: ExpenseCreate
    ) -> ExpenseResponse:
        await self._cat_or_404(data.category_id, tenant_id)
        if data.branch_id is not None:
            await self._verify_branch(data.branch_id, tenant_id)
        exp = Expense(
            tenant_id=tenant_id,
            category_id=data.category_id,
            branch_id=data.branch_id,
            amount=data.amount,
            expense_date=data.expense_date,
            payment_method=data.payment_method,
            vendor=data.vendor,
            reference=data.reference,
            note=data.note,
            recorded_by=recorded_by,
        )
        self.db.add(exp)
        await self.db.commit()
        return await self.get(exp.id, tenant_id)

    async def update(
        self, id: UUID, tenant_id: UUID, data: ExpenseUpdate
    ) -> ExpenseResponse:
        row = await self.db.execute(
            select(Expense).where(
                Expense.id == id,
                Expense.tenant_id == tenant_id,
                Expense.deleted_at.is_(None),
            )
        )
        exp = row.scalar_one_or_none()
        if not exp:
            raise NotFoundError("Expense not found.")
        fields = data.model_dump(exclude_unset=True)
        if "category_id" in fields and fields["category_id"]:
            await self._cat_or_404(fields["category_id"], tenant_id)
        for field, value in fields.items():
            setattr(exp, field, value)
        await self.db.commit()
        return await self.get(id, tenant_id)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        row = await self.db.execute(
            select(Expense).where(
                Expense.id == id,
                Expense.tenant_id == tenant_id,
                Expense.deleted_at.is_(None),
            )
        )
        exp = row.scalar_one_or_none()
        if not exp:
            raise NotFoundError("Expense not found.")
        exp.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    # ── Monitor / summary ───────────────────────────────────────

    async def summary(
        self, tenant_id: UUID, date_from: date | None, date_to: date | None
    ) -> ExpenseSummary:
        today = date.today()
        m_start, _ = _month_bounds(today)
        if date_from is None:
            date_from = m_start
        if date_to is None:
            date_to = today

        base = [
            Expense.tenant_id == tenant_id,
            Expense.deleted_at.is_(None),
            Expense.expense_date >= date_from,
            Expense.expense_date <= date_to,
        ]

        total = await self.db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(*base))
        count = await self.db.scalar(select(func.count(Expense.id)).where(*base))

        cat_rows = await self.db.execute(
            select(
                Expense.category_id,
                ExpenseCategory.name,
                ExpenseCategory.monthly_budget,
                func.sum(Expense.amount),
                func.count(Expense.id),
            )
            .join(ExpenseCategory, Expense.category_id == ExpenseCategory.id)
            .where(*base)
            .group_by(Expense.category_id, ExpenseCategory.name, ExpenseCategory.monthly_budget)
            .order_by(func.sum(Expense.amount).desc())
        )
        by_category = [
            CategoryBreakdown(
                category_id=cid, name=name, total=Decimal(str(tot or 0)),
                budget=budget, count=int(cnt or 0),
            )
            for cid, name, budget, tot, cnt in cat_rows.all()
        ]

        month_expr = func.to_char(Expense.expense_date, "YYYY-MM")
        month_rows = await self.db.execute(
            select(month_expr, func.sum(Expense.amount))
            .where(*base)
            .group_by(month_expr)
            .order_by(month_expr)
        )
        by_month = [MonthPoint(month=m, total=Decimal(str(t or 0))) for m, t in month_rows.all()]

        branch_rows = await self.db.execute(
            select(Expense.branch_id, Branch.name, func.sum(Expense.amount))
            .outerjoin(Branch, Expense.branch_id == Branch.id)
            .where(*base)
            .group_by(Expense.branch_id, Branch.name)
            .order_by(func.sum(Expense.amount).desc())
        )
        by_branch = [
            BranchBreakdown(branch_id=bid, name=bname or "Unassigned", total=Decimal(str(t or 0)))
            for bid, bname, t in branch_rows.all()
        ]

        method_rows = await self.db.execute(
            select(Expense.payment_method, func.sum(Expense.amount))
            .where(*base)
            .group_by(Expense.payment_method)
            .order_by(func.sum(Expense.amount).desc())
        )
        by_payment_method = [
            MethodBreakdown(method=m or "Other", total=Decimal(str(t or 0))) for m, t in method_rows.all()
        ]

        return ExpenseSummary(
            date_from=date_from,
            date_to=date_to,
            total=Decimal(str(total or 0)),
            count=int(count or 0),
            by_category=by_category,
            by_month=by_month,
            by_branch=by_branch,
            by_payment_method=by_payment_method,
        )
