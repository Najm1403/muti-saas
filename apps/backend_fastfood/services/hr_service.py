# services/hr_service.py
#
# Tenant-scoped HR: employee records + monthly salary payments + payroll
# analytics. Soft-deletes throughout. Employee numbers are auto-assigned per
# tenant ("EMP-0001") and never recycled.

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError, ValidationError
from core.security import hash_password
from models.branch import Branch
from models.employee import Employee
from models.business import Business
from models.salary_payment import SalaryPayment
from models.user import User
from schemas.employee import (
    DeptBreakdown,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    MonthPoint,
    PayrollRegister,
    PayrollRegisterRow,
    PayrollSummary,
    SalaryPaymentCreate,
    SalaryPaymentResponse,
    SalaryPaymentUpdate,
    StatusBreakdown,
)

_ZERO = Decimal("0")


def _period(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def _last_n_periods(n: int, ref: date | None = None) -> list[tuple[int, int]]:
    ref = ref or date.today()
    out: list[tuple[int, int]] = []
    y, m = ref.year, ref.month
    for _ in range(n):
        out.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(out))


def _dec(v) -> Decimal:
    return Decimal(str(v or 0))


class HRService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Employee numbering ──────────────────────────────────────

    async def _next_employee_no(self, tenant_id: UUID) -> tuple[int, str]:
        max_seq = await self.db.scalar(
            select(func.coalesce(func.max(Employee.seq), 0)).where(
                Employee.tenant_id == tenant_id
            )
        )
        seq = int(max_seq or 0) + 1
        return seq, f"EMP-{seq:04d}"

    # ── Employee helpers ────────────────────────────────────────

    async def _emp_or_404(self, id: UUID, tenant_id: UUID) -> Employee:
        row = await self.db.execute(
            select(Employee).where(
                Employee.id == id,
                Employee.tenant_id == tenant_id,
                Employee.deleted_at.is_(None),
            )
        )
        emp = row.scalar_one_or_none()
        if not emp:
            raise NotFoundError("Employee not found.")
        return emp

    async def _verify_branch(self, branch_id: UUID, tenant_id: UUID) -> None:
        ok = await self.db.scalar(
            select(Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Branch.id == branch_id,
                Business.tenant_id == tenant_id,
                Branch.deleted_at.is_(None),
                Business.deleted_at.is_(None),
            )
        )
        if not ok:
            raise NotFoundError("Branch not found.")

    async def _verify_user(
        self, user_id: UUID, tenant_id: UUID, *, exclude_employee_id: UUID | None = None,
    ) -> None:
        ok = await self.db.scalar(
            select(User.id).where(
                User.id == user_id,
                User.tenant_id == tenant_id,
                User.deleted_at.is_(None),
            )
        )
        if not ok:
            raise NotFoundError("Linked user not found.")
        linked_q = select(Employee.id).where(
            Employee.user_id == user_id,
            Employee.tenant_id == tenant_id,
            Employee.deleted_at.is_(None),
        )
        if exclude_employee_id is not None:
            linked_q = linked_q.where(Employee.id != exclude_employee_id)
        if await self.db.scalar(linked_q):
            raise ConflictError("This user account is already linked to another employee.")

    async def _payroll_rollup(self, employee_ids: list[UUID]) -> dict[UUID, dict]:
        """paid_this_month + last_paid_period for a set of employees."""
        if not employee_ids:
            return {}
        today = date.today()
        rows = (
            await self.db.execute(
                select(
                    SalaryPayment.employee_id,
                    SalaryPayment.period_year,
                    SalaryPayment.period_month,
                ).where(
                    SalaryPayment.employee_id.in_(employee_ids),
                    SalaryPayment.deleted_at.is_(None),
                    SalaryPayment.status == "paid",
                )
            )
        ).all()
        out: dict[UUID, dict] = {}
        for eid, yr, mo in rows:
            slot = out.setdefault(eid, {"last_paid_period": None, "paid_this_month": False})
            per = _period(yr, mo)
            if slot["last_paid_period"] is None or per > slot["last_paid_period"]:
                slot["last_paid_period"] = per
            if yr == today.year and mo == today.month:
                slot["paid_this_month"] = True
        return out

    def _emp_response(self, emp: Employee, branch_name: str | None, rollup: dict) -> EmployeeResponse:
        return EmployeeResponse(
            id=emp.id,
            tenant_id=emp.tenant_id,
            employee_no=emp.employee_no,
            seq=emp.seq,
            full_name=emp.full_name,
            email=emp.email,
            phone=emp.phone,
            designation=emp.designation,
            department=emp.department,
            employment_type=emp.employment_type,
            status=emp.status,
            join_date=emp.join_date,
            end_date=emp.end_date,
            monthly_salary=emp.monthly_salary,
            branch_id=emp.branch_id,
            branch_name=branch_name,
            user_id=emp.user_id,
            has_pin=emp.pin_hash is not None,
            bank_name=emp.bank_name,
            bank_account=emp.bank_account,
            national_id=emp.national_id,
            address=emp.address,
            notes=emp.notes,
            created_at=emp.created_at,
            updated_at=emp.updated_at,
            paid_this_month=bool(rollup.get("paid_this_month", False)),
            last_paid_period=rollup.get("last_paid_period"),
        )

    # ── Employee CRUD ──────────────────────────────────────────

    async def list_employees(
        self,
        tenant_id: UUID,
        *,
        status: str | None = None,
        department: str | None = None,
        branch_id: UUID | None = None,
        q: str | None = None,
        unlinked: bool | None = None,
        skip: int = 0,
        limit: int = 200,
    ) -> list[EmployeeResponse]:
        stmt = (
            select(Employee, Branch.name.label("branch_name"))
            .outerjoin(Branch, Employee.branch_id == Branch.id)
            .where(Employee.tenant_id == tenant_id, Employee.deleted_at.is_(None))
        )
        if status:
            stmt = stmt.where(Employee.status == status)
        if department:
            stmt = stmt.where(Employee.department == department)
        if branch_id:
            stmt = stmt.where(Employee.branch_id == branch_id)
        if unlinked:
            # Not yet promoted to a User — the candidate pool for Add User.
            stmt = stmt.where(Employee.user_id.is_(None))
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    Employee.full_name.ilike(like),
                    Employee.employee_no.ilike(like),
                    Employee.designation.ilike(like),
                    Employee.email.ilike(like),
                )
            )
        stmt = stmt.order_by(Employee.seq).offset(skip).limit(limit)
        rows = (await self.db.execute(stmt)).all()
        rollups = await self._payroll_rollup([r[0].id for r in rows])
        return [self._emp_response(r[0], r.branch_name, rollups.get(r[0].id, {})) for r in rows]

    async def get_employee(self, id: UUID, tenant_id: UUID) -> EmployeeResponse:
        emp = await self._emp_or_404(id, tenant_id)
        branch_name = None
        if emp.branch_id:
            branch_name = await self.db.scalar(select(Branch.name).where(Branch.id == emp.branch_id))
        rollups = await self._payroll_rollup([emp.id])
        return self._emp_response(emp, branch_name, rollups.get(emp.id, {}))

    async def create_employee(self, tenant_id: UUID, data: EmployeeCreate) -> EmployeeResponse:
        if data.branch_id is not None:
            await self._verify_branch(data.branch_id, tenant_id)
        if data.user_id is not None:
            await self._verify_user(data.user_id, tenant_id)
        seq, emp_no = await self._next_employee_no(tenant_id)
        emp = Employee(
            tenant_id=tenant_id,
            seq=seq,
            employee_no=emp_no,
            pin_hash=hash_password(data.pin) if data.pin else None,
            **data.model_dump(exclude={"pin"}),
        )
        self.db.add(emp)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ConflictError("This user account is already linked to another employee.")
        return await self.get_employee(emp.id, tenant_id)

    async def update_employee(
        self, id: UUID, tenant_id: UUID, data: EmployeeUpdate
    ) -> EmployeeResponse:
        emp = await self._emp_or_404(id, tenant_id)
        fields = data.model_dump(exclude_unset=True)
        if fields.get("branch_id") is not None:
            await self._verify_branch(fields["branch_id"], tenant_id)
        if fields.get("user_id") is not None:
            await self._verify_user(fields["user_id"], tenant_id, exclude_employee_id=id)
        for k, v in fields.items():
            setattr(emp, k, v)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ConflictError("This user account is already linked to another employee.")
        return await self.get_employee(id, tenant_id)

    async def set_pin(self, id: UUID, tenant_id: UUID, pin: str) -> EmployeeResponse:
        """Set or replace an employee's attendance clock-in PIN (admin action)."""
        emp = await self._emp_or_404(id, tenant_id)
        emp.pin_hash = hash_password(pin)
        await self.db.commit()
        return await self.get_employee(id, tenant_id)

    async def delete_employee(self, id: UUID, tenant_id: UUID) -> None:
        emp = await self._emp_or_404(id, tenant_id)
        paid = await self.db.scalar(
            select(func.count(SalaryPayment.id)).where(
                SalaryPayment.employee_id == emp.id,
                SalaryPayment.deleted_at.is_(None),
                SalaryPayment.status == "paid",
            )
        )
        if paid:
            # keep the audit trail: archive instead of blocking, but flip status
            emp.status = "terminated"
        emp.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def departments(self, tenant_id: UUID) -> list[str]:
        rows = await self.db.execute(
            select(Employee.department)
            .where(
                Employee.tenant_id == tenant_id,
                Employee.deleted_at.is_(None),
                Employee.department.is_not(None),
                Employee.department != "",
            )
            .distinct()
            .order_by(Employee.department)
        )
        return [r[0] for r in rows.all()]

    # ── Salary payment helpers ─────────────────────────────────

    async def _pay_or_404(self, id: UUID, tenant_id: UUID) -> SalaryPayment:
        row = await self.db.execute(
            select(SalaryPayment).where(
                SalaryPayment.id == id,
                SalaryPayment.tenant_id == tenant_id,
                SalaryPayment.deleted_at.is_(None),
            )
        )
        pay = row.scalar_one_or_none()
        if not pay:
            raise NotFoundError("Salary payment not found.")
        return pay

    @staticmethod
    def _net(gross, bonus, deductions) -> Decimal:
        return (_dec(gross) + _dec(bonus) - _dec(deductions)).quantize(Decimal("0.01"))

    def _pay_response(self, row) -> SalaryPaymentResponse:
        p: SalaryPayment = row[0]
        return SalaryPaymentResponse(
            id=p.id,
            tenant_id=p.tenant_id,
            employee_id=p.employee_id,
            employee_no=row.employee_no,
            employee_name=row.employee_name,
            department=row.department,
            period_month=p.period_month,
            period_year=p.period_year,
            period=_period(p.period_year, p.period_month),
            gross_amount=p.gross_amount,
            bonus=p.bonus,
            deductions=p.deductions,
            net_amount=p.net_amount,
            status=p.status,
            payment_date=p.payment_date,
            payment_method=p.payment_method,
            reference=p.reference,
            note=p.note,
            recorded_by=p.recorded_by,
            recorded_by_name=row.recorded_by_name,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )

    def _pay_base_select(self, tenant_id: UUID):
        return (
            select(
                SalaryPayment,
                Employee.employee_no.label("employee_no"),
                Employee.full_name.label("employee_name"),
                Employee.department.label("department"),
                User.full_name.label("recorded_by_name"),
            )
            .join(Employee, SalaryPayment.employee_id == Employee.id)
            .outerjoin(User, SalaryPayment.recorded_by == User.id)
            .where(SalaryPayment.tenant_id == tenant_id, SalaryPayment.deleted_at.is_(None))
        )

    # ── Salary payment CRUD ───────────────────────────────────

    async def list_payments(
        self,
        tenant_id: UUID,
        *,
        employee_id: UUID | None = None,
        period_month: int | None = None,
        period_year: int | None = None,
        status: str | None = None,
        q: str | None = None,
        skip: int = 0,
        limit: int = 300,
    ) -> list[SalaryPaymentResponse]:
        stmt = self._pay_base_select(tenant_id)
        if employee_id:
            stmt = stmt.where(SalaryPayment.employee_id == employee_id)
        if period_month:
            stmt = stmt.where(SalaryPayment.period_month == period_month)
        if period_year:
            stmt = stmt.where(SalaryPayment.period_year == period_year)
        if status:
            stmt = stmt.where(SalaryPayment.status == status)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(Employee.full_name.ilike(like), Employee.employee_no.ilike(like))
            )
        stmt = stmt.order_by(
            SalaryPayment.period_year.desc(),
            SalaryPayment.period_month.desc(),
            Employee.seq,
        ).offset(skip).limit(limit)
        rows = (await self.db.execute(stmt)).all()
        return [self._pay_response(r) for r in rows]

    async def get_payment(self, id: UUID, tenant_id: UUID) -> SalaryPaymentResponse:
        rows = await self.db.execute(
            self._pay_base_select(tenant_id).where(SalaryPayment.id == id)
        )
        row = rows.first()
        if not row:
            raise NotFoundError("Salary payment not found.")
        return self._pay_response(row)

    async def create_payment(
        self, tenant_id: UUID, recorded_by: UUID | None, data: SalaryPaymentCreate
    ) -> SalaryPaymentResponse:
        emp = await self._emp_or_404(data.employee_id, tenant_id)

        dup = await self.db.scalar(
            select(SalaryPayment.id).where(
                SalaryPayment.employee_id == emp.id,
                SalaryPayment.period_year == data.period_year,
                SalaryPayment.period_month == data.period_month,
                SalaryPayment.deleted_at.is_(None),
            )
        )
        if dup:
            raise ConflictError(
                f"A salary row for {emp.employee_no} / {_period(data.period_year, data.period_month)} already exists."
            )

        gross = data.gross_amount if data.gross_amount is not None else emp.monthly_salary
        status = (data.status or "paid").lower()
        if status not in ("paid", "pending"):
            raise ValidationError("status must be 'paid' or 'pending'.")
        pay_date = data.payment_date
        if status == "paid" and pay_date is None:
            pay_date = date.today()

        pay = SalaryPayment(
            tenant_id=tenant_id,
            employee_id=emp.id,
            period_month=data.period_month,
            period_year=data.period_year,
            gross_amount=_dec(gross),
            bonus=_dec(data.bonus),
            deductions=_dec(data.deductions),
            net_amount=self._net(gross, data.bonus, data.deductions),
            status=status,
            payment_date=pay_date,
            payment_method=data.payment_method or "Bank",
            reference=data.reference,
            note=data.note,
            recorded_by=recorded_by,
        )
        self.db.add(pay)
        await self.db.commit()
        return await self.get_payment(pay.id, tenant_id)

    async def update_payment(
        self, id: UUID, tenant_id: UUID, data: SalaryPaymentUpdate
    ) -> SalaryPaymentResponse:
        pay = await self._pay_or_404(id, tenant_id)
        fields = data.model_dump(exclude_unset=True)
        for k, v in fields.items():
            setattr(pay, k, v)
        if {"gross_amount", "bonus", "deductions"} & fields.keys():
            pay.net_amount = self._net(pay.gross_amount, pay.bonus, pay.deductions)
        if "status" in fields:
            pay.status = (pay.status or "pending").lower()
            if pay.status == "paid" and pay.payment_date is None:
                pay.payment_date = date.today()
        await self.db.commit()
        return await self.get_payment(id, tenant_id)

    async def delete_payment(self, id: UUID, tenant_id: UUID) -> None:
        pay = await self._pay_or_404(id, tenant_id)
        pay.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    # ── Payroll register (one month) ──────────────────────────

    async def payroll_register(
        self, tenant_id: UUID, period_month: int, period_year: int
    ) -> PayrollRegister:
        emps = (
            await self.db.execute(
                select(Employee)
                .where(
                    Employee.tenant_id == tenant_id,
                    Employee.deleted_at.is_(None),
                    Employee.status != "terminated",
                )
                .order_by(Employee.seq)
            )
        ).scalars().all()

        pays = {
            p.employee_id: p
            for p in (
                await self.db.execute(
                    select(SalaryPayment).where(
                        SalaryPayment.tenant_id == tenant_id,
                        SalaryPayment.deleted_at.is_(None),
                        SalaryPayment.period_month == period_month,
                        SalaryPayment.period_year == period_year,
                    )
                )
            ).scalars().all()
        }

        rows: list[PayrollRegisterRow] = []
        paid_count = pending_count = unpaid_count = 0
        gross_total = net_paid_total = net_pending_total = _ZERO

        for e in emps:
            p = pays.get(e.id)
            if p is None:
                unpaid_count += 1
                rows.append(PayrollRegisterRow(
                    employee_id=e.id, employee_no=e.employee_no, full_name=e.full_name,
                    department=e.department, designation=e.designation,
                    monthly_salary=e.monthly_salary, status="unpaid",
                ))
                continue
            gross_total += _dec(p.gross_amount)
            if p.status == "paid":
                paid_count += 1
                net_paid_total += _dec(p.net_amount)
            else:
                pending_count += 1
                net_pending_total += _dec(p.net_amount)
            rows.append(PayrollRegisterRow(
                employee_id=e.id, employee_no=e.employee_no, full_name=e.full_name,
                department=e.department, designation=e.designation,
                monthly_salary=e.monthly_salary,
                payment_id=p.id, gross_amount=p.gross_amount, bonus=p.bonus,
                deductions=p.deductions, net_amount=p.net_amount, status=p.status,
                payment_date=p.payment_date, payment_method=p.payment_method,
            ))

        return PayrollRegister(
            period_month=period_month, period_year=period_year,
            period=_period(period_year, period_month),
            headcount=len(emps), paid_count=paid_count,
            pending_count=pending_count, unpaid_count=unpaid_count,
            gross_total=gross_total, net_paid_total=net_paid_total,
            net_pending_total=net_pending_total, rows=rows,
        )

    # ── Analytics ─────────────────────────────────────────────

    async def summary(self, tenant_id: UUID) -> PayrollSummary:
        today = date.today()

        emps = (
            await self.db.execute(
                select(Employee).where(
                    Employee.tenant_id == tenant_id, Employee.deleted_at.is_(None)
                )
            )
        ).scalars().all()
        active = [e for e in emps if e.status == "active"]
        monthly_commitment = sum((_dec(e.monthly_salary) for e in active), _ZERO)

        by_status_map: dict[str, int] = {}
        for e in emps:
            by_status_map[e.status] = by_status_map.get(e.status, 0) + 1
        by_status = [StatusBreakdown(status=k, count=v) for k, v in sorted(by_status_map.items())]

        periods = _last_n_periods(6, today)
        pay_rows = (
            await self.db.execute(
                select(
                    SalaryPayment.period_year,
                    SalaryPayment.period_month,
                    SalaryPayment.status,
                    func.sum(SalaryPayment.net_amount),
                    func.count(SalaryPayment.id),
                )
                .where(
                    SalaryPayment.tenant_id == tenant_id,
                    SalaryPayment.deleted_at.is_(None),
                )
                .group_by(
                    SalaryPayment.period_year, SalaryPayment.period_month, SalaryPayment.status
                )
            )
        ).all()

        agg: dict[tuple[int, int], dict] = {}
        ytd_net_paid = _ZERO
        for yr, mo, status, net, cnt in pay_rows:
            slot = agg.setdefault((yr, mo), {"paid": _ZERO, "pending": _ZERO, "count": 0})
            if status == "paid":
                slot["paid"] += _dec(net)
                if yr == today.year:
                    ytd_net_paid += _dec(net)
            else:
                slot["pending"] += _dec(net)
            slot["count"] += int(cnt or 0)

        by_month = [
            MonthPoint(
                period=_period(y, m),
                net_paid=agg.get((y, m), {}).get("paid", _ZERO),
                net_pending=agg.get((y, m), {}).get("pending", _ZERO),
                count=agg.get((y, m), {}).get("count", 0),
            )
            for (y, m) in periods
        ]

        reg = await self.payroll_register(tenant_id, today.month, today.year)
        coverage = (reg.paid_count / reg.headcount * 100) if reg.headcount else 0.0

        dept_map: dict[str, dict] = {}
        for e in emps:
            if e.status == "terminated":
                continue
            d = (e.department or "Unassigned")
            slot = dept_map.setdefault(d, {"headcount": 0, "monthly_salary": _ZERO, "net_paid": _ZERO})
            slot["headcount"] += 1
            slot["monthly_salary"] += _dec(e.monthly_salary)
        for r in reg.rows:
            if r.status == "paid" and r.net_amount is not None:
                d = (r.department or "Unassigned")
                dept_map.setdefault(d, {"headcount": 0, "monthly_salary": _ZERO, "net_paid": _ZERO})
                dept_map[d]["net_paid"] += _dec(r.net_amount)
        by_department = [
            DeptBreakdown(department=k, headcount=v["headcount"],
                          monthly_salary=v["monthly_salary"], net_paid=v["net_paid"])
            for k, v in sorted(dept_map.items(), key=lambda kv: -kv[1]["monthly_salary"])
        ]

        return PayrollSummary(
            headcount_active=len(active),
            headcount_total=len(emps),
            monthly_commitment=monthly_commitment,
            this_month_period=_period(today.year, today.month),
            this_month_net_paid=reg.net_paid_total,
            this_month_net_pending=reg.net_pending_total,
            this_month_unpaid_count=reg.unpaid_count,
            this_month_coverage_pct=round(coverage, 1),
            ytd_net_paid=ytd_net_paid,
            by_month=by_month,
            by_department=by_department,
            by_status=by_status,
        )
