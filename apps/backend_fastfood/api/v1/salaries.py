# api/v1/salaries.py
#
# Tenant HR — monthly salary payments + payroll register + analytics.
# Permission-gated:
#   salaries.view    → read
#   salaries.manage  → write
# Admin / Owner / Manager roles (and all_branches users) bypass the check.
#
# Prefix: /api/v1/salaries

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, require_permission
from db.session import get_db
from schemas.common import MessageResponse
from schemas.employee import (
    PayrollRegister,
    PayrollSummary,
    SalaryPaymentCreate,
    SalaryPaymentResponse,
    SalaryPaymentUpdate,
)
from services.hr_service import HRService
from services.pdf_report_service import build_pdf, data_table, get_branding

_MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)

router = APIRouter(prefix="/salaries", tags=["Salaries"])

_view = require_permission("salaries.view")
_manage = require_permission("salaries.manage")


def _svc(db: AsyncSession = Depends(get_db)) -> HRService:
    return HRService(db)


def _default_period() -> tuple[int, int]:
    t = date.today()
    return t.month, t.year


@router.get("/summary", response_model=PayrollSummary, summary="Payroll analytics")
async def payroll_summary(
    current: CurrentUser = Depends(_view),
    svc: HRService = Depends(_svc),
) -> PayrollSummary:
    return await svc.summary(tenant_id=current.tenant_id)


@router.get("/register", response_model=PayrollRegister, summary="Payroll register for one month")
async def payroll_register(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    current: CurrentUser = Depends(_view),
    svc: HRService = Depends(_svc),
) -> PayrollRegister:
    dm, dy = _default_period()
    return await svc.payroll_register(
        tenant_id=current.tenant_id, period_month=month or dm, period_year=year or dy
    )


@router.get("/register/pdf", summary="Payroll register — PDF")
async def payroll_register_pdf(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    status_: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None),
    current: CurrentUser = Depends(_view),
    svc: HRService = Depends(_svc),
) -> Response:
    dm, dy = _default_period()
    register = await svc.payroll_register(
        tenant_id=current.tenant_id, period_month=month or dm, period_year=year or dy
    )
    # Mirrors the on-screen visibleRows() filter (salaries.html) — the
    # register endpoint itself returns every employee for the period, with
    # status/search narrowing applied client-side there and here alike.
    rows = register.rows
    if status_:
        rows = [r for r in rows if r.status == status_]
    if q:
        needle = q.lower()
        rows = [r for r in rows if needle in f"{r.employee_no} {r.full_name}".lower()]

    business_name, logo_bytes, branch_line, currency = await get_branding(
        svc.db, current.tenant_id, None,
    )

    def money(v) -> str:
        return f"{currency} {v:.2f}" if v is not None else "—"

    net_total = sum((r.net_amount or 0) for r in rows)
    table = data_table(
        ["Employee No", "Name", "Department", "Base", "Bonus", "Deductions", "Net", "Status", "Paid On"],
        [
            [r.employee_no, r.full_name, r.department or "—",
             money(r.gross_amount if r.gross_amount is not None else r.monthly_salary),
             money(r.bonus), money(r.deductions), money(r.net_amount),
             r.status.title(), r.payment_date.strftime("%d %b %Y") if r.payment_date else "—"]
            for r in rows
        ],
        numeric_cols={3, 4, 5, 6},
        col_fractions=[0.11, 0.17, 0.13, 0.11, 0.10, 0.11, 0.11, 0.09, 0.07],
        totals=["", "", "Total", "", "", "", money(net_total), "", ""] if rows else None,
    )
    period_label = f"{_MONTH_NAMES[(month or dm) - 1]} {year or dy}"
    pdf_bytes = await build_pdf(
        business_name=business_name, logo_bytes=logo_bytes, branch_line=branch_line,
        report_title="Payroll Register", subtitle=period_label, flowables=[table],
    )
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="payroll-register.pdf"'},
    )


@router.get("", response_model=list[SalaryPaymentResponse], summary="List salary payments")
@router.get("/", response_model=list[SalaryPaymentResponse], include_in_schema=False)
async def list_payments(
    employee_id: UUID | None = Query(default=None),
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    status_: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=300, ge=1, le=1000),
    current: CurrentUser = Depends(_view),
    svc: HRService = Depends(_svc),
) -> list[SalaryPaymentResponse]:
    return await svc.list_payments(
        tenant_id=current.tenant_id,
        employee_id=employee_id,
        period_month=month,
        period_year=year,
        status=status_,
        q=q,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=SalaryPaymentResponse, status_code=status.HTTP_201_CREATED, summary="Record a salary payment")
@router.post("/", response_model=SalaryPaymentResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_payment(
    data: SalaryPaymentCreate,
    current: CurrentUser = Depends(_manage),
    svc: HRService = Depends(_svc),
) -> SalaryPaymentResponse:
    return await svc.create_payment(
        tenant_id=current.tenant_id, recorded_by=current.user_id, data=data
    )


@router.get("/{id}", response_model=SalaryPaymentResponse, summary="Get a salary payment")
async def get_payment(
    id: UUID,
    current: CurrentUser = Depends(_view),
    svc: HRService = Depends(_svc),
) -> SalaryPaymentResponse:
    return await svc.get_payment(id=id, tenant_id=current.tenant_id)


@router.patch("/{id}", response_model=SalaryPaymentResponse, summary="Update a salary payment")
async def update_payment(
    id: UUID,
    data: SalaryPaymentUpdate,
    current: CurrentUser = Depends(_manage),
    svc: HRService = Depends(_svc),
) -> SalaryPaymentResponse:
    return await svc.update_payment(id=id, tenant_id=current.tenant_id, data=data)


@router.delete("/{id}", response_model=MessageResponse, summary="Delete a salary payment")
async def delete_payment(
    id: UUID,
    current: CurrentUser = Depends(_manage),
    svc: HRService = Depends(_svc),
) -> MessageResponse:
    await svc.delete_payment(id=id, tenant_id=current.tenant_id)
    return MessageResponse(message="Salary payment deleted.")
