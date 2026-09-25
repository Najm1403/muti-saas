# services/attendance_service.py
#
# Employee attendance (clock-in/out). Every query is explicitly scoped by
# tenant_id — AttendanceRecord.tenant_id is set once at creation from a
# server-verified source (the device token's tenant, or the authenticated
# admin's tenant for a manual entry) and never trusted from client input.
# branch_id supplied directly by a caller (dashboard manual entry) is
# re-verified against Branch -> Business -> tenant_id before use, the same
# defense-in-depth join used elsewhere in this codebase (see
# api/v1/pos/_guards.py::_load_device).

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from core.exceptions import NotFoundError, ValidationError
from core.security import verify_password
from models.attendance_record import AttendanceRecord
from models.branch import Branch
from models.business import Business
from models.employee import Employee
from models.user import User
from repositories.audit_log_repository import AuditLogRepository
from schemas.attendance import (
    AttendanceCorrection,
    AttendanceManualCreate,
    AttendancePunchResponse,
    AttendanceRecordResponse,
    AttendanceStaffMember,
    AttendanceStatusEntry,
)


class AttendanceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── POS punch (device token; no cashier session created or required) ──

    async def list_staff(self, *, tenant_id: UUID, branch_id: UUID) -> list[AttendanceStaffMember]:
        """Active employees who may punch at this device's branch.

        Branch-assigned employees only see their own branch; an employee with
        no branch_id (HQ / roaming staff) shows up everywhere, mirroring how
        an all_branches User appears on every device's cashier picker.
        """
        employees = (
            await self.db.execute(
                select(Employee)
                .where(
                    Employee.tenant_id == tenant_id,
                    Employee.status == "active",
                    Employee.deleted_at.is_(None),
                    (Employee.branch_id == branch_id) | (Employee.branch_id.is_(None)),
                )
                .order_by(Employee.full_name)
            )
        ).scalars().all()
        return [
            AttendanceStaffMember(
                employee_id=e.id, full_name=e.full_name, designation=e.designation,
                has_pin=e.pin_hash is not None,
            )
            for e in employees
        ]

    async def punch(
        self, *, tenant_id: UUID, branch_id: UUID, device_id: UUID, employee_id: UUID, pin: str,
    ) -> AttendancePunchResponse:
        employee = await self.db.scalar(
            select(Employee).where(
                Employee.id == employee_id, Employee.tenant_id == tenant_id,
                Employee.deleted_at.is_(None), Employee.status == "active",
            )
        )
        if not employee:
            raise ValidationError("Employee not found.")
        if not employee.pin_hash:
            raise ValidationError(
                "This employee has no attendance PIN set. Ask an admin to set one from Employees."
            )
        if not verify_password(pin, employee.pin_hash):
            raise ValidationError("Invalid PIN.")

        open_record = await self.db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.tenant_id == tenant_id,
                AttendanceRecord.employee_id == employee.id,
                AttendanceRecord.clock_out_at.is_(None),
                AttendanceRecord.deleted_at.is_(None),
            ).with_for_update()
        )
        now = datetime.now(timezone.utc)
        if open_record:
            open_record.clock_out_at = now
            await self.db.commit()
            return AttendancePunchResponse(
                id=open_record.id, employee_id=employee.id, full_name=employee.full_name,
                action="clocked_out", clock_in_at=open_record.clock_in_at, clock_out_at=now,
            )

        record = AttendanceRecord(
            tenant_id=tenant_id, branch_id=branch_id, employee_id=employee.id,
            user_id=employee.user_id, device_id=device_id, clock_in_at=now,
            method="pin", source="pos_kiosk",
        )
        self.db.add(record)
        try:
            await self.db.commit()
        except IntegrityError:
            # The partial unique index caught a race (double tap / concurrent
            # request) — someone else's request already opened a record.
            await self.db.rollback()
            raise ValidationError("Already clocked in — try again.")
        await self.db.refresh(record)
        return AttendancePunchResponse(
            id=record.id, employee_id=employee.id, full_name=employee.full_name,
            action="clocked_in", clock_in_at=record.clock_in_at, clock_out_at=None,
        )

    async def current_status(self, *, tenant_id: UUID, branch_id: UUID) -> list[AttendanceStatusEntry]:
        rows = await self.db.execute(
            select(AttendanceRecord, Employee.full_name)
            .join(Employee, (AttendanceRecord.employee_id == Employee.id) & (Employee.tenant_id == tenant_id))
            .where(
                AttendanceRecord.tenant_id == tenant_id,
                AttendanceRecord.branch_id == branch_id,
                AttendanceRecord.clock_out_at.is_(None),
                AttendanceRecord.deleted_at.is_(None),
            )
            .order_by(AttendanceRecord.clock_in_at)
        )
        return [
            AttendanceStatusEntry(
                employee_id=rec.employee_id, user_id=rec.user_id,
                full_name=name, clock_in_at=rec.clock_in_at,
            )
            for rec, name in rows.all()
        ]

    # ── Tenant dashboard ────────────────────────────────────────────────

    async def list(
        self, *, tenant_id: UUID, branch_id: UUID | None = None, employee_id: UUID | None = None,
        date_from: datetime | None = None, date_to: datetime | None = None,
        skip: int = 0, limit: int = 200,
    ) -> list[AttendanceRecordResponse]:
        recorded_by = aliased(User)
        q = (
            select(AttendanceRecord, Employee.employee_no, Employee.full_name,
                   Branch.name, recorded_by.full_name)
            .join(Employee, (AttendanceRecord.employee_id == Employee.id) & (Employee.tenant_id == tenant_id))
            .join(Branch, AttendanceRecord.branch_id == Branch.id)
            .outerjoin(recorded_by, AttendanceRecord.recorded_by_user_id == recorded_by.id)
            .where(AttendanceRecord.tenant_id == tenant_id, AttendanceRecord.deleted_at.is_(None))
        )
        if branch_id:
            q = q.where(AttendanceRecord.branch_id == branch_id)
        if employee_id:
            q = q.where(AttendanceRecord.employee_id == employee_id)
        if date_from:
            q = q.where(AttendanceRecord.clock_in_at >= date_from)
        if date_to:
            q = q.where(AttendanceRecord.clock_in_at <= date_to)
        q = q.order_by(AttendanceRecord.clock_in_at.desc()).offset(skip).limit(limit)

        rows = await self.db.execute(q)
        return [
            self._to_response(rec, no, name, branch_name, rb_name)
            for rec, no, name, branch_name, rb_name in rows.all()
        ]

    @staticmethod
    def _to_response(rec, employee_no, employee_name, branch_name, recorded_by_name) -> AttendanceRecordResponse:
        duration = None
        if rec.clock_out_at:
            duration = int((rec.clock_out_at - rec.clock_in_at).total_seconds() // 60)
        return AttendanceRecordResponse(
            id=rec.id, tenant_id=rec.tenant_id, branch_id=rec.branch_id, branch_name=branch_name,
            employee_id=rec.employee_id, employee_no=employee_no, employee_name=employee_name,
            user_id=rec.user_id, device_id=rec.device_id,
            clock_in_at=rec.clock_in_at, clock_out_at=rec.clock_out_at,
            duration_minutes=duration, is_open=rec.clock_out_at is None,
            method=rec.method, source=rec.source,
            recorded_by_user_id=rec.recorded_by_user_id, recorded_by_name=recorded_by_name,
            notes=rec.notes, created_at=rec.created_at, updated_at=rec.updated_at,
        )

    async def _verify_branch(self, branch_id: UUID, tenant_id: UUID) -> None:
        ok = await self.db.scalar(
            select(Branch.id).join(Business, Branch.business_id == Business.id)
            .where(Branch.id == branch_id, Business.tenant_id == tenant_id)
        )
        if not ok:
            raise NotFoundError("Branch not found.")

    async def _verify_employee(self, employee_id: UUID, tenant_id: UUID) -> Employee:
        employee = await self.db.scalar(
            select(Employee).where(
                Employee.id == employee_id, Employee.tenant_id == tenant_id,
                Employee.deleted_at.is_(None),
            )
        )
        if not employee:
            raise NotFoundError("Employee not found.")
        return employee

    async def manual_create(
        self, *, tenant_id: UUID, recorded_by_user_id: UUID, data: AttendanceManualCreate,
    ) -> AttendanceRecordResponse:
        employee = await self._verify_employee(data.employee_id, tenant_id)
        await self._verify_branch(data.branch_id, tenant_id)
        if data.clock_out_at and data.clock_out_at <= data.clock_in_at:
            raise ValidationError("clock_out_at must be after clock_in_at.")

        record = AttendanceRecord(
            tenant_id=tenant_id, branch_id=data.branch_id, employee_id=employee.id,
            clock_in_at=data.clock_in_at, clock_out_at=data.clock_out_at,
            method="manual", source="dashboard",
            recorded_by_user_id=recorded_by_user_id, notes=data.notes,
        )
        self.db.add(record)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise ValidationError(
                "This employee already has an open attendance record. Close it before adding another."
            )

        await AuditLogRepository(self.db).create(
            tenant_id=tenant_id, user_id=recorded_by_user_id, action="CREATE", module="attendance",
            entity_type="AttendanceRecord", entity_id=record.id,
            description=f"Manual attendance entry for {employee.full_name}: {data.notes}",
        )
        await self.db.commit()
        await self.db.refresh(record)

        recorder = await self.db.scalar(select(User.full_name).where(User.id == recorded_by_user_id))
        branch = await self.db.scalar(select(Branch.name).where(Branch.id == record.branch_id))
        return self._to_response(record, employee.employee_no, employee.full_name, branch, recorder)

    async def correct(
        self, *, tenant_id: UUID, recorded_by_user_id: UUID, id: UUID, data: AttendanceCorrection,
    ) -> AttendanceRecordResponse:
        record = await self.db.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.id == id, AttendanceRecord.tenant_id == tenant_id,
                AttendanceRecord.deleted_at.is_(None),
            ).with_for_update()
        )
        if not record:
            raise NotFoundError("Attendance record not found.")

        before = (
            f"in={record.clock_in_at.isoformat()} "
            f"out={record.clock_out_at.isoformat() if record.clock_out_at else None}"
        )
        if data.clock_in_at is not None:
            record.clock_in_at = data.clock_in_at
        if data.clear_clock_out:
            record.clock_out_at = None
        elif data.clock_out_at is not None:
            record.clock_out_at = data.clock_out_at
        if record.clock_out_at and record.clock_out_at <= record.clock_in_at:
            raise ValidationError("clock_out_at must be after clock_in_at.")
        record.recorded_by_user_id = recorded_by_user_id

        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            raise ValidationError("This employee already has another open attendance record.")

        employee = await self.db.scalar(
            select(Employee).where(Employee.id == record.employee_id, Employee.tenant_id == tenant_id)
        )
        after = (
            f"in={record.clock_in_at.isoformat()} "
            f"out={record.clock_out_at.isoformat() if record.clock_out_at else None}"
        )
        await AuditLogRepository(self.db).create(
            tenant_id=tenant_id, user_id=recorded_by_user_id, action="UPDATE", module="attendance",
            entity_type="AttendanceRecord", entity_id=record.id,
            description=(
                f"Corrected attendance for {employee.full_name if employee else record.employee_id}: "
                f"{before} -> {after}. Reason: {data.notes}"
            ),
        )
        await self.db.commit()
        await self.db.refresh(record)

        recorder = await self.db.scalar(select(User.full_name).where(User.id == recorded_by_user_id))
        branch = await self.db.scalar(select(Branch.name).where(Branch.id == record.branch_id))
        return self._to_response(
            record, employee.employee_no if employee else None,
            employee.full_name if employee else None, branch, recorder,
        )
