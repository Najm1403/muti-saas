# api/v1/pos/attendance.py
#
# POS attendance clock-in/out — device token only. Deliberately does NOT
# depend on operational_cashier: punching in/out must never require (or
# create) a cashier session, so an employee with a PIN but no POS-operating
# permission can still clock in without ever gaining POS access.
#
# Prefix: /api/v1/pos/attendance

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentDevice, tenant_enabled_modules
from api.v1.pos._guards import operational_device
from core.exceptions import ForbiddenError
from db.session import get_db
from schemas.attendance import (
    AttendancePunchRequest,
    AttendancePunchResponse,
    AttendanceStaffMember,
    AttendanceStatusEntry,
)
from services.attendance_service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["POS — Attendance"])


async def _require_module(db: AsyncSession, tenant_id) -> None:
    if "attendance" not in await tenant_enabled_modules(db, tenant_id):
        raise ForbiddenError("Attendance module is disabled.", code="MODULE_DISABLED")


@router.get(
    "/staff",
    response_model=list[AttendanceStaffMember],
    summary="List staff for this device's branch's attendance grid",
    description=(
        "Every active employee for this branch — not just Users. Powers the "
        "clock-in grid independent of the cashier staff picker."
    ),
)
async def staff(
    device: CurrentDevice = Depends(operational_device),
    db: AsyncSession = Depends(get_db),
) -> list[AttendanceStaffMember]:
    await _require_module(db, device.tenant_id)
    svc = AttendanceService(db)
    return await svc.list_staff(tenant_id=device.tenant_id, branch_id=device.branch_id)


@router.post(
    "/punch",
    response_model=AttendancePunchResponse,
    summary="Clock in or out",
    description=(
        "Toggles attendance for the employee identified by employee_id + PIN: "
        "clocks in if no open record exists for today, clocks out if one does. "
        "Authenticates against the employee's own attendance PIN — independent "
        "of any User account — and never issues a cashier token."
    ),
)
async def punch(
    data: AttendancePunchRequest,
    device: CurrentDevice = Depends(operational_device),
    db: AsyncSession = Depends(get_db),
) -> AttendancePunchResponse:
    await _require_module(db, device.tenant_id)
    svc = AttendanceService(db)
    return await svc.punch(
        tenant_id=device.tenant_id,
        branch_id=device.branch_id,
        device_id=device.device_id,
        employee_id=data.employee_id,
        pin=data.pin,
    )


@router.get(
    "/status",
    response_model=list[AttendanceStatusEntry],
    summary="Who is currently clocked in at this branch",
)
async def status(
    device: CurrentDevice = Depends(operational_device),
    db: AsyncSession = Depends(get_db),
) -> list[AttendanceStatusEntry]:
    await _require_module(db, device.tenant_id)
    svc = AttendanceService(db)
    return await svc.current_status(tenant_id=device.tenant_id, branch_id=device.branch_id)
