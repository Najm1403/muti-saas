# models/salary_payment.py
#
# One month's payroll row for a tenant employee.
# status = "pending" (not yet paid) or "paid".

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.employee import Employee
    from models.tenant import Tenant
    from models.user import User


class SalaryPayment(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "salary_payments"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    period_month: Mapped[int] = mapped_column(Integer, nullable=False)   # 1-12
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)

    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    bonus: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    # pending / paid
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)

    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False, default="Bank")
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    recorded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")
    employee: Mapped["Employee"] = relationship("Employee", back_populates="salary_payments")
    recorded_by_user: Mapped["User | None"] = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            "employee_id", "period_year", "period_month",
            name="uq_salary_employee_period",
        ),
    )
