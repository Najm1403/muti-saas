# api/v1/deals.py
#
# Deal bundle management routes — tenant scoped.
#
# A deal groups products or categories into a bundle priced via a fixed price
# or a discount. Items within the deal can be marked as free.
#
# Connected services / dependencies:
#   - services/deal_service.py  — DealService
#   - api/dependencies.py       — get_current_user
#   - db/session.py             — get_db
#   - schemas/deal.py           — DealCreate, DealUpdate, DealResponse,
#                                  DealItemCreate, DealItemUpdate, DealItemResponse
#   - schemas/common.py         — MessageResponse
#
# Prefix: /api/v1/deals

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.branch_assignment import BranchAssignmentResponse, BranchAssignmentUpdate
from schemas.common import MessageResponse
from schemas.deal import (
    DealCreate,
    DealItemCreate,
    DealItemResponse,
    DealItemUpdate,
    DealResponse,
    DealUpdate,
)
from services.deal_service import DealService

router = APIRouter(prefix="/deals", tags=["Deals"])


def _svc(db: AsyncSession = Depends(get_db)) -> DealService:
    """Dependency that instantiates DealService with the request's DB session."""
    return DealService(db)


@router.get(
    "/",
    response_model=list[DealResponse],
    status_code=status.HTTP_200_OK,
    summary="List deals",
    description=(
        "Returns all deals for the current tenant ordered by display_order then name. "
        "Each deal includes its bundle items."
    ),
)
async def list_deals(
    current_user: CurrentUser = Depends(get_current_user),
    svc: DealService = Depends(_svc),
) -> list[DealResponse]:
    return await svc.list(tenant_id=current_user.tenant_id)


@router.post(
    "/",
    response_model=DealResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create deal",
    description=(
        "Creates a new deal bundle. deal_code must be unique within the tenant. "
        "Items are added separately via POST /{id}/items."
    ),
)
async def create_deal(
    data: DealCreate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DealService = Depends(_svc),
) -> DealResponse:
    return await svc.create(tenant_id=current_user.tenant_id, data=data)


@router.get(
    "/{id}/branches",
    response_model=BranchAssignmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get deal branch assignment",
)
async def get_deal_branches(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DealService = Depends(_svc),
) -> BranchAssignmentResponse:
    return await svc.get_branch_assignment(deal_id=id, tenant_id=current_user.tenant_id)


@router.put(
    "/{id}/branches",
    response_model=BranchAssignmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Set deal branch assignment",
)
async def set_deal_branches(
    id: UUID,
    data: BranchAssignmentUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DealService = Depends(_svc),
) -> BranchAssignmentResponse:
    return await svc.set_branch_assignment(
        deal_id=id,
        tenant_id=current_user.tenant_id,
        all_branches=data.all_branches,
        branch_ids=data.branch_ids,
    )


@router.get(
    "/{id}",
    response_model=DealResponse,
    status_code=status.HTTP_200_OK,
    summary="Get deal",
    description="Returns the deal including its bundle items.",
)
async def get_deal(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DealService = Depends(_svc),
) -> DealResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch(
    "/{id}",
    response_model=DealResponse,
    status_code=status.HTTP_200_OK,
    summary="Update deal",
    description="Partially update a deal. Only provided fields are changed.",
)
async def update_deal(
    id: UUID,
    data: DealUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DealService = Depends(_svc),
) -> DealResponse:
    return await svc.update(id=id, tenant_id=current_user.tenant_id, data=data)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete deal",
    description="Soft-deletes the deal.",
)
async def delete_deal(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DealService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Deal deleted.")


# ─────────────────────────────────────────────
# Deal item sub-routes
# ─────────────────────────────────────────────

@router.post(
    "/{id}/items",
    response_model=DealItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to deal",
    description=(
        "Adds a product or category slot to the deal bundle. "
        "Requires product_id or category_id."
    ),
)
async def add_deal_item(
    id: UUID,
    data: DealItemCreate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DealService = Depends(_svc),
) -> DealItemResponse:
    return await svc.add_item(
        deal_id=id,
        tenant_id=current_user.tenant_id,
        data=data,
    )


@router.patch(
    "/{id}/items/{item_id}",
    response_model=DealItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update deal item",
    description="Partially update a deal bundle item. Only provided fields are changed.",
)
async def update_deal_item(
    id: UUID,
    item_id: UUID,
    data: DealItemUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DealService = Depends(_svc),
) -> DealItemResponse:
    return await svc.update_item(
        deal_id=id,
        item_id=item_id,
        tenant_id=current_user.tenant_id,
        data=data,
    )


@router.delete(
    "/{id}/items/{item_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove item from deal",
    description="Soft-deletes a deal bundle item.",
)
async def remove_deal_item(
    id: UUID,
    item_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: DealService = Depends(_svc),
) -> MessageResponse:
    await svc.remove_item(
        deal_id=id,
        item_id=item_id,
        tenant_id=current_user.tenant_id,
    )
    return MessageResponse(message="Deal item removed.")
