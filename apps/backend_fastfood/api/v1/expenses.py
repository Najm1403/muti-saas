# api/v1/expenses.py
#
# Tenant expense tracking — managed categories + expense records + a monitor
# summary. Every route is permission-gated:
#   expenses.view    → read (list / get / summary / categories)
#   expenses.manage  → write (create / update / delete, incl. categories)
# Admin / Owner / Manager roles (and all_branches users) bypass the check.
#
# Prefix: /api/v1/expenses

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, require_permission
from db.session import get_db
from schemas.common import MessageResponse
from schemas.expense import (
    ExpenseCategoryCreate,
    ExpenseCategoryResponse,
    ExpenseCategoryUpdate,
    ExpenseCreate,
    ExpenseResponse,
    ExpenseSummary,
    ExpenseUpdate,
)
from services.expense_service import ExpenseService
from services.pdf_report_service import build_pdf, data_table, get_branding

router = APIRouter(prefix="/expenses", tags=["Expenses"])

_view = require_permission("expenses.view")
_manage = require_permission("expenses.manage")


def _svc(db: AsyncSession = Depends(get_db)) -> ExpenseService:
    return ExpenseService(db)


# ── Categories ───────────────────────────────────────────────

@router.get("/categories", response_model=list[ExpenseCategoryResponse], summary="List expense categories")
async def list_categories(
    current: CurrentUser = Depends(_view),
    svc: ExpenseService = Depends(_svc),
) -> list[ExpenseCategoryResponse]:
    return await svc.list_categories(tenant_id=current.tenant_id)


@router.post(
    "/categories",
    response_model=ExpenseCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create expense category",
)
async def create_category(
    data: ExpenseCategoryCreate,
    current: CurrentUser = Depends(_manage),
    svc: ExpenseService = Depends(_svc),
) -> ExpenseCategoryResponse:
    return await svc.create_category(tenant_id=current.tenant_id, data=data)


@router.patch("/categories/{id}", response_model=ExpenseCategoryResponse, summary="Update expense category")
async def update_category(
    id: UUID,
    data: ExpenseCategoryUpdate,
    current: CurrentUser = Depends(_manage),
    svc: ExpenseService = Depends(_svc),
) -> ExpenseCategoryResponse:
    return await svc.update_category(id=id, tenant_id=current.tenant_id, data=data)


@router.delete("/categories/{id}", response_model=MessageResponse, summary="Delete expense category")
async def delete_category(
    id: UUID,
    current: CurrentUser = Depends(_manage),
    svc: ExpenseService = Depends(_svc),
) -> MessageResponse:
    await svc.delete_category(id=id, tenant_id=current.tenant_id)
    return MessageResponse(message="Expense category deleted.")


# ── Monitor ──────────────────────────────────────────────────

@router.get("/summary", response_model=ExpenseSummary, summary="Expense monitor summary")
async def expense_summary(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    current: CurrentUser = Depends(_view),
    svc: ExpenseService = Depends(_svc),
) -> ExpenseSummary:
    return await svc.summary(tenant_id=current.tenant_id, date_from=date_from, date_to=date_to)


# ── Expenses ─────────────────────────────────────────────────

@router.get("", response_model=list[ExpenseResponse], summary="List expenses")
@router.get("/", response_model=list[ExpenseResponse], include_in_schema=False)
async def list_expenses(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    payment_method: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    current: CurrentUser = Depends(_view),
    svc: ExpenseService = Depends(_svc),
) -> list[ExpenseResponse]:
    return await svc.list(
        tenant_id=current.tenant_id,
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        branch_id=branch_id,
        payment_method=payment_method,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED, summary="Record an expense")
@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_expense(
    data: ExpenseCreate,
    current: CurrentUser = Depends(_manage),
    svc: ExpenseService = Depends(_svc),
) -> ExpenseResponse:
    return await svc.create(
        tenant_id=current.tenant_id, recorded_by=current.user_id, data=data
    )


@router.get("/pdf", summary="Expense register — PDF")
async def get_expense_register_pdf(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    payment_method: str | None = Query(default=None),
    current: CurrentUser = Depends(_view),
    svc: ExpenseService = Depends(_svc),
) -> Response:
    rows = await svc.list(
        tenant_id=current.tenant_id,
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        branch_id=branch_id,
        payment_method=payment_method,
        limit=500,
    )
    business_name, logo_bytes, branch_line, currency = await get_branding(
        svc.db, current.tenant_id, branch_id,
    )

    total_amount = sum(e.amount for e in rows)
    table = data_table(
        ["Date", "Category", "Amount", "Method", "Vendor", "Branch", "Note"],
        [
            [e.expense_date.strftime("%d %b %Y"), e.category_name or "—", f"{currency} {e.amount:.2f}",
             e.payment_method, e.vendor or "—", e.branch_name or "—", e.note or e.reference or ""]
            for e in rows
        ],
        numeric_cols={2},
        col_fractions=[0.10, 0.15, 0.12, 0.11, 0.15, 0.15, 0.22],
        totals=["", "Total", f"{currency} {total_amount:.2f}", "", "", "", f"{len(rows)} entries"] if rows else None,
    )
    subtitle = None
    if date_from or date_to:
        subtitle = f"{date_from.strftime('%d %b %Y') if date_from else 'Start'} – {date_to.strftime('%d %b %Y') if date_to else 'Today'}"
    pdf_bytes = await build_pdf(
        business_name=business_name, logo_bytes=logo_bytes, branch_line=branch_line,
        report_title="Expense Register", subtitle=subtitle, flowables=[table],
    )
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="expense-register.pdf"'},
    )


@router.get("/{id}", response_model=ExpenseResponse, summary="Get an expense")
async def get_expense(
    id: UUID,
    current: CurrentUser = Depends(_view),
    svc: ExpenseService = Depends(_svc),
) -> ExpenseResponse:
    return await svc.get(id=id, tenant_id=current.tenant_id)


@router.patch("/{id}", response_model=ExpenseResponse, summary="Update an expense")
async def update_expense(
    id: UUID,
    data: ExpenseUpdate,
    current: CurrentUser = Depends(_manage),
    svc: ExpenseService = Depends(_svc),
) -> ExpenseResponse:
    return await svc.update(id=id, tenant_id=current.tenant_id, data=data)


@router.delete("/{id}", response_model=MessageResponse, summary="Delete an expense")
async def delete_expense(
    id: UUID,
    current: CurrentUser = Depends(_manage),
    svc: ExpenseService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current.tenant_id)
    return MessageResponse(message="Expense deleted.")
