# models/platform_employee.py
#
# An employee of the SaaS platform company itself (NOT a tenant's staff).
# Managed from the Platform dashboard → Human Resources → Employees.

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.platform_salary_payment import PlatformSalaryPayment


class PlatformEmployee(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "platform_employees"

    # Auto-assigned, human-readable id — "PLT-0001". Never recycled.
    employee_no: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)

    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str | None] = mapped_column(String(80), nullable=True)

    # Full-time / Part-time / Contract / Intern
    employment_type: Mapped[str] = mapped_column(String(30), nullable=False, default="Full-time")
    # active / on_leave / terminated
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)

    join_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    monthly_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    bank_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(String(60), nullable=True)
    national_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    salary_payments: Mapped[list["PlatformSalaryPayment"]] = relationship(
        "PlatformSalaryPayment", back_populates="employee"
    )
