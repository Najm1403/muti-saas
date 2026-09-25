# api/v1/attendance.py
#
# Tenant dashboard — attendance register, live status, manual entry and
# corrections. Permission-gated:
#   attendance.view    → read
#   attendance.manage  → write (manual entries, corrections)
# Admin / Owner / Manager roles (and all_branches users) bypass the check,
# same as every other tenant-scoped router.
#
# Prefix: /api/v1/attendance

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, require_permission
from db.session import get_db
from schemas.attendance import (
    AttendanceCorrection,
    AttendanceManualCreate,
    AttendanceRecordResponse,
    AttendanceStatusEntry,
)
from services.attendance_service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["Attendance"])

_view = require_permission("attendance.view")
_manage = require_permission("attendance.manage")


def _svc(db: AsyncSession = Depends(get_db)) -> AttendanceService:
    return AttendanceService(db)


@router.get("", response_model=list[AttendanceRecordResponse], summary="Attendance register")
@router.get("/", response_model=list[AttendanceRecordResponse], include_in_schema=False)
async def list_attendance(
    branch_id: UUID | None = Query(default=None),
    employee_id: UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    current: CurrentUser = Depends(_view),
    svc: AttendanceService = Depends(_svc),
) -> list[AttendanceRecordResponse]:
    return await svc.list(
        tenant_id=current.tenant_id,
        branch_id=branch_id,
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )


@router.get("/status", response_model=list[AttendanceStatusEntry], summary="Who is currently clocked in")
async def attendance_status(
    branch_id: UUID = Query(...),
    current: CurrentUser = Depends(_view),
    svc: AttendanceService = Depends(_svc),
) -> list[AttendanceStatusEntry]:
    return await svc.current_status(tenant_id=current.tenant_id, branch_id=branch_id)


@router.post("", response_model=AttendanceRecordResponse, summary="Add a manual attendance entry")
@router.post("/", response_model=AttendanceRecordResponse, include_in_schema=False)
async def create_manual(
    data: AttendanceManualCreate,
    current: CurrentUser = Depends(_manage),
    svc: AttendanceService = Depends(_svc),
) -> AttendanceRecordResponse:
    return await svc.manual_create(tenant_id=current.tenant_id, recorded_by_user_id=current.user_id, data=data)


@router.patch("/{id}", response_model=AttendanceRecordResponse, summary="Correct an attendance record")
async def correct_attendance(
    id: UUID,
    data: AttendanceCorrection,
    current: CurrentUser = Depends(_manage),
    svc: AttendanceService = Depends(_svc),
) -> AttendanceRecordResponse:
    return await svc.correct(tenant_id=current.tenant_id, recorded_by_user_id=current.user_id, id=id, data=data)
