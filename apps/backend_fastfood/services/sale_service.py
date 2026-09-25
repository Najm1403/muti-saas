# services/sale_service.py
#
# Core POS transaction service — the heart of the fastfood backend.
#
# Hierarchy enforced:
#   Tenant → Business → Branch → Device → Sale → SaleItems → SaleItemOptions
#
# Full flow:
#   1. Client (Android tablet or web) submits SaleCreate.
#   2. Service verifies ownership of branch, device, and cashier user.
#   3. Service validates that submitted totals are arithmetically correct.
#   4. Repository atomically inserts Sale → SaleItems → SaleItemOptions.
#   5. Service re-fetches the sale with eager loading and returns SaleResponse.
#   Payments are submitted separately via POST /payments after the sale is created.
#
# Dependencies:
#   - repositories/sale_repository.py    — atomic create, list, get, status update
#   - repositories/branch_repository.py  — verifies branch belongs to tenant
#   - repositories/device_repository.py  — verifies device belongs to branch+tenant
#   - repositories/user_repository.py    — verifies cashier belongs to tenant
#   - schemas/sale.py                    — SaleCreate, SaleResponse, SaleListResponse
#   - core/exceptions.py                 — NotFoundError, ValidationError

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.sale import Sale

from core.exceptions import NotFoundError, ValidationError
from repositories.branch_repository import BranchRepository
from repositories.device_repository import DeviceRepository
from repositories.sale_repository import SaleRepository
from repositories.user_repository import UserRepository
from schemas.sale import SaleCreate, SaleListResponse, SaleResponse, SaleStatusUpdate

# One-cent tolerance for rounding differences between device and server.
_TOLERANCE = Decimal("0.01")

# Status values the client is allowed to set via the status-update endpoint.
_ALLOWED_STATUSES = {"COMPLETED", "CANCELLED", "REFUNDED"}


