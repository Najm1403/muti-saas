# services/platform_hr_service.py
#
# Platform-company HR: employee records + monthly salary payments + payroll
# analytics. Not tenant-scoped. Employee numbers are auto-assigned globally
# ("PLT-0001") and never recycled.

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from core.exceptions import ConflictError, NotFoundError, ValidationError
from models.platform_admin import PlatformAdmin
from models.platform_employee import PlatformEmployee
from models.platform_department import PlatformDepartment
from models.platform_salary_payment import PlatformSalaryPayment
from schemas.platform_employee import (
    DeptBreakdown,
    MonthPoint,
    PayrollRegister,
    PayrollRegisterRow,
    PayrollSummary,
    PlatformEmployeeCreate,
    PlatformEmployeeResponse,
    PlatformEmployeeUpdate,
    PlatformSalaryPaymentCreate,
    PlatformSalaryPaymentResponse,
    PlatformSalaryPaymentUpdate,
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


class PlatformHRService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Numbering ─────────────────────────────────────────────

    async def _next_employee_no(self) -> tuple[int, str]:
        max_seq = await self.db.scalar(
            select(func.coalesce(func.max(PlatformEmployee.seq), 0))
        )
        seq = int(max_seq or 0) + 1
        return seq, f"PLT-{seq:04d}"

    # ── Employee helpers ─────────────────────────────────────

    async def _emp_or_404(self, id: UUID) -> PlatformEmployee:
        row = await self.db.execute(
            select(PlatformEmployee).where(
                PlatformEmployee.id == id, PlatformEmployee.deleted_at.is_(None)
            )
        )
        emp = row.scalar_one_or_none()
        if not emp:
            raise NotFoundError("Employee not found.")
        return emp

    async def _payroll_rollup(self, employee_ids: list[UUID]) -> dict[UUID, dict]:
        if not employee_ids:
            return {}
        today = date.today()
        rows = (
            await self.db.execute(
                select(
                    PlatformSalaryPayment.platform_employee_id,
                    PlatformSalaryPayment.period_year,
                    PlatformSalaryPayment.period_month,
                ).where(
                    PlatformSalaryPayment.platform_employee_id.in_(employee_ids),
                    PlatformSalaryPayment.deleted_at.is_(None),
                    PlatformSalaryPayment.status == "paid",
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

    def _emp_response(self, emp: PlatformEmployee, rollup: dict) -> PlatformEmployeeResponse:
        return PlatformEmployeeResponse(
            id=emp.id,
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

    # ── Employee CRUD ────────────────────────────────────────

    async def list_employees(
        self,
        *,
        status: str | None = None,
        department: str | None = None,
        q: str | None = None,
        skip: int = 0,
        limit: int = 200,
    ) -> list[PlatformEmployeeResponse]:
        stmt = select(PlatformEmployee).where(PlatformEmployee.deleted_at.is_(None))
        if status:
            stmt = stmt.where(PlatformEmployee.status == status)
        if department:
            stmt = stmt.where(PlatformEmployee.department == department)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    PlatformEmployee.full_name.ilike(like),
                    PlatformEmployee.employee_no.ilike(like),
                    PlatformEmployee.designation.ilike(like),
                    PlatformEmployee.email.ilike(like),
                )
            )
        stmt = stmt.order_by(PlatformEmployee.seq).offset(skip).limit(limit)
        emps = (await self.db.execute(stmt)).scalars().all()
        rollups = await self._payroll_rollup([e.id for e in emps])
        return [self._emp_response(e, rollups.get(e.id, {})) for e in emps]

    async def get_employee(self, id: UUID) -> PlatformEmployeeResponse:
        emp = await self._emp_or_404(id)
        rollups = await self._payroll_rollup([emp.id])
        return self._emp_response(emp, rollups.get(emp.id, {}))

    async def create_employee(self, data: PlatformEmployeeCreate) -> PlatformEmployeeResponse:
        seq, emp_no = await self._next_employee_no()
        emp = PlatformEmployee(seq=seq, employee_no=emp_no, **data.model_dump())
        self.db.add(emp)
        await self.db.commit()
        return await self.get_employee(emp.id)

    async def update_employee(
        self, id: UUID, data: PlatformEmployeeUpdate
    ) -> PlatformEmployeeResponse:
        emp = await self._emp_or_404(id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(emp, k, v)
        await self.db.commit()
        return await self.get_employee(id)

    async def delete_employee(self, id: UUID) -> None:
        emp = await self._emp_or_404(id)
        paid = await self.db.scalar(
            select(func.count(PlatformSalaryPayment.id)).where(
                PlatformSalaryPayment.platform_employee_id == emp.id,
                PlatformSalaryPayment.deleted_at.is_(None),
                PlatformSalaryPayment.status == "paid",
            )
        )
        if paid:
            emp.status = "terminated"
        emp.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def departments(self) -> list[str]:
        rows = await self.db.execute(
            select(PlatformEmployee.department)
            .where(
                PlatformEmployee.deleted_at.is_(None),
                PlatformEmployee.department.is_not(None),
                PlatformEmployee.department != "",
            )
            .distinct()
            .order_by(PlatformEmployee.department)
        )
        existing = [r[0] for r in rows.all()]
        saved = (await self.db.scalars(select(PlatformDepartment.name))).all()
        return sorted(set(existing) | set(saved), key=str.casefold)

    async def create_department(self, name: str) -> str:
        name = name.strip()
        if not name or len(name) > 80:
            raise ValidationError("Department name must contain 1 to 80 characters.")
        existing = next((d for d in await self.departments() if d.casefold() == name.casefold()), None)
        if existing:
            name = existing
        try:
            async with self.db.begin_nested():
                self.db.add(PlatformDepartment(name=name))
                await self.db.flush()
        except IntegrityError:
            saved = await self.db.scalar(select(PlatformDepartment.name).where(func.lower(PlatformDepartment.name) == name.lower()))
            if saved is None:
                raise
            name = saved
        await self.db.commit()
        return name

    # ── Salary payment helpers ──────────────────────────────

    async def _pay_or_404(self, id: UUID) -> PlatformSalaryPayment:
        row = await self.db.execute(
            select(PlatformSalaryPayment).where(
                PlatformSalaryPayment.id == id,
                PlatformSalaryPayment.deleted_at.is_(None),
            )
        )
        pay = row.scalar_one_or_none()
        if not pay:
            raise NotFoundError("Salary payment not found.")
        return pay

    @staticmethod
    def _net(gross, bonus, deductions) -> Decimal:
        return (_dec(gross) + _dec(bonus) - _dec(deductions)).quantize(Decimal("0.01"))

    def _pay_response(self, row) -> PlatformSalaryPaymentResponse:
        p: PlatformSalaryPayment = row[0]
        return PlatformSalaryPaymentResponse(
            id=p.id,
            platform_employee_id=p.platform_employee_id,
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
            paid_by=p.paid_by,
            paid_by_name=row.paid_by_name,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )

    def _pay_base_select(self):
        return (
            select(
                PlatformSalaryPayment,
                PlatformEmployee.employee_no.label("employee_no"),
                PlatformEmployee.full_name.label("employee_name"),
                PlatformEmployee.department.label("department"),
                PlatformAdmin.full_name.label("paid_by_name"),
            )
            .join(
                PlatformEmployee,
                PlatformSalaryPayment.platform_employee_id == PlatformEmployee.id,
            )
            .outerjoin(PlatformAdmin, PlatformSalaryPayment.paid_by == PlatformAdmin.id)
            .where(PlatformSalaryPayment.deleted_at.is_(None))
        )

    # ── Salary payment CRUD ─────────────────────────────────

    async def list_payments(
        self,
        *,
        employee_id: UUID | None = None,
        period_month: int | None = None,
        period_year: int | None = None,
        status: str | None = None,
        q: str | None = None,
        skip: int = 0,
        limit: int = 300,
    ) -> list[PlatformSalaryPaymentResponse]:
        stmt = self._pay_base_select()
        if employee_id:
            stmt = stmt.where(PlatformSalaryPayment.platform_employee_id == employee_id)
        if period_month:
            stmt = stmt.where(PlatformSalaryPayment.period_month == period_month)
        if period_year:
            stmt = stmt.where(PlatformSalaryPayment.period_year == period_year)
        if status:
            stmt = stmt.where(PlatformSalaryPayment.status == status)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    PlatformEmployee.full_name.ilike(like),
                    PlatformEmployee.employee_no.ilike(like),
                )
            )
        stmt = stmt.order_by(
            PlatformSalaryPayment.period_year.desc(),
            PlatformSalaryPayment.period_month.desc(),
            PlatformEmployee.seq,
        ).offset(skip).limit(limit)
        rows = (await self.db.execute(stmt)).all()
        return [self._pay_response(r) for r in rows]

    async def get_payment(self, id: UUID) -> PlatformSalaryPaymentResponse:
        rows = await self.db.execute(
            self._pay_base_select().where(PlatformSalaryPayment.id == id)
        )
        row = rows.first()
        if not row:
            raise NotFoundError("Salary payment not found.")
        return self._pay_response(row)

    async def create_payment(
        self, paid_by: UUID | None, data: PlatformSalaryPaymentCreate
    ) -> PlatformSalaryPaymentResponse:
        emp = await self._emp_or_404(data.platform_employee_id)

        dup = await self.db.scalar(
            select(PlatformSalaryPayment.id).where(
                PlatformSalaryPayment.platform_employee_id == emp.id,
                PlatformSalaryPayment.period_year == data.period_year,
                PlatformSalaryPayment.period_month == data.period_month,
                PlatformSalaryPayment.deleted_at.is_(None),
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

        pay = PlatformSalaryPayment(
            platform_employee_id=emp.id,
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
            paid_by=paid_by,
        )
        self.db.add(pay)
        await self.db.commit()
        return await self.get_payment(pay.id)

    async def update_payment(
        self, id: UUID, data: PlatformSalaryPaymentUpdate
    ) -> PlatformSalaryPaymentResponse:
        pay = await self._pay_or_404(id)
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
        return await self.get_payment(id)

    async def delete_payment(self, id: UUID) -> None:
        pay = await self._pay_or_404(id)
        pay.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    # ── Payroll register (one month) ────────────────────────

    async def payroll_register(self, period_month: int, period_year: int) -> PayrollRegister:
        emps = (
            await self.db.execute(
                select(PlatformEmployee)
                .where(
                    PlatformEmployee.deleted_at.is_(None),
                    PlatformEmployee.status != "terminated",
                )
                .order_by(PlatformEmployee.seq)
            )
        ).scalars().all()

        pays = {
            p.platform_employee_id: p
            for p in (
                await self.db.execute(
                    select(PlatformSalaryPayment).where(
                        PlatformSalaryPayment.deleted_at.is_(None),
                        PlatformSalaryPayment.period_month == period_month,
                        PlatformSalaryPayment.period_year == period_year,
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

    # ── Analytics ───────────────────────────────────────────

    async def summary(self) -> PayrollSummary:
        today = date.today()

        emps = (
            await self.db.execute(
                select(PlatformEmployee).where(PlatformEmployee.deleted_at.is_(None))
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
                    PlatformSalaryPayment.period_year,
                    PlatformSalaryPayment.period_month,
                    PlatformSalaryPayment.status,
                    func.sum(PlatformSalaryPayment.net_amount),
                    func.count(PlatformSalaryPayment.id),
                )
                .where(PlatformSalaryPayment.deleted_at.is_(None))
                .group_by(
                    PlatformSalaryPayment.period_year,
                    PlatformSalaryPayment.period_month,
                    PlatformSalaryPayment.status,
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

        reg = await self.payroll_register(today.month, today.year)
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
