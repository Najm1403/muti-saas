# api/v1/branches.py
#
# Branch management routes — tenant admin only.
# Branches sit under the tenant's Business: Tenant → Business → Branch.
# A tenant has exactly one Business, so business_id is resolved server-side
# (get_current_business_id) rather than passed by the caller.
# Prefix: /api/v1/branches

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user, get_current_business_id, require_any_module
from db.session import get_db
from schemas.branch import BranchCreate, BranchResponse, BranchStatsResponse, BranchUpdate
from schemas.common import MessageResponse
from services.branch_service import BranchService
from services.branch_stats_service import BranchStatsService

router = APIRouter(prefix="/branches", tags=["Branches"])
catalog_router = APIRouter(
    prefix="/branches",
    tags=["Branches"],
    dependencies=[Depends(require_any_module("branches", "inventory"))],
)


def _svc(db: AsyncSession = Depends(get_db)) -> BranchService:
    return BranchService(db)


def _stats_svc(db: AsyncSession = Depends(get_db)) -> BranchStatsService:
    return BranchStatsService(db)


@catalog_router.get(
    "/",
    response_model=list[BranchResponse],
    status_code=status.HTTP_200_OK,
    summary="List branches",
    description="Returns all branches for the current tenant's business.",
)
async def list_branches(
    skip: int = 0,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    business_id: UUID = Depends(get_current_business_id),
    svc: BranchService = Depends(_svc),
) -> list[BranchResponse]:
    rows = await svc.list(
        business_id=business_id,
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit,
    )
    from api.branch_access import visible_branches
    allowed = await visible_branches(svc.db, current_user)
    return rows if allowed is None else [row for row in rows if row.id in allowed]


@router.post(
    "/",
    response_model=BranchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create branch",
    description="branch_code must be unique within the business.",
)
async def create_branch(
    data: BranchCreate,
    current_user: CurrentUser = Depends(get_current_user),
    business_id: UUID = Depends(get_current_business_id),
    svc: BranchService = Depends(_svc),
) -> BranchResponse:
    return await svc.create(
        business_id=business_id,
        tenant_id=current_user.tenant_id,
        data=data,
    )


# ── Branch Stats ──────────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=list[BranchStatsResponse],
    status_code=status.HTTP_200_OK,
    summary="All branches with aggregate stats",
    description=(
        "Returns every non-deleted branch for the tenant enriched with: "
        "device counts (total/active/activated), most recent device sync time, "
        "and COMPLETED sale counts + revenue for today and the current calendar month."
    ),
)
async def list_branch_stats(
    current_user: CurrentUser = Depends(get_current_user),
    svc: BranchStatsService = Depends(_stats_svc),
) -> list[BranchStatsResponse]:
    rows = await svc.get_all(tenant_id=current_user.tenant_id)
    from api.branch_access import visible_branches
    allowed = await visible_branches(svc.db, current_user)
    return rows if allowed is None else [row for row in rows if row.id in allowed]


@router.get(
    "/{id}",
    response_model=BranchResponse,
    status_code=status.HTTP_200_OK,
    summary="Get branch",
)
async def get_branch(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: BranchService = Depends(_svc),
) -> BranchResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch(
    "/{id}",
    response_model=BranchResponse,
    status_code=status.HTTP_200_OK,
    summary="Update branch",
)
async def update_branch(
    id: UUID,
    data: BranchUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: BranchService = Depends(_svc),
) -> BranchResponse:
    return await svc.update(id=id, tenant_id=current_user.tenant_id, data=data)


@router.post(
    "/{id}/activate",
    response_model=BranchResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate branch",
)
async def activate_branch(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: BranchService = Depends(_svc),
) -> BranchResponse:
    return await svc.activate(id=id, tenant_id=current_user.tenant_id)


@router.post(
    "/{id}/deactivate",
    response_model=BranchResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate branch",
)
async def deactivate_branch(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: BranchService = Depends(_svc),
) -> BranchResponse:
    return await svc.deactivate(id=id, tenant_id=current_user.tenant_id)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete branch",
    description="Soft-deletes the branch. Devices and sales data are retained.",
)
async def delete_branch(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: BranchService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Branch deleted.")


@router.get(
    "/{id}/stats",
    response_model=BranchStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Single branch with aggregate stats",
)
async def get_branch_stats(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: BranchStatsService = Depends(_stats_svc),
) -> BranchStatsResponse:
    return await svc.get_one(branch_id=id, tenant_id=current_user.tenant_id)
