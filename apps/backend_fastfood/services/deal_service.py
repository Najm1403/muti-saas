# services/deal_service.py
#
# CRUD service for deals and their bundle items, scoped to a tenant.
# Deals are always loaded with their items relationship eagerly.

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError
from models.branch import Branch
from models.branch_deal import BranchDeal
from models.deal import Deal
from models.deal_item import DealItem
from schemas.branch_assignment import BranchAssignmentResponse, BranchBrief
from schemas.deal import (
    DealCreate,
    DealItemCreate,
    DealItemResponse,
    DealItemUpdate,
    DealResponse,
    DealUpdate,
)


class DealService:
    """Manages deal bundles and their items scoped to a tenant."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_deal_or_404(self, deal_id: UUID, tenant_id: UUID) -> Deal:
        """Load a deal with its non-deleted items or raise NotFoundError."""
        result = await self.db.execute(
            select(Deal)
            .options(selectinload(Deal.items))
            .options(with_loader_criteria(DealItem, DealItem.deleted_at.is_(None)))
            .where(
                Deal.id == deal_id,
                Deal.tenant_id == tenant_id,
                Deal.deleted_at.is_(None),
            )
        )
        deal = result.scalar_one_or_none()
        if not deal:
            raise NotFoundError("Deal not found.")
        return deal

    async def create(
        self, tenant_id: UUID, data: DealCreate
    ) -> DealResponse:
        # Enforce deal_code uniqueness within the tenant.
        existing = await self.db.execute(
            select(Deal).where(
                Deal.tenant_id == tenant_id,
                Deal.deal_code == data.deal_code,
                Deal.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError(
                f"A deal with code '{data.deal_code}' already exists."
            )

        deal = Deal(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            deal_code=data.deal_code,
            image_path=data.image_path,
            fixed_price=data.fixed_price,
            discount_value=data.discount_value,
            discount_type=data.discount_type,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            display_order=data.display_order,
        )
        self.db.add(deal)
        await self.db.commit()
        await self.db.refresh(deal)
        # Reload with items relationship.
        return DealResponse.model_validate(await self._get_deal_or_404(deal.id, tenant_id))

    async def get(self, id: UUID, tenant_id: UUID) -> DealResponse:
        deal = await self._get_deal_or_404(id, tenant_id)
        return DealResponse.model_validate(deal)

    async def list(self, tenant_id: UUID) -> list[DealResponse]:
        result = await self.db.execute(
            select(Deal)
            .options(selectinload(Deal.items))
            .where(
                Deal.tenant_id == tenant_id,
                Deal.deleted_at.is_(None),
            )
            .order_by(Deal.display_order, Deal.name)
        )
        deals = result.scalars().all()
        return [DealResponse.model_validate(d) for d in deals]

    async def update(
        self, id: UUID, tenant_id: UUID, data: DealUpdate
    ) -> DealResponse:
        deal = await self._get_deal_or_404(id, tenant_id)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(deal, field, value)

        await self.db.commit()
        await self.db.refresh(deal)
        return DealResponse.model_validate(await self._get_deal_or_404(id, tenant_id))

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        deal = await self._get_deal_or_404(id, tenant_id)
        deal.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    # ─────────────────────────────────────────────
    # Deal items
    # ─────────────────────────────────────────────

    async def add_item(
        self, deal_id: UUID, tenant_id: UUID, data: DealItemCreate
    ) -> DealItemResponse:
        from services.ownership import catalog_references
        await catalog_references(self.db, tenant_id, data.model_dump(exclude_unset=True))
        # Verify deal exists and belongs to tenant.
        await self._get_deal_or_404(deal_id, tenant_id)

        item = DealItem(
            deal_id=deal_id,
            product_id=data.product_id,
            category_id=data.category_id,
            quantity=data.quantity,
            is_free=data.is_free,
            sort_order=data.sort_order,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return DealItemResponse.model_validate(item)

    async def update_item(
        self,
        deal_id: UUID,
        item_id: UUID,
        tenant_id: UUID,
        data: DealItemUpdate,
    ) -> DealItemResponse:
        from services.ownership import catalog_references
        await catalog_references(self.db, tenant_id, data.model_dump(exclude_unset=True))
        # Verify deal belongs to tenant.
        await self._get_deal_or_404(deal_id, tenant_id)

        result = await self.db.execute(
            select(DealItem).where(
                DealItem.id == item_id,
                DealItem.deal_id == deal_id,
                DealItem.deleted_at.is_(None),
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise NotFoundError("Deal item not found.")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)

        await self.db.commit()
        await self.db.refresh(item)
        return DealItemResponse.model_validate(item)

    async def remove_item(
        self, deal_id: UUID, item_id: UUID, tenant_id: UUID
    ) -> None:
        # Verify deal belongs to tenant.
        await self._get_deal_or_404(deal_id, tenant_id)

        result = await self.db.execute(
            select(DealItem).where(
                DealItem.id == item_id,
                DealItem.deal_id == deal_id,
                DealItem.deleted_at.is_(None),
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise NotFoundError("Deal item not found.")

        item.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    # ─────────────────────────────────────────────
    # Branch assignment
    # ─────────────────────────────────────────────

    async def get_branch_assignment(
        self, deal_id: UUID, tenant_id: UUID
    ) -> BranchAssignmentResponse:
        deal = await self._get_deal_or_404(deal_id, tenant_id)
        if deal.all_branches:
            return BranchAssignmentResponse(all_branches=True, branches=[])
        result = await self.db.execute(
            select(Branch)
            .join(BranchDeal, BranchDeal.branch_id == Branch.id)
            .where(BranchDeal.deal_id == deal_id)
            .where(Branch.deleted_at.is_(None))
            .order_by(Branch.name)
        )
        branches = result.scalars().all()
        return BranchAssignmentResponse(
            all_branches=False,
            branches=[BranchBrief(id=b.id, name=b.name, branch_code=b.branch_code) for b in branches],
        )

    async def set_branch_assignment(
        self, deal_id: UUID, tenant_id: UUID, all_branches: bool, branch_ids: list[UUID]
    ) -> BranchAssignmentResponse:
        from services.ownership import tenant_branches
        branch_ids = await tenant_branches(self.db, tenant_id, branch_ids)
        deal = await self._get_deal_or_404(deal_id, tenant_id)
        deal.all_branches = all_branches
        await self.db.execute(
            delete(BranchDeal).where(BranchDeal.deal_id == deal_id)
        )
        assigned: list[Branch] = []
        if not all_branches and branch_ids:
            for bid in branch_ids:
                self.db.add(BranchDeal(branch_id=bid, deal_id=deal_id))
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
