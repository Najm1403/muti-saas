# schemas/platform_employee.py
#
# Platform HR — employees of the SaaS company + their monthly salary payments
# + payroll analytics. Platform-admin scoped (no tenant_id).

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator

from schemas.common import APIBaseSchema, TimestampResponseSchema, UUIDResponseSchema

EMPLOYMENT_TYPES = ("Full-time", "Part-time", "Contract", "Intern")
EMPLOYEE_STATUSES = ("active", "on_leave", "terminated")
PAYMENT_METHODS = ("Bank", "Cash", "Cheque", "Mobile", "Other")


# ── Employees ─────────────────────────────────────────────────

class PlatformDepartmentCreate(APIBaseSchema):
    name: str = Field(..., min_length=1, max_length=80)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class PlatformEmployeeBase(APIBaseSchema):
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
    bank_name: str | None = Field(None, max_length=120)
    bank_account: str | None = Field(None, max_length=60)
    national_id: str | None = Field(None, max_length=40)
    address: str | None = None
    notes: str | None = None


class PlatformEmployeeCreate(PlatformEmployeeBase):
    pass


class PlatformEmployeeUpdate(APIBaseSchema):
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
    bank_name: str | None = Field(None, max_length=120)
    bank_account: str | None = Field(None, max_length=60)
    national_id: str | None = Field(None, max_length=40)
    address: str | None = None
    notes: str | None = None


class PlatformEmployeeResponse(UUIDResponseSchema, TimestampResponseSchema):
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
    bank_name: str | None = None
    bank_account: str | None = None
    national_id: str | None = None
    address: str | None = None
    notes: str | None = None
    paid_this_month: bool = False
    last_paid_period: str | None = None


# ── Salary payments ──────────────────────────────────────────

class PlatformSalaryPaymentCreate(APIBaseSchema):
    platform_employee_id: UUID
    period_month: int = Field(..., ge=1, le=12)
    period_year: int = Field(..., ge=2000, le=2100)
    gross_amount: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    bonus: Decimal = Field(Decimal("0"), ge=Decimal("0"), decimal_places=2)
    deductions: Decimal = Field(Decimal("0"), ge=Decimal("0"), decimal_places=2)
    status: str = Field("paid", max_length=20)
    payment_date: date | None = None
    payment_method: str = Field("Bank", max_length=30)
    reference: str | None = Field(None, max_length=100)
    note: str | None = None


class PlatformSalaryPaymentUpdate(APIBaseSchema):
    gross_amount: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    bonus: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    deductions: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    status: str | None = Field(None, max_length=20)
    payment_date: date | None = None
    payment_method: str | None = Field(None, max_length=30)
    reference: str | None = Field(None, max_length=100)
    note: str | None = None


class PlatformSalaryPaymentResponse(UUIDResponseSchema, TimestampResponseSchema):
    platform_employee_id: UUID
    employee_no: str | None = None
    employee_name: str | None = None
    department: str | None = None
    period_month: int
    period_year: int
    period: str
    gross_amount: Decimal
    bonus: Decimal
    deductions: Decimal
    net_amount: Decimal
    status: str
    payment_date: date | None = None
    payment_method: str
    reference: str | None = None
    note: str | None = None
    paid_by: UUID | None = None
    paid_by_name: str | None = None


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
    status: str
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
    period: str
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
    monthly_commitment: Decimal
    this_month_period: str
    this_month_net_paid: Decimal
    this_month_net_pending: Decimal
    this_month_unpaid_count: int
    this_month_coverage_pct: float
    ytd_net_paid: Decimal
    by_month: list[MonthPoint] = []
    by_department: list[DeptBreakdown] = []
    by_status: list[StatusBreakdown] = []
