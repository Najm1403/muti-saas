# api/platform/plans.py
#
# Plan management routes — platform admin only.
# Prefix: /api/platform/plans

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import CurrentPlatformAdmin, get_current_platform_admin, require_super
from db.session import get_db
from schemas.common import MessageResponse
from schemas.plan import PlanCreate, PlanResponse, PlanUpdate
from services.plan_service import PlanService

router = APIRouter(prefix="/plans", tags=["Platform · Plans"])


def _svc(db: AsyncSession = Depends(get_db)) -> PlanService:
    return PlanService(db)


@router.get("", response_model=list[PlanResponse], status_code=status.HTTP_200_OK, summary="List plans")
@router.get("/", response_model=list[PlanResponse], status_code=status.HTTP_200_OK, include_in_schema=False)
async def list_plans(
    include_inactive: bool = False,
    skip: int = 0,
    limit: int = 50,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlanService = Depends(_svc),
) -> list[PlanResponse]:
    return await svc.list(include_inactive=include_inactive, skip=skip, limit=limit)


@router.post(
    "/",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create plan",
    description="Super admin only.",
)
async def create_plan(
    data: PlanCreate,
    _: CurrentPlatformAdmin = Depends(require_super),
    svc: PlanService = Depends(_svc),
) -> PlanResponse:
    return await svc.create(data)


@router.get(
    "/{id}",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Get plan",
)
async def get_plan(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlanService = Depends(_svc),
) -> PlanResponse:
    return await svc.get(id)


@router.patch(
    "/{id}",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Update plan",
    description="Super admin only.",
)
async def update_plan(
    id: UUID,
    data: PlanUpdate,
    _: CurrentPlatformAdmin = Depends(require_super),
    svc: PlanService = Depends(_svc),
) -> PlanResponse:
    return await svc.update(id, data)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete plan",
    description="Soft-deletes the plan. Existing subscriptions are unaffected. Super admin only.",
)
async def delete_plan(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(require_super),
    svc: PlanService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id)
    return MessageResponse(message="Plan deleted.")
