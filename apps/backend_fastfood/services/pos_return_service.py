"""Cashier-facing cancellation and sales-return workflows."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.exceptions import ForbiddenError, NotFoundError, ValidationError
from models.cashier_session import CashierSession
from models.refund import Refund
from models.refund_item import RefundItem
from models.sale import Sale
from models.sale_item import SaleItem
from schemas.refund import (
    PosCancelCreate, PosRefundResult, PosReturnCreate,
    RefundCreate, RefundItemCreate,
)
from services.refund_service import RefundService


class PosReturnService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _require_permission(self, user_id: UUID, tenant_id: UUID) -> None:
        from api.dependencies import get_user_permissions
        permissions = await get_user_permissions(self.db, user_id, tenant_id)
        if "*" not in permissions and "sales.cancel" not in permissions:
            raise ForbiddenError(
                "Cancel and return operations require the sales.cancel permission.",
                code="PERMISSION_DENIED",
            )

    async def _open_session(self, *, tenant_id: UUID, branch_id: UUID,
                            device_id: UUID, user_id: UUID) -> CashierSession:
        session = await self.db.scalar(
            select(CashierSession).where(
                CashierSession.tenant_id == tenant_id,
                CashierSession.branch_id == branch_id,
                CashierSession.device_id == device_id,
                CashierSession.user_id == user_id,
                CashierSession.closed_at.is_(None),
            ).order_by(CashierSession.opened_at.desc()).limit(1)
        )
        if session is None:
            raise ValidationError("Open a cashier shift before cancelling or returning a sale.")
        return session

    async def _sale(self, sale_id: UUID, branch_id: UUID, *, lock: bool = True) -> Sale:
        query = select(Sale).options(
            selectinload(Sale.items), selectinload(Sale.payments)
        ).where(
            Sale.id == sale_id, Sale.branch_id == branch_id,
            Sale.deleted_at.is_(None),
        )
        if lock:
            query = query.with_for_update(of=Sale)
        sale = await self.db.scalar(query)
        if sale is None:
            raise NotFoundError("Sale not found in this branch.")
        return sale

    async def _returned_quantities(self, sale_id: UUID) -> dict[UUID, Decimal]:
        rows = await self.db.execute(
            select(RefundItem.sale_item_id, func.coalesce(func.sum(RefundItem.quantity), 0))
            .join(Refund, RefundItem.refund_id == Refund.id)
            .where(Refund.sale_id == sale_id, Refund.status == "COMPLETED",
                   Refund.deleted_at.is_(None))
            .group_by(RefundItem.sale_item_id)
        )
        return {item_id: Decimal(str(quantity)) for item_id, quantity in rows.all()}

    async def _payment_breakdown(self, sale: Sale, target: Decimal) -> dict[str, Decimal]:
        previous = (await self.db.scalars(select(Refund).where(
            Refund.sale_id == sale.id, Refund.status == "COMPLETED",
            Refund.deleted_at.is_(None),
        ))).all()
        already: dict[str, Decimal] = {}
        for refund in previous:
            breakdown = refund.payment_breakdown or {refund.refund_method: refund.amount}
            for method, amount in breakdown.items():
                already[method] = already.get(method, Decimal(0)) + Decimal(str(amount))

        available: dict[str, Decimal] = {}
        for payment in sale.payments:
            available[payment.payment_method] = (
                available.get(payment.payment_method, Decimal(0))
                + Decimal(str(payment.amount))
            )
        for method, amount in already.items():
            available[method] = max(Decimal(0), available.get(method, Decimal(0)) - amount)

        remaining = target
        result: dict[str, Decimal] = {}
        for method, amount in available.items():
            applied = min(amount, remaining)
            if applied > 0:
                result[method] = applied
                remaining -= applied
            if remaining <= 0:
                break
        if remaining > Decimal("0.01"):
            raise ValidationError("Original payment allocation is incomplete; contact an administrator.")
        if remaining > 0:
            if not result:
                raise ValidationError("Original payment allocation is incomplete; contact an administrator.")
            # Sub-cent rounding slack (at most 1 cent, from proportional
            # allocation across multiple payment methods) — fold it into
            # whichever method already received the most, so the breakdown
            # sums to exactly `target` instead of silently under-reporting
            # by up to a cent against the refund's recorded amount.
            largest_method = max(result, key=result.get)
            result[largest_method] += remaining
        return result

    @staticmethod
    def _number(sale: Sale, operation: str) -> str:
        suffix = uuid4().hex[:8].upper()
        return f"{operation}-{sale.sale_number}-{suffix}"[:50]

    @staticmethod
    def _redistribute(raw: list[Decimal], target: Decimal) -> list[Decimal]:
        """Adjusts already-rounded proportional per-line shares so they sum
        to exactly `target`, without ever pushing an individual share
        negative.

        The gap between sum(raw) and target is usually at most a cent or
        two from per-line ROUND_HALF_UP quantization, but can be larger
        when `target` is capped below sum(raw) by the sale's remaining
        refundable total (an earlier partial refund/cancel already
        consumed some of it) — dumping that whole gap onto the last line
        unconditionally could drive it negative. Instead this walks from
        the last line backward, taking as much of the shortfall as each
        line can safely give up (down to zero) before moving to the
        previous one, spreading the deficit instead of concentrating it.
        `target` is always > 0 by the time this is called, so the deficit
        (target - sum(raw) when negative) is always strictly less than
        sum(raw) and is therefore always fully absorbable this way.
        """
        if not raw:
            return raw
        diff = target - sum(raw, Decimal(0))
        if diff == 0:
            return raw
        adjusted = list(raw)
        if diff > 0:
            adjusted[-1] += diff
            return adjusted
        shortfall = -diff
        for i in range(len(adjusted) - 1, -1, -1):
            take = min(adjusted[i], shortfall)
            adjusted[i] -= take
            shortfall -= take
            if shortfall <= 0:
                break
        return adjusted

    async def _create(self, *, sale: Sale, selected: list[tuple[SaleItem, Decimal]],
                      reason: str | None, refund_type: str, user_id: UUID,
                      session: CashierSession, full_sale_status: str) -> PosRefundResult:
        prior_amount = Decimal(str(await self.db.scalar(
            select(func.coalesce(func.sum(Refund.amount), 0)).where(
                Refund.sale_id == sale.id, Refund.status == "COMPLETED",
                Refund.deleted_at.is_(None))
        ) or 0))
        remaining_total = sale.total - prior_amount
        returned = await self._returned_quantities(sale.id)
        returns_everything = all(
            returned.get(line.id, Decimal(0)) + next(
                (qty for chosen, qty in selected if chosen.id == line.id), Decimal(0)
            ) == line.quantity for line in sale.items
        )

        raw = []
        for line, qty in selected:
            line_share = (line.total * qty / line.quantity) if line.quantity else Decimal(0)
            amount = (line_share * sale.total / sale.subtotal) if sale.subtotal else Decimal(0)
            raw.append(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        if returns_everything:
            target = remaining_total
        else:
            target = min(sum(raw, Decimal(0)), remaining_total)
        if target <= 0:
            raise ValidationError("This sale has no refundable amount remaining.")
        raw = self._redistribute(raw, target)

        payment_breakdown = await self._payment_breakdown(sale, target)
        refund_method = next(iter(payment_breakdown)) if len(payment_breakdown) == 1 else "Multiple"
        payload = RefundCreate(
            sale_id=sale.id, branch_id=sale.branch_id, device_id=session.device_id,
            refund_number=self._number(sale, "CAN" if refund_type == "CANCEL" else "RET"),
            refunded_at=datetime.now(timezone.utc), amount=target,
            refund_method=refund_method, reason=reason,
            items=[RefundItemCreate(
                sale_item_id=line.id, product_name=line.product_name,
                quantity=int(qty), unit_price=line.unit_price, amount=amount,
            ) for (line, qty), amount in zip(selected, raw)],
        )
        result = await RefundService(self.db).create(
            payload, session.tenant_id, created_by=user_id,
            refund_type=refund_type, session_id=session.id,
            full_sale_status=full_sale_status,
            payment_breakdown=payment_breakdown,
        )
        return PosRefundResult(
            id=result.id, sale_id=sale.id, sale_number=sale.sale_number,
            refund_number=result.refund_number, refund_type=refund_type,
            amount=result.amount, status=result.status,
        )

    async def cancel(self, *, sale_id: UUID, data: PosCancelCreate,
                     tenant_id: UUID, branch_id: UUID, device_id: UUID,
                     user_id: UUID) -> PosRefundResult:
        await self._require_permission(user_id, tenant_id)
        session = await self._open_session(tenant_id=tenant_id, branch_id=branch_id,
                                           device_id=device_id, user_id=user_id)
        sale = await self._sale(sale_id, branch_id)
        if sale.user_id != user_id or sale.device_id != device_id:
            raise ForbiddenError("Only the cashier and device that made this bill can cancel it.")
        if sale.status != "COMPLETED":
            raise ValidationError("Only a completed, unreturned sale can be cancelled.")
        if sale.session_id != session.id:
            raise ValidationError("This bill belongs to an earlier shift; use Sales Return instead.")
        if await self.db.scalar(select(Refund.id).where(
                Refund.sale_id == sale.id, Refund.status == "COMPLETED").limit(1)):
            raise ValidationError("A bill with an existing return cannot be cancelled.")
        return await self._create(
            sale=sale, selected=[(line, line.quantity) for line in sale.items],
            reason=data.reason, refund_type="CANCEL", user_id=user_id,
            session=session, full_sale_status="CANCELLED",
        )

    async def return_items(self, *, sale_id: UUID, data: PosReturnCreate,
                           tenant_id: UUID, branch_id: UUID, device_id: UUID,
                           user_id: UUID) -> PosRefundResult:
        await self._require_permission(user_id, tenant_id)
        session = await self._open_session(tenant_id=tenant_id, branch_id=branch_id,
                                           device_id=device_id, user_id=user_id)
        sale = await self._sale(sale_id, branch_id)
        if sale.status not in {"COMPLETED"}:
            raise ValidationError("This bill is cancelled or already fully returned.")
        lines = {line.id: line for line in sale.items}
        returned = await self._returned_quantities(sale.id)
        seen: set[UUID] = set()
        selected: list[tuple[SaleItem, Decimal]] = []
        for requested in data.items:
            if requested.sale_item_id in seen:
                raise ValidationError("A sale item can only appear once in a return.")
            seen.add(requested.sale_item_id)
            line = lines.get(requested.sale_item_id)
            if line is None:
                raise ValidationError("A selected item does not belong to this invoice.")
            remaining = line.quantity - returned.get(line.id, Decimal(0))
            if requested.quantity > remaining:
                raise ValidationError(
                    f"Only {remaining} of '{line.product_name}' remains returnable."
                )
            selected.append((line, requested.quantity))
        return await self._create(
            sale=sale, selected=selected, reason=data.reason,
            refund_type="RETURN", user_id=user_id, session=session,
            full_sale_status="REFUNDED",
        )
