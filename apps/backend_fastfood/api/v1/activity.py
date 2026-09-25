# api/v1/activity.py
#
# Tenant-scoped activity log — read-only audit log viewer.
# Prefix: /api/v1/activity

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.activity import ActivityLogResponse
from services.activity_service import ActivityService

router = APIRouter(prefix="/activity", tags=["Activity"])


def _svc(db: AsyncSession = Depends(get_db)) -> ActivityService:
    return ActivityService(db)


@router.get(
    "",
    response_model=list[ActivityLogResponse],
    status_code=status.HTTP_200_OK,
    summary="List activity logs",
    description=(
        "Returns audit log entries for this tenant, newest first. "
        "Filter by user_id, action (CREATE/UPDATE/DELETE/LOGIN/LOGOUT), or module "
        "(sales/products/users/roles/branches/devices/categories/settings). "
        "Max 200 per request."
    ),
)
@router.get("/", response_model=list[ActivityLogResponse], status_code=status.HTTP_200_OK, include_in_schema=False)
async def list_activity(
    user_id: UUID | None = Query(None, description="Filter by user"),
    action: str | None = Query(None, description="CREATE / UPDATE / DELETE / LOGIN / LOGOUT"),
    module: str | None = Query(None, description="Module name, e.g. 'sales'"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    svc: ActivityService = Depends(_svc),
) -> list[ActivityLogResponse]:
    return await svc.list(
        tenant_id=current_user.tenant_id,
        user_id=user_id,
        action=action,
        module=module,
        skip=skip,
        limit=limit,
    )
