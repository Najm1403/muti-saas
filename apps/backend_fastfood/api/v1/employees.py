# api/v1/employees.py
#
# Tenant HR — employee records. Permission-gated:
#   employees.view    → read
#   employees.manage  → write
# Admin / Owner / Manager roles (and all_branches users) bypass the check.
#
# Prefix: /api/v1/employees

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, require_permission
from db.session import get_db
from schemas.common import MessageResponse
from schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeSetPin,
    EmployeeUpdate,
)
from services.hr_service import HRService
from services.pdf_report_service import build_pdf, data_table, get_branding

router = APIRouter(prefix="/employees", tags=["Employees"])

_view = require_permission("employees.view")
_manage = require_permission("employees.manage")


def _svc(db: AsyncSession = Depends(get_db)) -> HRService:
    return HRService(db)


@router.get("/departments", response_model=list[str], summary="Distinct department names")
async def list_departments(
    current: CurrentUser = Depends(_view),
    svc: HRService = Depends(_svc),
) -> list[str]:
    return await svc.departments(tenant_id=current.tenant_id)


@router.get("", response_model=list[EmployeeResponse], summary="List employees")
@router.get("/", response_model=list[EmployeeResponse], include_in_schema=False)
async def list_employees(
    status_: str | None = Query(default=None, alias="status"),
    department: str | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    q: str | None = Query(default=None),
    unlinked: bool | None = Query(default=None, description="Only employees with no linked User account."),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    current: CurrentUser = Depends(_view),
    svc: HRService = Depends(_svc),
) -> list[EmployeeResponse]:
    return await svc.list_employees(
        tenant_id=current.tenant_id,
        status=status_,
        department=department,
        branch_id=branch_id,
        q=q,
        unlinked=unlinked,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED, summary="Add an employee")
@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_employee(
    data: EmployeeCreate,
    current: CurrentUser = Depends(_manage),
    svc: HRService = Depends(_svc),
) -> EmployeeResponse:
    return await svc.create_employee(tenant_id=current.tenant_id, data=data)


@router.get("/pdf", summary="Employee register — PDF")
async def get_employee_register_pdf(
    status_: str | None = Query(default=None, alias="status"),
    department: str | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    q: str | None = Query(default=None),
    current: CurrentUser = Depends(_view),
    svc: HRService = Depends(_svc),
) -> Response:
    rows = await svc.list_employees(
        tenant_id=current.tenant_id,
        status=status_,
        department=department,
        branch_id=branch_id,
        q=q,
        limit=500,
    )
    business_name, logo_bytes, branch_line, currency = await get_branding(
        svc.db, current.tenant_id, branch_id,
    )

    total_salary = sum(e.monthly_salary for e in rows)
    table = data_table(
        ["Employee No", "Name", "Designation", "Department", "Branch", "Monthly Salary", "Status", "This Month"],
        [
            [e.employee_no, e.full_name, e.designation or "—", e.department or "—",
             e.branch_name or "—", f"{currency} {e.monthly_salary:.2f}",
             e.status.replace("_", " ").title(), "Paid" if e.paid_this_month else "Unpaid"]
            for e in rows
        ],
        numeric_cols={5},
        col_fractions=[0.11, 0.17, 0.13, 0.12, 0.12, 0.13, 0.11, 0.11],
        totals=["", "", "", "", "Total", f"{currency} {total_salary:.2f}", "", f"{len(rows)} employees"] if rows else None,
    )
    pdf_bytes = await build_pdf(
        business_name=business_name, logo_bytes=logo_bytes, branch_line=branch_line,
        report_title="Employee Register", flowables=[table],
    )
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="employee-register.pdf"'},
    )


@router.get("/{id}", response_model=EmployeeResponse, summary="Get an employee")
async def get_employee(
    id: UUID,
    current: CurrentUser = Depends(_view),
    svc: HRService = Depends(_svc),
) -> EmployeeResponse:
    return await svc.get_employee(id=id, tenant_id=current.tenant_id)


@router.patch("/{id}", response_model=EmployeeResponse, summary="Update an employee")
async def update_employee(
    id: UUID,
    data: EmployeeUpdate,
    current: CurrentUser = Depends(_manage),
    svc: HRService = Depends(_svc),
) -> EmployeeResponse:
    return await svc.update_employee(id=id, tenant_id=current.tenant_id, data=data)


@router.post(
    "/{id}/set-pin",
    response_model=EmployeeResponse,
    status_code=status.HTTP_200_OK,
    summary="Set attendance PIN",
    description=(
        "Set or replace an employee's 4-6 digit attendance clock-in PIN. "
        "Admin action — no current PIN required. Independent of any linked "
        "User's POS PIN."
    ),
)
async def set_employee_pin(
    id: UUID,
    data: EmployeeSetPin,
    current: CurrentUser = Depends(_manage),
    svc: HRService = Depends(_svc),
) -> EmployeeResponse:
    return await svc.set_pin(id=id, tenant_id=current.tenant_id, pin=data.pin)


@router.delete("/{id}", response_model=MessageResponse, summary="Archive an employee")
async def delete_employee(
    id: UUID,
    current: CurrentUser = Depends(_manage),
    svc: HRService = Depends(_svc),
) -> MessageResponse:
    await svc.delete_employee(id=id, tenant_id=current.tenant_id)
    return MessageResponse(message="Employee archived.")
