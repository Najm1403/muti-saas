# schemas/attendance.py
#
# Employee attendance (clock-in/out). Independent of CashierSession — see
# models/attendance_record.py for the full rationale.

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from schemas.common import APIBaseSchema, TimestampResponseSchema, UUIDResponseSchema

ATTENDANCE_METHODS = ("pin", "manual", "biometric")
ATTENDANCE_SOURCES = ("pos_kiosk", "dashboard")


# ── POS punch (device token, no cashier session) ────────────────

class AttendanceStaffMember(APIBaseSchema):
    """Active employee for this device's branch — powers the attendance
    clock-in grid. Independent of the cashier staff picker (which lists
    Users, not Employees) — every employee may appear here whether or not
    they ever become a User."""

    employee_id: UUID
    full_name: str
    designation: str | None = None
    has_pin: bool


class AttendancePunchRequest(APIBaseSchema):
    employee_id: UUID
    pin: str = Field(..., min_length=4, max_length=6, pattern=r"^\d+$")


class AttendancePunchResponse(APIBaseSchema):
    id: UUID
    employee_id: UUID
    full_name: str
    action: str          # "clocked_in" | "clocked_out"
    clock_in_at: datetime
    clock_out_at: datetime | None = None


# ── Live "who's in" status (POS grid + dashboard) ───────────────

class AttendanceStatusEntry(APIBaseSchema):
    employee_id: UUID
    user_id: UUID | None = None
    full_name: str
    clock_in_at: datetime


# ── Tenant dashboard: register + manual entry/correction ────────

class AttendanceRecordResponse(UUIDResponseSchema, TimestampResponseSchema):
    tenant_id: UUID
    branch_id: UUID
    branch_name: str | None = None
    employee_id: UUID
    employee_no: str | None = None
    employee_name: str | None = None
    user_id: UUID | None = None
    device_id: UUID | None = None
    clock_in_at: datetime
    clock_out_at: datetime | None = None
    duration_minutes: int | None = None
    is_open: bool
    method: str
    source: str
    recorded_by_user_id: UUID | None = None
    recorded_by_name: str | None = None
    notes: str | None = None


class AttendanceManualCreate(APIBaseSchema):
    employee_id: UUID
    branch_id: UUID
    clock_in_at: datetime
    clock_out_at: datetime | None = None
    notes: str = Field(..., min_length=1, max_length=500)


class AttendanceCorrection(APIBaseSchema):
    clock_in_at: datetime | None = None
    clock_out_at: datetime | None = None
    # Explicit tri-state clear: pass true to null out an accidental clock_out.
    clear_clock_out: bool = False
    notes: str = Field(..., min_length=1, max_length=500)