class SaleService:
    """
    Processes POS sales transactions end-to-end.

    Every ownership check uses tenant_id from the caller's JWT so cross-tenant
    access is impossible even if the caller knows another tenant's UUIDs.

    Offline-first support:
        The Android app may generate UUIDs locally (sale.id, item.id, option.id).
        These are passed through to the repository which preserves them.
        If a UUID is omitted the repository generates one (uuid4).
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SaleRepository(db)
        self.branch_repo = BranchRepository(db)
        self.device_repo = DeviceRepository(db)
        self.user_repo = UserRepository(db)

    # ── private validation helpers ───────────────────────────────────────

    async def _verify_branch(self, branch_id: UUID, tenant_id: UUID) -> None:
        """Raise NotFoundError if branch does not belong to tenant."""
        if not await self.branch_repo.get_by_id(branch_id, tenant_id):
            raise NotFoundError("Branch not found.")

    async def _verify_device(
        self, device_id: UUID, branch_id: UUID, tenant_id: UUID
    ) -> None:
        """
        Raise NotFoundError if device is unknown to this tenant.
        Raise ValidationError if device is deactivated or belongs to a different branch.
        A deactivated terminal should not be recording new sales.
        """
        device = await self.device_repo.get_by_id(device_id, tenant_id)
        if not device:
            raise NotFoundError("Device not found.")
        if device.branch_id != branch_id:
            raise NotFoundError("Device does not belong to the specified branch.")
        from models.device import assert_operational
        assert_operational(device)
        if not device.is_active:
            raise ValidationError("Device is deactivated and cannot record sales.")

    async def _verify_user(self, user_id: UUID, tenant_id: UUID) -> None:
        """
        Raise NotFoundError if cashier does not belong to this tenant.
        Raise ValidationError if the account is deactivated.
        """
        user = await self.user_repo.get_by_id(user_id, tenant_id)
        if not user:
            raise NotFoundError("User (cashier) not found.")
        if not user.is_active:
            raise ValidationError("User account is deactivated.")

    @staticmethod
    def _validate_totals(data: SaleCreate) -> None:
        """
        Re-compute totals from first principles and compare to submitted values.

        Item level:  item.total ≈ (item.unit_price × item.quantity) − item.discount
        Sale level:  sale.subtotal ≈ Σ item.total
                     sale.total    ≈ sale.subtotal − sale.discount

        Variant Options carry no price (spec A1) — unit_price already reflects
        the selected Variant's sale_price. Allows _TOLERANCE (0.01) for
        one-cent rounding differences.
        """
        computed_subtotal = Decimal("0.00")
        for item in data.items:
            expected = (item.unit_price * item.quantity) - item.discount
            if abs(item.total - expected) > _TOLERANCE:
                raise ValidationError(
                    f"Item '{item.product_name}' total mismatch: "
                    f"submitted {item.total}, expected ≈ {expected}."
                )
            computed_subtotal += item.total

        if abs(data.subtotal - computed_subtotal) > _TOLERANCE:
            raise ValidationError(
                f"Sale subtotal mismatch: submitted {data.subtotal}, "
                f"computed from items {computed_subtotal}."
            )
        expected_total = data.subtotal - data.discount + data.tax_amount
        if abs(data.total - expected_total) > _TOLERANCE:
            raise ValidationError(
                f"Sale total mismatch: submitted {data.total}, "
                f"expected subtotal − discount + tax = {expected_total}."
            )

    # ── public interface ─────────────────────────────────────────────────

    async def create(self, data: SaleCreate, tenant_id: UUID) -> SaleResponse:
        """
        Record a complete POS sale transaction.

        Steps:
            1. Verify branch → tenant ownership.
            2. Verify device → branch → tenant ownership and active status.
            3. Verify cashier user → tenant membership and active status.
            4. Validate all totals arithmetically.
            5. Atomically insert Sale + SaleItems + SaleItemOptions.
            6. Re-fetch with selectinload (items + options) and return SaleResponse.

        Payment is submitted separately via POST /api/v1/payments after this call.
        """
        await self._verify_branch(data.branch_id, tenant_id)
        await self._verify_device(data.device_id, data.branch_id, tenant_id)
        await self._verify_user(data.user_id, tenant_id)
        self._validate_totals(data)

        from services.checkout_validation import validate_catalog
        await validate_catalog(self.db, data, tenant_id, data.branch_id)
        # Generic management API settles through PaymentService, so start unpaid.
        data = data.model_copy(update={"status": "PENDING"})
        from services.variant_service import VariantService
        variants = VariantService(self.db, created_by=data.user_id)
        await variants.validate_variant_selection(tenant_id, data.items)
        await variants.validate_stock(
            tenant_id, [(item.variant_id, item.quantity) for item in data.items], branch_id=data.branch_id
        )
        sale = await self.repo.create(data)
        await variants.deduct(tenant_id,
            [(i.variant_id, int(i.quantity), i.id, []) for i in sale.items], sale.id, branch_id=data.branch_id)
        sale.variant_inventory_reserved = True
        await self.db.commit()

        # Re-fetch with eager loading so items + options are present on the response.
        loaded = await self.repo.get_by_id(sale.id, tenant_id)
        if not loaded:
            raise NotFoundError("Sale could not be retrieved after creation.")
        return SaleResponse.model_validate(loaded)

    async def get(self, id: UUID, tenant_id: UUID) -> SaleResponse:
        """
        Return a fully nested sale (with items and options) by UUID.

        Raises NotFoundError if the sale belongs to a different tenant or is deleted.
        """
        sale = await self.repo.get_by_id(id, tenant_id)
        if not sale:
            raise NotFoundError("Sale not found.")
        return SaleResponse.model_validate(sale)

    async def list(
        self,
        branch_id: UUID,
        tenant_id: UUID,
        date_from=None,
        date_to=None,
        status: str | None = None,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[SaleListResponse]:
        """
        Return a paginated list of sales for a branch, ordered newest first.

        Returns lightweight SaleListResponse (no nested items) for performance.
        Use get() for the full detail of a single sale.
        """
        await self._verify_branch(branch_id, tenant_id)
        sales = await self.repo.list(
            branch_id=branch_id,
            tenant_id=tenant_id,
            date_from=date_from,
            date_to=date_to,
            status=status,
            user_id=user_id,
            session_id=session_id,
            skip=skip,
            limit=limit,
        )
        return [SaleListResponse.model_validate(s) for s in sales]

    async def update_status(
        self, id: UUID, tenant_id: UUID, data: SaleStatusUpdate
    ) -> SaleResponse:
        """
        Transition an unpaid pending sale to CANCELLED.

        Only values in _ALLOWED_STATUSES are accepted to prevent arbitrary
        strings from entering the database.
        """
        if data.status not in _ALLOWED_STATUSES:
            raise ValidationError(
                f"Invalid status '{data.status}'. "
                f"Allowed: {', '.join(sorted(_ALLOWED_STATUSES))}."
            )
        await self.db.execute(select(Sale.id).where(Sale.id == id).with_for_update())
        existing = await self.repo.get_by_id(id, tenant_id)
        if not existing: raise NotFoundError("Sale not found.")
        if data.status != existing.status and (existing.status != "PENDING" or data.status != "CANCELLED"):
            raise ValidationError("Paid sales must use the refund workflow; completion requires settlement.")
        if existing.status == "PENDING" and data.status == "CANCELLED":
            await self._release_stock(existing, tenant_id)
        sale = await self.repo.update_status(id, tenant_id, data.status)
        if not sale:
            raise NotFoundError("Sale not found.")
        await self.db.commit()
        return SaleResponse.model_validate(sale)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        """
        Soft-delete a sale (sets deleted_at).

        Linked payments and refund records are retained for accounting.
        The sale stops appearing in list results once deleted.
        """
        await self.db.execute(select(Sale.id).where(Sale.id == id).with_for_update())
        existing = await self.repo.get_by_id(id, tenant_id)
        if existing and (existing.status != "PENDING" or existing.payments):
            raise ValidationError("Financial records cannot be deleted; use the refund workflow.")
        if existing:
            await self._release_stock(existing, tenant_id)
        if not await self.repo.soft_delete(id, tenant_id):
            raise NotFoundError("Sale not found.")
        await self.db.commit()

    async def _release_stock(self, sale, tenant_id):
        from services.variant_service import VariantService
        from models.stock_adjustment import StockAdjustment
        # Old pending orders did not reserve stock; only release recorded SKU deductions.
        movements = (await self.db.scalars(select(StockAdjustment).where(
            StockAdjustment.reference_id == sale.id, StockAdjustment.adjustment_type == "sale"))).all()
        service = VariantService(self.db)
        for movement in sorted(movements, key=lambda row: str(row.variant_id)):
            await service.restore(tenant_id, movement.variant_id, -movement.quantity_change, sale.id, tracked_at_sale=True, branch_id=sale.branch_id)
