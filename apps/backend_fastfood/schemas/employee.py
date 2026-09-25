# schemas/employee.py
#
# Tenant HR — employee records + monthly salary payments + payroll analytics.

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from schemas.common import APIBaseSchema, TimestampResponseSchema, UUIDResponseSchema

EMPLOYMENT_TYPES = ("Full-time", "Part-time", "Contract", "Intern")
EMPLOYEE_STATUSES = ("active", "on_leave", "terminated")
PAYMENT_METHODS = ("Bank", "Cash", "Cheque", "Mobile", "Other")


# ── Employees ─────────────────────────────────────────────────

class EmployeeBase(APIBaseSchema):
    full_name: str = Field(..., min_length=1, max_length=150)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=40)
    designation: str | None = Field(None, max_length=100)
    department: str | None = Field(None, max_length=80)
    employment_type: str = Field("Full-time", max_length=30)
    status: str = Field("active", max_length=20)
    join_date: date | None = None
    end_date: date | None = None
    monthly_salary: Decimal = Field(Decimal("0"), ge=Decimal("0"), decimal_places=2)
    branch_id: UUID | None = None
    user_id: UUID | None = None
    bank_name: str | None = Field(None, max_length=120)
    bank_account: str | None = Field(None, max_length=60)
    national_id: str | None = Field(None, max_length=40)
    address: str | None = None
    notes: str | None = None


class EmployeeCreate(EmployeeBase):
    pin: str | None = Field(
        None, min_length=4, max_length=6, pattern=r"^\d+$",
        description="Optional 4-6 digit attendance clock-in PIN — hashed server-side.",
    )


class EmployeeUpdate(APIBaseSchema):
    full_name: str | None = Field(None, min_length=1, max_length=150)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=40)
    designation: str | None = Field(None, max_length=100)
    department: str | None = Field(None, max_length=80)
    employment_type: str | None = Field(None, max_length=30)
    status: str | None = Field(None, max_length=20)
    join_date: date | None = None
    end_date: date | None = None
    monthly_salary: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    branch_id: UUID | None = None
    user_id: UUID | None = None
    bank_name: str | None = Field(None, max_length=120)
    bank_account: str | None = Field(None, max_length=60)
    national_id: str | None = Field(None, max_length=40)
    address: str | None = None
    notes: str | None = None


class EmployeeResponse(UUIDResponseSchema, TimestampResponseSchema):
    tenant_id: UUID
    employee_no: str
    seq: int
    full_name: str
    email: str | None = None
    phone: str | None = None
    designation: str | None = None
    department: str | None = None
    employment_type: str
    status: str
    join_date: date | None = None
    end_date: date | None = None
    monthly_salary: Decimal
    branch_id: UUID | None = None
    branch_name: str | None = None
    user_id: UUID | None = None
    has_pin: bool = False   # attendance clock-in PIN set (independent of any linked User)
    bank_name: str | None = None
    bank_account: str | None = None
    national_id: str | None = None
    address: str | None = None
    notes: str | None = None
    # payroll rollups (filled by the service on the detail/list view)
    paid_this_month: bool = False
    last_paid_period: str | None = None       # "YYYY-MM"


class EmployeeSetPin(APIBaseSchema):
    """Admin sets/replaces an employee's attendance clock-in PIN."""

    pin: str = Field(..., min_length=4, max_length=6, pattern=r"^\d+$")


# ── Salary payments ──────────────────────────────────────────

class SalaryPaymentCreate(APIBaseSchema):
    employee_id: UUID
    period_month: int = Field(..., ge=1, le=12)
    period_year: int = Field(..., ge=2000, le=2100)
    gross_amount: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    bonus: Decimal = Field(Decimal("0"), ge=Decimal("0"), decimal_places=2)
    deductions: Decimal = Field(Decimal("0"), ge=Decimal("0"), decimal_places=2)
    status: str = Field("paid", max_length=20)          # paid | pending
    payment_date: date | None = None
    payment_method: str = Field("Bank", max_length=30)
    reference: str | None = Field(None, max_length=100)
    note: str | None = None


class SalaryPaymentUpdate(APIBaseSchema):
    gross_amount: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    bonus: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    deductions: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    status: str | None = Field(None, max_length=20)
    payment_date: date | None = None
    payment_method: str | None = Field(None, max_length=30)
    reference: str | None = Field(None, max_length=100)
    note: str | None = None


class SalaryPaymentResponse(UUIDResponseSchema, TimestampResponseSchema):
    tenant_id: UUID
    employee_id: UUID
    employee_no: str | None = None
    employee_name: str | None = None
    department: str | None = None
    period_month: int
    period_year: int
    period: str                         # "YYYY-MM"
    gross_amount: Decimal
    bonus: Decimal
    deductions: Decimal
    net_amount: Decimal
    status: str
    payment_date: date | None = None
    payment_method: str
    reference: str | None = None
    note: str | None = None
    recorded_by: UUID | None = None
    recorded_by_name: str | None = None


# ── Payroll register + analytics ────────────────────────────

class PayrollRegisterRow(APIBaseSchema):
    employee_id: UUID
    employee_no: str
    full_name: str
    department: str | None = None
    designation: str | None = None
    monthly_salary: Decimal
    payment_id: UUID | None = None
    gross_amount: Decimal | None = None
    bonus: Decimal | None = None
    deductions: Decimal | None = None
    net_amount: Decimal | None = None
    status: str                         # paid | pending | unpaid
    payment_date: date | None = None
    payment_method: str | None = None


class PayrollRegister(APIBaseSchema):
    period_month: int
    period_year: int
    period: str
    headcount: int
    paid_count: int
    pending_count: int
    unpaid_count: int
    gross_total: Decimal
    net_paid_total: Decimal
    net_pending_total: Decimal
    rows: list[PayrollRegisterRow] = []


class MonthPoint(APIBaseSchema):
    period: str                         # "YYYY-MM"
    net_paid: Decimal
    net_pending: Decimal
    count: int


class DeptBreakdown(APIBaseSchema):
    department: str
    headcount: int
    monthly_salary: Decimal
    net_paid: Decimal


class StatusBreakdown(APIBaseSchema):
    status: str
    count: int


class PayrollSummary(APIBaseSchema):
    headcount_active: int
    headcount_total: int
    monthly_commitment: Decimal         # sum of active employees' monthly_salary
    this_month_period: str
    this_month_net_paid: Decimal
    this_month_net_pending: Decimal
    this_month_unpaid_count: int
    this_month_coverage_pct: float
    ytd_net_paid: Decimal
    by_month: list[MonthPoint] = []
    by_department: list[DeptBreakdown] = []
    by_status: list[StatusBreakdown] = []
