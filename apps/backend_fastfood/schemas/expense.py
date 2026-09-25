# schemas/expense.py

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from schemas.common import APIBaseSchema, TimestampResponseSchema, UUIDResponseSchema


# ── Categories ────────────────────────────────────────────────

class ExpenseCategoryCreate(APIBaseSchema):
    name: str = Field(..., min_length=1, max_length=80)
    monthly_budget: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)


class ExpenseCategoryUpdate(APIBaseSchema):
    name: str | None = Field(None, min_length=1, max_length=80)
    monthly_budget: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    is_active: bool | None = None


class ExpenseCategoryResponse(UUIDResponseSchema, TimestampResponseSchema):
    tenant_id: UUID
    name: str
    monthly_budget: Decimal | None = None
    is_active: bool
    expense_count: int = 0
    spent_this_month: Decimal = Decimal("0")


# ── Expenses ──────────────────────────────────────────────────

class ExpenseCreate(APIBaseSchema):
    category_id: UUID
    branch_id: UUID | None = None
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    expense_date: date
    payment_method: str = Field(default="Cash", min_length=1, max_length=40)
    vendor: str | None = Field(None, max_length=150)
    reference: str | None = Field(None, max_length=100)
    note: str | None = None


class ExpenseUpdate(APIBaseSchema):
    category_id: UUID | None = None
    branch_id: UUID | None = None
    amount: Decimal | None = Field(None, gt=0, decimal_places=2)
    expense_date: date | None = None
    payment_method: str | None = Field(None, min_length=1, max_length=40)
    vendor: str | None = Field(None, max_length=150)
    reference: str | None = Field(None, max_length=100)
    note: str | None = None


class ExpenseResponse(UUIDResponseSchema, TimestampResponseSchema):
    tenant_id: UUID
    category_id: UUID
    category_name: str | None = None
    branch_id: UUID | None = None
    branch_name: str | None = None
    amount: Decimal
    expense_date: date
    payment_method: str
    vendor: str | None = None
    reference: str | None = None
    note: str | None = None
    recorded_by: UUID | None = None
    recorded_by_name: str | None = None


# ── Monitor / summary ─────────────────────────────────────────

class CategoryBreakdown(APIBaseSchema):
    category_id: UUID
    name: str
    total: Decimal
    budget: Decimal | None = None
    count: int


class MonthPoint(APIBaseSchema):
    month: str        # "YYYY-MM"
    total: Decimal


class BranchBreakdown(APIBaseSchema):
    branch_id: UUID | None = None
    name: str
    total: Decimal


class MethodBreakdown(APIBaseSchema):
    method: str
    total: Decimal


class ExpenseSummary(APIBaseSchema):
    date_from: date
    date_to: date
    total: Decimal
    count: int
    by_category: list[CategoryBreakdown] = []
    by_month: list[MonthPoint] = []
    by_branch: list[BranchBreakdown] = []
    by_payment_method: list[MethodBreakdown] = []
