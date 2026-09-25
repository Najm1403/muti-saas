# services/payment_service.py
#
# Manages payments against a sale.
#
# Hierarchy enforced:
#   Tenant → Restaurant → Branch → Sale → Payment
#
# A sale may have multiple payments (split payment: part cash, part card).
# Payments are always submitted after the sale is created.
#
# Dependencies:
#   - repositories/payment_repository.py — create, get_by_id, get_by_sale
#   - repositories/sale_repository.py    — verifies the sale belongs to tenant
#   - schemas/payment.py                 — PaymentCreate, PaymentResponse
#   - core/exceptions.py                 — NotFoundError

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError, ValidationError
from sqlalchemy import select, func
from models.sale import Sale
from models.payment import Payment
from models.product import Product
from repositories.payment_repository import PaymentRepository
from repositories.sale_repository import SaleRepository
from schemas.payment import PaymentCreate, PaymentResponse


class PaymentService:
    """
    Records and retrieves payments for POS sales.

    Split payments (e.g. part cash + part card for one sale) are supported:
    POST /payments can be called multiple times for the same sale_id.

    The service verifies the target sale exists and belongs to the requesting
    tenant before creating any payment record.  This prevents a tenant from
    attaching payments to another tenant's sales.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PaymentRepository(db)
        self.sale_repo = SaleRepository(db)

    # ── private helpers ──────────────────────────────────────────────────

    async def _verify_sale(self, sale_id: UUID, tenant_id: UUID) -> None:
        """
        Raise NotFoundError if the sale does not exist or belongs to a different tenant.

        Called before creating a payment to ensure the payment is linked to
        a valid, tenant-owned sale.
        """
        if not await self.sale_repo.get_by_id(sale_id, tenant_id):
            raise NotFoundError("Sale not found.")

    # ── public interface ─────────────────────────────────────────────────

    async def create(self, data: PaymentCreate, tenant_id: UUID) -> PaymentResponse:
        """
        Record a payment against a sale.

        Verifies the sale belongs to the tenant, then creates the payment row.
        Multiple calls with the same sale_id are allowed (split payment).

        payment_method is a free-text field: "CASH", "CARD", "DIGITAL", etc.
        reference is optional — used for card/digital transaction references.
        """
        await self._verify_sale(data.sale_id, tenant_id)
        await self.db.execute(select(Sale.id).where(Sale.id == data.sale_id).with_for_update())
        sale = await self.sale_repo.get_by_id(data.sale_id, tenant_id)
        applied = await self.db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.sale_id == sale.id, Payment.deleted_at.is_(None)))
        due = sale.total - applied
        if due <= 0 or sale.status in {"CANCELLED", "REFUNDED"}:
            raise ValidationError("Sale has no outstanding payment.")
        if data.amount > due and data.payment_method != "Cash":
            raise ValidationError("Non-cash payment exceeds the remaining amount.")
        tender = data.amount
        payment = await self.repo.create(data.model_copy(update={"amount": min(tender, due)}))
        payment.tendered_amount = tender
        if payment.amount == due and sale.status == "PENDING":
            # New orders reserve stock at placement. Pre-migration pending orders
            # reserve here, once, using only their backfilled composed variant IDs.
            if not sale.variant_inventory_reserved:
                from services.variant_service import VariantService
                lines = []
                for item in sale.items:
                    if item.quantity != int(item.quantity):
                        raise ValidationError("Legacy order has fractional units; recreate it with whole quantities.")
                    lines.append((item.variant_id, int(item.quantity), item.id))
                await VariantService(self.db, created_by=sale.user_id).deduct(tenant_id, lines, sale.id, branch_id=sale.branch_id)
                sale.variant_inventory_reserved = True
            sale.status = "COMPLETED"
        await self.db.commit()
        return PaymentResponse.model_validate(payment)

    async def get(self, id: UUID, tenant_id: UUID) -> PaymentResponse:
        """
        Return a single payment by UUID, scoped to the tenant.

        The repository joins Payment → Sale → Branch → Restaurant to scope
        by tenant, so the id alone is not enough — the tenant must match.
        """
        payment = await self.repo.get_by_id(id, tenant_id)
        if not payment:
            raise NotFoundError("Payment not found.")
        return PaymentResponse.model_validate(payment)

    async def list_by_sale(
        self, sale_id: UUID, tenant_id: UUID
    ) -> list[PaymentResponse]:
        """
        Return all payments for a sale, scoped to the tenant.

        Verifies the sale exists first so a cross-tenant sale_id returns 404
        rather than silently returning an empty list.
        """
        await self._verify_sale(sale_id, tenant_id)
        payments = await self.repo.get_by_sale(sale_id, tenant_id)
        return [PaymentResponse.model_validate(p) for p in payments]
