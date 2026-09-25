# services/cashier_session_service.py
#
# Manages cashier shift sessions on a POS device.
# One OPEN session per device at a time — opening a second raises ValidationError.

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError, ValidationError
from core.payment_methods import PAYMENT_METHODS, label_lenient
from models.branch import Branch
from models.cashier_session import CashierSession
from models.device import Device
from models.payment import Payment
from models.refund import Refund
from models.sale import Sale
from models.user import User
from schemas.pos_session import (
    SessionCloseRequest,
    SessionCloseResponse,
    SessionOpenRequest,
    SessionResponse,
    SessionSummary,
    SessionSummaryResponse,
    SessionVarianceItem,
)


class CashierSessionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _to_schema(self, s: CashierSession) -> SessionResponse:
        return SessionResponse(
            id=s.id,
            device_id=s.device_id,
            user_id=s.user_id,
            branch_id=s.branch_id,
            tenant_id=s.tenant_id,
            opened_at=s.opened_at,
            closed_at=s.closed_at,
            opening_cash=s.opening_cash,
            closing_cash=s.closing_cash,
            status=s.status,
            notes=s.notes,
            created_at=s.created_at,
            shift_number=s.shift_number,
        )

    async def _get_open(
        self, device_id: UUID, tenant_id: UUID
    ) -> CashierSession | None:
        """The device's open session, regardless of which cashier owns it.

        Used only where "is this device already occupied" is the actual
        question (open/close/summary) — never for deciding what a given
        cashier should see as "their" current session (use
        `_get_open_for_user` for that; see get_current()).
        """
        result = await self.db.execute(
            select(CashierSession).where(
                CashierSession.device_id == device_id,
                CashierSession.tenant_id == tenant_id,
                CashierSession.status == "OPEN",
            )
        )
        return result.scalar_one_or_none()

    async def _get_open_for_user(
        self, device_id: UUID, user_id: UUID, tenant_id: UUID
    ) -> CashierSession | None:
        result = await self.db.execute(
            select(CashierSession).where(
                CashierSession.device_id == device_id,
                CashierSession.user_id == user_id,
                CashierSession.tenant_id == tenant_id,
                CashierSession.status == "OPEN",
            )
        )
        return result.scalar_one_or_none()

    async def get_open_elsewhere(
        self, user_id: UUID, device_id: UUID, tenant_id: UUID
    ) -> CashierSession | None:
        """Any OPEN session this user holds on a device OTHER than [device_id].

        Used at login time (not just shift-open) to enforce "one open shift
        per cashier at a time" — the per-device uniqueness in `open()` alone
        would otherwise let the same cashier hold two simultaneously-open
        shifts, one per device, with no warning to anyone.

        Uses scalars().first() rather than scalar_one_or_none(): this is
        exactly the state this method exists to guard against, so if it
        ever does happen (a login race, or legacy data), returning the
        first one and surfacing the intended "shift open elsewhere" error
        is far better than crashing with an unhandled MultipleResultsFound
        and locking the cashier out of logging in anywhere.
        """
        result = await self.db.execute(
            select(CashierSession).where(
                CashierSession.user_id == user_id,
                CashierSession.tenant_id == tenant_id,
                CashierSession.status == "OPEN",
                CashierSession.device_id != device_id,
            ).order_by(CashierSession.opened_at)
        )
        return result.scalars().first()

    def _sale_filter(self, s: CashierSession):
        """Sales that belong to this shift.

        Primary match is Sale.session_id; sales that predate session tracking
        (or arrived offline without a session id) fall back to a
        device + cashier + time-window match.
        """
        window_end = s.closed_at if s.closed_at is not None else datetime.now(timezone.utc)
        return and_(
            Sale.deleted_at.is_(None),
            Sale.status.notin_(["CANCELLED", "PENDING"]),
            or_(
                Sale.session_id == s.id,
                and_(
                    Sale.session_id.is_(None),
                    Sale.device_id == s.device_id,
                    Sale.user_id == s.user_id,
                    Sale.sold_at >= s.opened_at,
                    Sale.sold_at <= window_end,
                ),
            ),
        )

    def _refund_filter(self, s: CashierSession, refund_type: str = "RETURN"):
        window_end = s.closed_at if s.closed_at is not None else datetime.now(timezone.utc)
        return and_(
            Refund.deleted_at.is_(None),
            Refund.device_id == s.device_id,
            Refund.branch_id == s.branch_id,
            Refund.refunded_at >= s.opened_at,
            Refund.refunded_at <= window_end,
            Refund.status == "COMPLETED",
            Refund.refund_type == refund_type,
        )

    async def _summary(self, s: CashierSession) -> SessionSummary:
        sale_filter = self._sale_filter(s)

        totals = await self.db.execute(
            select(
                func.count(Sale.id),
                func.coalesce(func.sum(Sale.subtotal), 0),
                func.coalesce(func.sum(Sale.discount), 0),
                func.coalesce(func.sum(Sale.tax_amount), 0),
                func.coalesce(func.sum(Sale.total), 0),
            ).where(sale_filter)
        )
        sales_count, subtotal_total, discount_total, tax_total, gross_total = totals.one()

        by_method_rows = await self.db.execute(
            select(
                Sale.id,
                Sale.total,
                Payment.payment_method,
                Payment.amount,
            )
            .select_from(Payment)
            .join(Sale, Payment.sale_id == Sale.id)
            .where(sale_filter)
        )
        # Pre-seed every canonical method at zero so the shift-close screen always
        # shows the full Cash/JazzCash/EasyPaisa/Online Transfer/Credit Card
        # breakdown; `label_lenient` folds any pre-existing free-text value
        # (old seed data, older app builds) onto its canonical label instead of
        # creating a duplicate row.
        by_payment_method: dict[str, Decimal] = {m: Decimal("0.00") for m in PAYMENT_METHODS}
        payments_by_sale: dict[UUID, tuple[Decimal, list[tuple[str, Decimal]]]] = {}
        for sale_id, sale_total, method, amount in by_method_rows.all():
            if sale_id not in payments_by_sale:
                payments_by_sale[sale_id] = (Decimal(str(sale_total)), [])
            payments_by_sale[sale_id][1].append((method, Decimal(str(amount))))

        for sale_total, sale_payments in payments_by_sale.values():
            for method, amount in sale_payments:
                label = label_lenient(method)
                by_payment_method[label] = by_payment_method.get(label, Decimal("0.00")) + amount
            # Any over-tender is change returned to the customer, not money
            # retained in the drawer. POS currently permits over-tender only
            # for Cash, so remove that excess from its reconciliation total.
            excess = max(sum((amount for _, amount in sale_payments), Decimal("0.00")) - sale_total,
                         Decimal("0.00"))
            if excess:
                by_payment_method["Cash"] = max(
                    by_payment_method.get("Cash", Decimal("0.00")) - excess,
                    Decimal("0.00"),
                )

        refund_records = list((await self.db.scalars(
            select(Refund).where(self._refund_filter(s))
        )).all())
        refunds_count = len(refund_records)
        refund_total = sum((Decimal(str(row.amount)) for row in refund_records), Decimal(0))
        refunds_by_payment_method: dict[str, Decimal] = {
            m: Decimal("0.00") for m in PAYMENT_METHODS
        }
        for row in refund_records:
            breakdown = row.payment_breakdown or {row.refund_method: row.amount}
            for method, amount in breakdown.items():
                label = label_lenient(method)
                refunds_by_payment_method[label] = (
                    refunds_by_payment_method.get(label, Decimal("0.00"))
                    + Decimal(str(amount))
                )
        cash_sales_total = by_payment_method.get("Cash", Decimal("0.00"))
        cash_refunds_total = refunds_by_payment_method.get("Cash", Decimal("0.00"))
        total_payments = sum(by_payment_method.values(), Decimal("0.00"))
        refund_total = Decimal(str(refund_total or 0))
        cancellation_records = list((await self.db.scalars(
            select(Refund).where(self._refund_filter(s, "CANCEL"))
        )).all())
        cancellations_count = len(cancellation_records)
        cancellation_total = sum(
            (Decimal(str(row.amount)) for row in cancellation_records), Decimal(0)
        )
        cancellations_by_payment_method: dict[str, Decimal] = {
            m: Decimal("0.00") for m in PAYMENT_METHODS
        }
        for row in cancellation_records:
            breakdown = row.payment_breakdown or {row.refund_method: row.amount}
            for method, amount in breakdown.items():
                label = label_lenient(method)
                cancellations_by_payment_method[label] = (
                    cancellations_by_payment_method.get(label, Decimal("0.00"))
                    + Decimal(str(amount))
                )

        return SessionSummary(
            sales_count=int(sales_count or 0),
            subtotal_total=Decimal(str(subtotal_total or 0)),
            discount_total=Decimal(str(discount_total or 0)),
            tax_total=Decimal(str(tax_total or 0)),
            gross_total=Decimal(str(gross_total or 0)),
            total_payments=total_payments,
            by_payment_method=by_payment_method,
            cash_sales_total=cash_sales_total,
            refunds_count=int(refunds_count or 0),
            refund_total=refund_total,
            refunds_by_payment_method=refunds_by_payment_method,
            cancellations_count=int(cancellations_count or 0),
            cancellation_total=Decimal(str(cancellation_total or 0)),
            cancellations_by_payment_method=cancellations_by_payment_method,
            net_total=Decimal(str(gross_total or 0)) - refund_total,
            opening_cash=s.opening_cash,
            expected_cash=s.opening_cash + cash_sales_total - cash_refunds_total,
        )

    async def summary(
        self, device_id: UUID, tenant_id: UUID
    ) -> SessionSummaryResponse:
        session = await self._get_open(device_id, tenant_id)
        if not session:
            raise NotFoundError("No open session found for this device.")
        return SessionSummaryResponse(
            session=self._to_schema(session),
            summary=await self._summary(session),
        )

    async def _next_shift_number(self, device: Device, opened_at: datetime) -> str:
        """YYMMDD + device letter + this device's Nth shift opened today
        (1-based) — e.g. "260924A1", then "260924A2" for the next shift on
        the same device later that day. Caller must hold the device row
        lock (see open()) so two concurrent opens on the same device can
        never compute the same sequence number.
        """
        day_start = datetime(opened_at.year, opened_at.month, opened_at.day, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        count_today = await self.db.scalar(
            select(func.count(CashierSession.id)).where(
                CashierSession.device_id == device.id,
                CashierSession.opened_at >= day_start,
                CashierSession.opened_at < day_end,
            )
        )
        return f"{opened_at.strftime('%y%m%d')}{device.letter}{(count_today or 0) + 1}"

    async def open(
        self,
        device_id: UUID,
        user_id: UUID,
        branch_id: UUID,
        tenant_id: UUID,
        data: SessionOpenRequest,
    ) -> SessionResponse:
        # Locks the device row so a concurrent open() on the same device
        # can't race either the "already open" check below or the daily
        # shift-number count in _next_shift_number().
        device = await self.db.scalar(
            select(Device).where(Device.id == device_id).with_for_update()
        )
        if not device:
            raise NotFoundError("Device not found.")

        existing = await self._get_open(device_id, tenant_id)
        if existing:
            raise ValidationError(
                "A session is already open on this device. Close it before opening a new one."
            )
        opened_at = datetime.now(timezone.utc)
        session = CashierSession(
            device_id=device_id,
            user_id=user_id,
            branch_id=branch_id,
            tenant_id=tenant_id,
            opened_at=opened_at,
            opening_cash=data.opening_cash,
            notes=data.notes,
            status="OPEN",
            shift_number=await self._next_shift_number(device, opened_at),
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return self._to_schema(session)

    async def close(
        self,
        device_id: UUID,
        user_id: UUID,
        tenant_id: UUID,
        data: SessionCloseRequest,
    ) -> SessionCloseResponse:
        session = await self._get_open(device_id, tenant_id)
        if not session:
            raise NotFoundError("No open session found for this device.")

        # GAP 4 — explicit ownership guard.
        # The one-session-per-device invariant makes this safe today, but an
        # explicit check means the guard survives any future relaxation of that rule.
        if session.user_id != user_id:
            raise ValidationError(
                "You can only close your own session. Ask the current session owner to close it."
            )
        session.closed_at = datetime.now(timezone.utc)
        session.closing_cash = data.closing_cash
        session.status = "CLOSED"
        if data.notes:
            session.notes = data.notes
        await self.db.commit()
        await self.db.refresh(session)

        summary = await self._summary(session)
        return SessionCloseResponse(
            session=self._to_schema(session),
            summary=summary,
            variance=data.closing_cash - summary.expected_cash,
        )

    async def get_current(
        self, device_id: UUID, user_id: UUID, tenant_id: UUID
    ) -> SessionResponse:
        """The CALLING cashier's own open session on this device.

        Deliberately scoped by user_id, not just device_id — a device can
        have another cashier's shift left open (e.g. they forgot to close
        out), and that must never be silently handed to whoever logs in
        next. A cashier with no open session of their own gets 404 here
        even while the device is "occupied"; open() then reports the real
        reason ("A session is already open on this device...") if they try
        to start one.
        """
        session = await self._get_open_for_user(device_id, user_id, tenant_id)
        if not session:
            raise NotFoundError("No open session found for this device.")
        return self._to_schema(session)

    async def list_history(
        self, user_id: UUID, tenant_id: UUID, limit: int = 50
    ) -> list[SessionResponse]:
        """This cashier's past shifts (closed sessions), newest first.

        Scoped by user_id only (not device_id) — a cashier's shift history
        follows them across whichever devices/branches they worked on.
        """
        result = await self.db.execute(
            select(CashierSession)
            .where(
                CashierSession.user_id == user_id,
                CashierSession.tenant_id == tenant_id,
                CashierSession.status == "CLOSED",
            )
            .order_by(CashierSession.closed_at.desc())
            .limit(limit)
        )
        return [self._to_schema(s) for s in result.scalars().all()]

    async def history_summary(
        self, session_id: UUID, user_id: UUID, tenant_id: UUID
    ) -> SessionSummaryResponse:
        """Full reconciliation summary for one of the cashier's own past
        (or current) shifts, looked up by id — unlike summary(), this works
        for a CLOSED session too, so a shift's totals remain reviewable
        after close, not just once at the moment of closing."""
        session = await self.db.get(CashierSession, session_id)
        if not session or session.tenant_id != tenant_id or session.user_id != user_id:
            raise NotFoundError("Session not found.")
        return SessionSummaryResponse(
            session=self._to_schema(session),
            summary=await self._summary(session),
        )

    async def list_variance(
        self,
        tenant_id: UUID,
        branch_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        allowed_branch_ids: set[UUID] | None = None,
        shortages_only: bool = False,
        limit: int = 100,
    ) -> list[SessionVarianceItem]:
        """CLOSED shifts with their cash variance — the tenant-admin-facing
        counterpart to what a cashier already sees on their own device at
        close time (see close()/_summary()). Reuses _summary() as-is for
        expected_cash, so this can never compute a different figure than
        the one the cashier actually saw when they closed the shift.
        """
        filters = [
            CashierSession.tenant_id == tenant_id,
            CashierSession.status == "CLOSED",
        ]
        if branch_id is not None:
            filters.append(CashierSession.branch_id == branch_id)
        if allowed_branch_ids is not None:
            filters.append(CashierSession.branch_id.in_(allowed_branch_ids))
        if date_from is not None:
            filters.append(CashierSession.closed_at >= date_from)
        if date_to is not None:
            filters.append(CashierSession.closed_at <= date_to)

        sessions = (await self.db.scalars(
            select(CashierSession)
            .where(*filters)
            .order_by(CashierSession.closed_at.desc())
            .limit(limit)
        )).all()
        if not sessions:
            return []

        branch_ids = {s.branch_id for s in sessions}
        device_ids = {s.device_id for s in sessions}
        user_ids = {s.user_id for s in sessions}
        branch_names = dict((await self.db.execute(
            select(Branch.id, Branch.name).where(Branch.id.in_(branch_ids))
        )).all())
        device_names = dict((await self.db.execute(
            select(Device.id, Device.name).where(Device.id.in_(device_ids))
        )).all())
        cashier_names = {
            uid: (full_name or username)
            for uid, full_name, username in (await self.db.execute(
                select(User.id, User.full_name, User.username).where(User.id.in_(user_ids))
            )).all()
        }

        items: list[SessionVarianceItem] = []
        for session in sessions:
            summary = await self._summary(session)
            variance = session.closing_cash - summary.expected_cash
            if shortages_only and variance >= 0:
                continue
            items.append(SessionVarianceItem(
                id=session.id,
                shift_number=session.shift_number,
                branch_id=session.branch_id,
                branch_name=branch_names.get(session.branch_id, "—"),
                device_id=session.device_id,
                device_name=device_names.get(session.device_id, "—"),
                user_id=session.user_id,
                cashier_name=cashier_names.get(session.user_id, "—"),
                opened_at=session.opened_at,
                closed_at=session.closed_at,
                opening_cash=session.opening_cash,
                closing_cash=session.closing_cash,
                expected_cash=summary.expected_cash,
                variance=variance,
            ))
        return items
