# models/employee.py
#
# A tenant's employee / staff HR record. Distinct from `User` (a dashboard /
# POS login) — an employee may optionally be linked to a User via user_id, but
# most employees are payroll-only records with no login.

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.branch import Branch
    from models.salary_payment import SalaryPayment
    from models.tenant import Tenant
    from models.user import User


class Employee(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "employees"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Auto-assigned per tenant — "EMP-0001". Unique within the tenant, never recycled.
    employee_no: Mapped[str] = mapped_column(String(20), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)

    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    # Attendance clock-in PIN — independent of User.pin_hash. Every active
    # employee can have one and use it to punch in/out whether or not they
    # ever become a User; POS operation still requires pos.operate on a User.
    pin_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)

    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str | None] = mapped_column(String(80), nullable=True)

    employment_type: Mapped[str] = mapped_column(String(30), nullable=False, default="Full-time")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)

    join_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    monthly_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    bank_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(String(60), nullable=True)
    national_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant")
    branch: Mapped["Branch | None"] = relationship("Branch")
    user: Mapped["User | None"] = relationship("User")
    salary_payments: Mapped[list["SalaryPayment"]] = relationship(
        "SalaryPayment", back_populates="employee"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "employee_no", name="uq_employee_tenant_no"),
    )
