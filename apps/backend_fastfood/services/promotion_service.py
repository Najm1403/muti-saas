# services/promotion_service.py
#
# CRUD + evaluate service for promotions, scoped to a tenant.
# evaluate() checks which active promotions apply to a given cart.

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError
from models.branch import Branch
from models.branch_promotion import BranchPromotion
from models.promotion import Promotion
from schemas.branch_assignment import BranchAssignmentResponse, BranchBrief
from schemas.promotion import (
    ApplicablePromotion,
    PromotionCreate,
    PromotionEvaluateRequest,
    PromotionResponse,
    PromotionUpdate,
)


class PromotionService:
    """Manages promotions and cart evaluation scoped to a tenant."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _check_promo_code_unique(
        self, tenant_id: UUID, promo_code: str, exclude_id: UUID | None = None
    ) -> None:
        stmt = select(Promotion).where(
            Promotion.tenant_id == tenant_id,
            Promotion.promo_code == promo_code,
            Promotion.deleted_at.is_(None),
        )
        if exclude_id:
            stmt = stmt.where(Promotion.id != exclude_id)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictError(
                f"A promotion with promo code '{promo_code}' already exists."
            )

    async def create(
        self, tenant_id: UUID, data: PromotionCreate
    ) -> PromotionResponse:
        from services.ownership import catalog_references
        await catalog_references(self.db, tenant_id, data.model_dump(exclude_unset=True))
        if data.promo_code:
            await self._check_promo_code_unique(tenant_id, data.promo_code)

        promotion = Promotion(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            promo_code=data.promo_code,
            type=data.type,
            discount_value=data.discount_value,
            trigger_product_id=data.trigger_product_id,
            trigger_category_id=data.trigger_category_id,
            trigger_min_qty=data.trigger_min_qty,
            trigger_min_amount=data.trigger_min_amount,
            reward_product_id=data.reward_product_id,
            reward_category_id=data.reward_category_id,
            reward_quantity=data.reward_quantity,
            reward_discount_type=data.reward_discount_type,
            reward_discount_value=data.reward_discount_value,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            max_uses=data.max_uses,
        )
        self.db.add(promotion)
        await self.db.commit()
        await self.db.refresh(promotion)
        return PromotionResponse.model_validate(promotion)

    async def get(self, id: UUID, tenant_id: UUID) -> PromotionResponse:
        result = await self.db.execute(
            select(Promotion).where(
                Promotion.id == id,
                Promotion.tenant_id == tenant_id,
                Promotion.deleted_at.is_(None),
            )
        )
        promotion = result.scalar_one_or_none()
        if not promotion:
            raise NotFoundError("Promotion not found.")
        return PromotionResponse.model_validate(promotion)

    async def list(self, tenant_id: UUID) -> list[PromotionResponse]:
        result = await self.db.execute(
            select(Promotion)
            .where(
                Promotion.tenant_id == tenant_id,
                Promotion.deleted_at.is_(None),
            )
            .order_by(Promotion.created_at.desc())
        )
        promotions = result.scalars().all()
        return [PromotionResponse.model_validate(p) for p in promotions]

    async def update(
        self, id: UUID, tenant_id: UUID, data: PromotionUpdate
    ) -> PromotionResponse:
        from services.ownership import catalog_references
        await catalog_references(self.db, tenant_id, data.model_dump(exclude_unset=True))
        result = await self.db.execute(
            select(Promotion).where(
                Promotion.id == id,
                Promotion.tenant_id == tenant_id,
                Promotion.deleted_at.is_(None),
            )
        )
        promotion = result.scalar_one_or_none()
        if not promotion:
            raise NotFoundError("Promotion not found.")

        fields = data.model_dump(exclude_unset=True)

        if "promo_code" in fields and fields["promo_code"]:
            await self._check_promo_code_unique(
                tenant_id, fields["promo_code"], exclude_id=id
            )

        for field, value in fields.items():
            setattr(promotion, field, value)

        await self.db.commit()
        await self.db.refresh(promotion)
        return PromotionResponse.model_validate(promotion)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        result = await self.db.execute(
            select(Promotion).where(
                Promotion.id == id,
                Promotion.tenant_id == tenant_id,
                Promotion.deleted_at.is_(None),
            )
        )
        promotion = result.scalar_one_or_none()
        if not promotion:
            raise NotFoundError("Promotion not found.")
        promotion.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def evaluate(
        self, tenant_id: UUID, request: PromotionEvaluateRequest
    ) -> list[ApplicablePromotion]:
        """
        Evaluate which active promotions apply to the given cart.

        Auto-applied promotions (promo_code is None) are always considered.
        Code-gated promotions are only considered if request.promo_code matches.
        """
        now = datetime.now(timezone.utc)

        # Build query: active, non-deleted promotions for this tenant that are
        # either auto-applied or match the supplied promo code.
        stmt = select(Promotion).where(
            Promotion.tenant_id == tenant_id,
            Promotion.deleted_at.is_(None),
            Promotion.is_active.is_(True),
        )
        result = await self.db.execute(stmt)
        all_promotions: list[Promotion] = list(result.scalars().all())

        applicable: list[ApplicablePromotion] = []

        cart_product_ids = {item.product_id for item in request.items}
        cart_category_ids = {item.category_id for item in request.items if item.category_id}
        total_qty = sum(item.quantity for item in request.items)

        for promo in all_promotions:
            # Filter: code-gated promotions only apply when the code matches.
            if promo.promo_code is not None:
                if not request.promo_code or promo.promo_code != request.promo_code:
                    continue

            # Filter: validity window.
            if promo.valid_from and promo.valid_from > now:
                continue
            if promo.valid_until and promo.valid_until < now:
                continue

            # Filter: exhausted max uses.
            if promo.max_uses is not None and promo.used_count >= promo.max_uses:
                continue

            # Filter: trigger conditions.
            if promo.trigger_min_amount is not None:
                if request.order_total < promo.trigger_min_amount:
                    continue

            if promo.trigger_min_qty is not None:
                if total_qty < promo.trigger_min_qty:
                    continue

            if promo.trigger_product_id is not None:
                if promo.trigger_product_id not in cart_product_ids:
                    continue

            if promo.trigger_category_id is not None:
                if promo.trigger_category_id not in cart_category_ids:
                    continue

            # Compute discount amount.
            if promo.type == "PERCENTAGE":
                discount_amount = (
                    request.order_total * promo.discount_value / Decimal("100")
                )
                message = f"{promo.discount_value}% discount applied."
            elif promo.type == "FLAT_AMOUNT":
                discount_amount = min(promo.discount_value, request.order_total)
                message = f"Flat discount of {discount_amount} applied."
            else:
                # BXGY / FREE_ITEM — POS handles the physical reward.
                discount_amount = Decimal("0")
                qty = promo.reward_quantity or 1
                message = f"{qty} free item(s) to be added by cashier."

            applicable.append(
                ApplicablePromotion(
                    promotion_id=promo.id,
                    promotion_name=promo.name,
                    promo_code=promo.promo_code,
                    type=promo.type,
                    discount_amount=discount_amount,
                    reward_product_id=promo.reward_product_id,
                    reward_quantity=promo.reward_quantity,
                    message=message,
                )
            )

        return applicable

    # ─────────────────────────────────────────────
    # Branch assignment
    # ─────────────────────────────────────────────

    async def _get_promotion_or_404(self, promotion_id: UUID, tenant_id: UUID) -> Promotion:
        result = await self.db.execute(
            select(Promotion).where(
                Promotion.id == promotion_id,
                Promotion.tenant_id == tenant_id,
                Promotion.deleted_at.is_(None),
            )
        )
        promotion = result.scalar_one_or_none()
        if not promotion:
            raise NotFoundError("Promotion not found.")
        return promotion

    async def get_branch_assignment(
        self, promotion_id: UUID, tenant_id: UUID
    ) -> BranchAssignmentResponse:
        promo = await self._get_promotion_or_404(promotion_id, tenant_id)
        if promo.all_branches:
            return BranchAssignmentResponse(all_branches=True, branches=[])
        result = await self.db.execute(
            select(Branch)
            .join(BranchPromotion, BranchPromotion.branch_id == Branch.id)
            .where(BranchPromotion.promotion_id == promotion_id)
            .where(Branch.deleted_at.is_(None))
            .order_by(Branch.name)
        )
        branches = result.scalars().all()
        return BranchAssignmentResponse(
            all_branches=False,
            branches=[BranchBrief(id=b.id, name=b.name, branch_code=b.branch_code) for b in branches],
        )

    async def set_branch_assignment(
        self, promotion_id: UUID, tenant_id: UUID, all_branches: bool, branch_ids: list[UUID]
    ) -> BranchAssignmentResponse:
        from services.ownership import tenant_branches
        branch_ids = await tenant_branches(self.db, tenant_id, branch_ids)
        promo = await self._get_promotion_or_404(promotion_id, tenant_id)
        promo.all_branches = all_branches
        await self.db.execute(
            delete(BranchPromotion).where(BranchPromotion.promotion_id == promotion_id)
        )
        assigned: list[Branch] = []
        if not all_branches and branch_ids:
            for bid in branch_ids:
                self.db.add(BranchPromotion(branch_id=bid, promotion_id=promotion_id))
            await self.db.flush()
            result = await self.db.execute(
                select(Branch)
                .where(Branch.id.in_(branch_ids))
                .where(Branch.deleted_at.is_(None))
                .order_by(Branch.name)
            )
            assigned = list(result.scalars().all())
        await self.db.commit()
        return BranchAssignmentResponse(
            all_branches=all_branches,
            branches=[BranchBrief(id=b.id, name=b.name, branch_code=b.branch_code) for b in assigned],
        )
