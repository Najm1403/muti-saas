# services/refund_service.py
#
# Manages refund creation and retrieval for the management API.
#
# Rules enforced:
#   - The refunded sale must exist and belong to the tenant.
#   - Each RefundItem must reference a SaleItem that belongs to that sale.
#   - The refund amount must equal the sum of its item amounts (±1 cent).
#   - refund_number must be unique within the branch.
#   - Refund + RefundItems are inserted atomically in a single flush.
#   - The parent Sale status is set to "REFUNDED" when the refund covers its full total.

from __future__ import annotations

from decimal import Decimal
from collections import defaultdict
from uuid import UUID, uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.exceptions import ConflictError, NotFoundError, ValidationError
from models.branch import Branch
from models.product import Product
from models.refund import Refund
from models.refund_item import RefundItem
from models.business import Business
from models.sale import Sale
from models.sale_item_option import SaleItemOption
from schemas.refund import RefundCreate, RefundItemResponse, RefundResponse

_TOLERANCE = Decimal("0.01")


class RefundService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _to_schema(self, refund: Refund) -> RefundResponse:
        return RefundResponse(
            id=refund.id,
            sale_id=refund.sale_id,
            branch_id=refund.branch_id,
            device_id=refund.device_id,
            refund_number=refund.refund_number,
            refunded_at=refund.refunded_at,
            amount=refund.amount,
            refund_method=refund.refund_method,
            payment_breakdown=refund.payment_breakdown or {refund.refund_method: refund.amount},
            reason=refund.reason,
            status=refund.status,
            refund_type=refund.refund_type,
            processed_by_user_id=refund.processed_by_user_id,
            session_id=refund.session_id,
            created_at=refund.created_at,
            updated_at=refund.updated_at,
            sync_status=refund.sync_status,
            synced_at=refund.synced_at,
            items=[
                RefundItemResponse(
                    id=i.id,
                    refund_id=i.refund_id,
                    sale_item_id=i.sale_item_id,
                    product_name=i.product_name,
                    quantity=i.quantity,
                    unit_price=i.unit_price,
                    amount=i.amount,
                    created_at=i.created_at,
                    updated_at=i.updated_at,
                    sync_status=i.sync_status,
                    synced_at=i.synced_at,
                )
                for i in refund.items
            ],
        )

    async def _get_sale(
        self, sale_id: UUID, branch_id: UUID, tenant_id: UUID
    ) -> Sale:
        """Fetch sale with items, verifying it belongs to the given tenant + branch."""
        result = await self.db.execute(
            select(Sale)
            .join(Branch, Sale.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .options(selectinload(Sale.items))
            .with_for_update(of=Sale)
            .where(
                Sale.id == sale_id,
                Sale.branch_id == branch_id,
                Business.tenant_id == tenant_id,
                Sale.deleted_at.is_(None),
            )
        )
        sale = result.scalar_one_or_none()
        if not sale:
            raise NotFoundError("Sale not found.")
        return sale

    async def create(self, data: RefundCreate, tenant_id: UUID, created_by=None,
                     *, refund_type: str = "RETURN", session_id=None,
                     full_sale_status: str = "REFUNDED",
                     payment_breakdown: dict[str, Decimal] | None = None) -> RefundResponse:
        # 1. Verify sale ownership.
        sale = await self._get_sale(data.sale_id, data.branch_id, tenant_id)

        if data.amount > 0:
            from models.payment import Payment
            free_guest = await self.db.scalar(select(Payment.id).where(
                Payment.sale_id == sale.id, Payment.payment_method == "Free Guest"
            ).limit(1))
            if free_guest:
                raise ValidationError("A Free Guest order has no paid amount to refund.")

        # 2. Guard duplicate refund_number within the branch.
        dup = await self.db.execute(
            select(Refund).where(
                Refund.branch_id == data.branch_id,
                Refund.refund_number == data.refund_number,
                Refund.deleted_at.is_(None),
            )
        )
        if dup.scalar_one_or_none():
            raise ConflictError(
                f"Refund number '{data.refund_number}' already exists for this branch."
            )

        # 3. Verify refund total matches sum of item amounts.
        computed = sum(i.amount for i in data.items)
        if abs(computed - data.amount) > _TOLERANCE:
            raise ValidationError(
                f"Refund amount mismatch: submitted {data.amount}, "
                f"sum of items {computed}."
            )

        # 4. Each RefundItem must reference a SaleItem from this sale.
        sale_item_ids = {item.id for item in sale.items}
        for ri in data.items:
            if ri.sale_item_id not in sale_item_ids:
                raise ValidationError(
                    f"SaleItem {ri.sale_item_id} does not belong to sale {data.sale_id}."
                )

        if sale.status != "COMPLETED":
            raise ValidationError("This sale cannot be refunded.")
        from models.device import Device
        if await self.db.scalar(select(Device.id).where(Device.id==data.device_id, Device.branch_id==data.branch_id,Device.deleted_at.is_(None))) is None:
            raise ValidationError("Refund device is not assigned to this branch.")
        prior = await self.db.scalar(select(func.coalesce(func.sum(Refund.amount), 0)).where(
            Refund.sale_id == sale.id, Refund.deleted_at.is_(None), Refund.status == "COMPLETED"))
        if prior + data.amount > sale.total:
            raise ValidationError("Refund exceeds the remaining sale amount.")
        quantities = {}
        for ri in data.items:
            quantities[ri.sale_item_id] = quantities.get(ri.sale_item_id, Decimal(0)) + ri.quantity
        all_units_returned = True
        for item in sale.items:
            used = await self.db.scalar(select(func.coalesce(func.sum(RefundItem.quantity), 0))
                .join(Refund, RefundItem.refund_id == Refund.id).where(
                    RefundItem.sale_item_id == item.id, Refund.deleted_at.is_(None), Refund.status == "COMPLETED"))
            if used + quantities.get(item.id, 0) > item.quantity:
                raise ValidationError("Refund quantity exceeds the remaining purchased quantity.")
            if used + quantities.get(item.id, 0) < item.quantity:
                all_units_returned = False

        # 5. Persist refund + items atomically.
        refund_id = data.id or uuid4()
        refund = Refund(
            id=refund_id,
            sale_id=data.sale_id,
            branch_id=data.branch_id,
            device_id=data.device_id,
            refund_number=data.refund_number,
            refunded_at=data.refunded_at,
            amount=data.amount,
            refund_method=data.refund_method,
            payment_breakdown={
                key: str(value) for key, value in (
                    payment_breakdown or {data.refund_method: data.amount}
                ).items()
            },
            reason=data.reason,
            status="COMPLETED",
            refund_type=refund_type,
            processed_by_user_id=created_by,
            session_id=session_id,
        )
        self.db.add(refund)
        await self.db.flush()

        sale_item_by_id = {i.id: i for i in sale.items}
        for item_data in data.items:
            self.db.add(RefundItem(
                id=uuid4(),
                refund_id=refund_id,
                sale_item_id=item_data.sale_item_id,
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                amount=item_data.amount,
            ))

        # Restore only previously deducted lines; restore also checks both current toggles.
        from services.variant_service import VariantService
        variants = VariantService(self.db, created_by=created_by)
        restore_demand = defaultdict(int)
        for item_data in data.items:
            line = sale_item_by_id[item_data.sale_item_id]
            if line.tracked_at_sale:
                restore_demand[line.variant_id] += item_data.quantity
        for variant_id in sorted(restore_demand, key=str):
            await variants.restore(tenant_id, variant_id, restore_demand[variant_id],
                                   refund.id, tracked_at_sale=True, branch_id=sale.branch_id)

        # 6. Mark sale REFUNDED when the refund covers its entire total.
        if all_units_returned and abs(prior + data.amount - sale.total) <= _TOLERANCE:
            sale.status = full_sale_status

        await self.db.flush()

        # Re-fetch with items eager-loaded for the response.
        loaded = await self.db.execute(
            select(Refund)
            .options(selectinload(Refund.items))
            .where(Refund.id == refund_id)
        )
        loaded_refund = loaded.scalar_one()
        await self.db.commit()
        return self._to_schema(loaded_refund)

    async def get(self, refund_id: UUID, tenant_id: UUID) -> RefundResponse:
        """Return a single refund by UUID, scoped to tenant via Branch → Business."""
        result = await self.db.execute(
            select(Refund)
            .join(Branch, Refund.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .options(selectinload(Refund.items))
            .where(
                Refund.id == refund_id,
                Business.tenant_id == tenant_id,
                Refund.deleted_at.is_(None),
            )
        )
        refund = result.scalar_one_or_none()
        if not refund:
            raise NotFoundError("Refund not found.")
        return self._to_schema(refund)

    async def list_for_sale(
        self, sale_id: UUID, tenant_id: UUID
    ) -> list[RefundResponse]:
        """All refunds for a sale, newest first, scoped to tenant."""
        result = await self.db.execute(
            select(Refund)
            .join(Branch, Refund.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .options(selectinload(Refund.items))
            .where(
                Refund.sale_id == sale_id,
                Business.tenant_id == tenant_id,
                Refund.deleted_at.is_(None),
            )
            .order_by(Refund.refunded_at.desc())
        )
        return [self._to_schema(r) for r in result.scalars().all()]
