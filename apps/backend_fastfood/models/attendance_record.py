# models/attendance_record.py
#
# One clock-in/clock-out punch for a tenant employee. Independent of
# CashierSession (cash-drawer shifts) — an employee can be clocked in for
# attendance without ever opening a POS shift, and vice versa is not possible
# (POS access requires pos.operate, see api/v1/pos/auth.py).
#
# tenant_id is stored directly (not resolved only via employee/branch joins)
# so every query can filter on it without an extra join — the same pattern
# used by SalaryPayment.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.branch import Branch
    from models.device import Device
    from models.employee import Employee
    from models.tenant import Tenant
    from models.user import User


class AttendanceRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "attendance_records"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The POS login used to punch, when method="pin". Null for a dashboard
    # manual entry where the employee has no login at all.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # The device the punch came from. Null for a dashboard manual entry.
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
    )

    clock_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Null means still clocked in. A partial unique index (see migration)
    # guarantees at most one open record per employee at the database level.
    clock_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # pin | manual | biometric (future)
    method: Mapped[str] = mapped_column(String(20), nullable=False, default="pin")
    # pos_kiosk | dashboard
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="pos_kiosk")

    # Who created/edited this row when it wasn't the employee's own PIN punch
    # (a dashboard manual entry or a correction to an existing row).
    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant")
    branch: Mapped["Branch"] = relationship("Branch")
    employee: Mapped["Employee"] = relationship("Employee")
    user: Mapped["User | None"] = relationship("User", foreign_keys=[user_id])
    device: Mapped["Device | None"] = relationship("Device")
    recorded_by: Mapped["User | None"] = relationship("User", foreign_keys=[recorded_by_user_id])
