# api/platform/salaries.py
#
# Platform-company HR — monthly salary payments + payroll register + analytics.
# Platform admin only. Delete requires super admin.
# Prefix: /api/platform/salaries

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import (
    CurrentPlatformAdmin,
    get_current_platform_admin,
    require_super,
)
from db.session import get_db
from schemas.common import MessageResponse
from schemas.platform_employee import (
    PayrollRegister,
    PayrollSummary,
    PlatformSalaryPaymentCreate,
    PlatformSalaryPaymentResponse,
    PlatformSalaryPaymentUpdate,
)
from services.platform_hr_service import PlatformHRService

router = APIRouter(prefix="/salaries", tags=["Platform · Salaries"])


def _svc(db: AsyncSession = Depends(get_db)) -> PlatformHRService:
    return PlatformHRService(db)


def _default_period() -> tuple[int, int]:
    t = date.today()
    return t.month, t.year


@router.get("/summary", response_model=PayrollSummary, summary="Payroll analytics")
async def payroll_summary(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformHRService = Depends(_svc),
) -> PayrollSummary:
    return await svc.summary()


@router.get("/register", response_model=PayrollRegister, summary="Payroll register for one month")
async def payroll_register(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformHRService = Depends(_svc),
) -> PayrollRegister:
    dm, dy = _default_period()
    return await svc.payroll_register(period_month=month or dm, period_year=year or dy)


@router.get("", response_model=list[PlatformSalaryPaymentResponse], summary="List salary payments")
@router.get("/", response_model=list[PlatformSalaryPaymentResponse], include_in_schema=False)
async def list_payments(
    employee_id: UUID | None = Query(default=None),
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    status_: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=300, ge=1, le=1000),
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformHRService = Depends(_svc),
) -> list[PlatformSalaryPaymentResponse]:
    return await svc.list_payments(
        employee_id=employee_id,
        period_month=month,
        period_year=year,
        status=status_,
        q=q,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=PlatformSalaryPaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a salary payment",
)
@router.post("/", response_model=PlatformSalaryPaymentResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_payment(
    data: PlatformSalaryPaymentCreate,
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformHRService = Depends(_svc),
) -> PlatformSalaryPaymentResponse:
    return await svc.create_payment(paid_by=current.admin_id, data=data)


@router.get("/{id}", response_model=PlatformSalaryPaymentResponse, summary="Get a salary payment")
async def get_payment(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformHRService = Depends(_svc),
) -> PlatformSalaryPaymentResponse:
    return await svc.get_payment(id)


@router.patch("/{id}", response_model=PlatformSalaryPaymentResponse, summary="Update a salary payment")
async def update_payment(
    id: UUID,
    data: PlatformSalaryPaymentUpdate,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformHRService = Depends(_svc),
) -> PlatformSalaryPaymentResponse:
    return await svc.update_payment(id, data)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    summary="Delete a salary payment (super admin only)",
)
async def delete_payment(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(require_super),
    svc: PlatformHRService = Depends(_svc),
) -> MessageResponse:
    await svc.delete_payment(id)
    return MessageResponse(message="Salary payment deleted.")
