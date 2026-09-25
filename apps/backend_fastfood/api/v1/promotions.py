# api/v1/promotions.py
#
# Promotion management and cart evaluation routes — tenant scoped.
#
# Promotions support four types: PERCENTAGE, FLAT_AMOUNT, BXGY, FREE_ITEM.
# The /evaluate endpoint accepts a cart payload and returns all applicable
# promotions, including auto-applied ones.
#
# IMPORTANT: /evaluate is registered before /{id} so FastAPI does not
# interpret the literal string "evaluate" as a UUID path parameter.
#
# Connected services / dependencies:
#   - services/promotion_service.py  — PromotionService
#   - api/dependencies.py            — get_current_user
#   - db/session.py                  — get_db
#   - schemas/promotion.py           — PromotionCreate, PromotionUpdate, PromotionResponse,
#                                      PromotionEvaluateRequest, ApplicablePromotion
#   - schemas/common.py              — MessageResponse
#
# Prefix: /api/v1/promotions

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.branch_assignment import BranchAssignmentResponse, BranchAssignmentUpdate
from schemas.common import MessageResponse
from schemas.promotion import (
    ApplicablePromotion,
    PromotionCreate,
    PromotionEvaluateRequest,
    PromotionResponse,
    PromotionUpdate,
)
from services.promotion_service import PromotionService

router = APIRouter(prefix="/promotions", tags=["Promotions"])


def _svc(db: AsyncSession = Depends(get_db)) -> PromotionService:
    """Dependency that instantiates PromotionService with the request's DB session."""
    return PromotionService(db)


@router.get(
    "/",
    response_model=list[PromotionResponse],
    status_code=status.HTTP_200_OK,
    summary="List promotions",
    description="Returns all promotions for the current tenant, ordered by creation date (newest first).",
)
async def list_promotions(
    current_user: CurrentUser = Depends(get_current_user),
    svc: PromotionService = Depends(_svc),
) -> list[PromotionResponse]:
    return await svc.list(tenant_id=current_user.tenant_id)


@router.post(
    "/",
    response_model=PromotionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create promotion",
    description=(
        "Creates a new promotion. "
        "BXGY and FREE_ITEM types require reward_product_id or reward_category_id. "
        "promo_code must be unique within the tenant."
    ),
)
async def create_promotion(
    data: PromotionCreate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PromotionService = Depends(_svc),
) -> PromotionResponse:
    return await svc.create(tenant_id=current_user.tenant_id, data=data)


# /evaluate MUST be registered before /{id} to avoid route collision.
@router.post(
    "/evaluate",
    response_model=list[ApplicablePromotion],
    status_code=status.HTTP_200_OK,
    summary="Evaluate promotions for a cart",
    description=(
        "Evaluates all active promotions against the submitted cart. "
        "Returns a list of applicable promotions with their computed discount amounts. "
        "Auto-applied promotions are always checked; code-gated promotions are only "
        "checked when a matching promo_code is supplied."
    ),
)
async def evaluate_promotions(
    data: PromotionEvaluateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PromotionService = Depends(_svc),
) -> list[ApplicablePromotion]:
    return await svc.evaluate(tenant_id=current_user.tenant_id, request=data)


@router.get(
    "/{id}/branches",
    response_model=BranchAssignmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get promotion branch assignment",
)
async def get_promotion_branches(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PromotionService = Depends(_svc),
) -> BranchAssignmentResponse:
    return await svc.get_branch_assignment(promotion_id=id, tenant_id=current_user.tenant_id)


@router.put(
    "/{id}/branches",
    response_model=BranchAssignmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Set promotion branch assignment",
)
async def set_promotion_branches(
    id: UUID,
    data: BranchAssignmentUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PromotionService = Depends(_svc),
) -> BranchAssignmentResponse:
    return await svc.set_branch_assignment(
        promotion_id=id,
        tenant_id=current_user.tenant_id,
        all_branches=data.all_branches,
        branch_ids=data.branch_ids,
    )


@router.get(
    "/{id}",
    response_model=PromotionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get promotion",
)
async def get_promotion(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PromotionService = Depends(_svc),
) -> PromotionResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch(
    "/{id}",
    response_model=PromotionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update promotion",
    description="Partially update a promotion. Only provided fields are changed.",
)
async def update_promotion(
    id: UUID,
    data: PromotionUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PromotionService = Depends(_svc),
) -> PromotionResponse:
    return await svc.update(id=id, tenant_id=current_user.tenant_id, data=data)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete promotion",
    description="Soft-deletes the promotion.",
)
async def delete_promotion(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PromotionService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Promotion deleted.")
