# api/platform/activity.py
#
# Platform audit log — cross-tenant activity feed for super admins.
# Prefix: /api/platform/activity

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import CurrentPlatformAdmin, get_current_platform_admin
from db.session import get_db
from schemas.onboarding import ActivityLogResponse
from services.onboarding_service import OnboardingService

router = APIRouter(prefix="/activity", tags=["Platform · Activity"])


def _svc(db: AsyncSession = Depends(get_db)) -> OnboardingService:
    return OnboardingService(db)


@router.get(
    "",
    response_model=list[ActivityLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Platform activity / audit log",
    description=(
        "Returns audit log entries newest-first. "
        "Filter by tenant_id to scope to a single tenant, or by action "
        "(e.g. LOGIN, CREATE, UPDATE, DELETE). "
        "Platform admin only."
    ),
)
@router.get("/", response_model=list[ActivityLogResponse], status_code=status.HTTP_200_OK, include_in_schema=False)
async def list_activity(
    tenant_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None, description="e.g. LOGIN, CREATE, UPDATE, DELETE"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: OnboardingService = Depends(_svc),
) -> list[ActivityLogResponse]:
    return await svc.list_activity(
        tenant_id=tenant_id,
        action=action,
        skip=skip,
        limit=limit,
    )
