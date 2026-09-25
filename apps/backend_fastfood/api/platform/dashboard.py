# api/platform/dashboard.py
#
# Platform super-admin dashboard — aggregate stats across all tenants.
# Prefix: /api/platform/dashboard

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import CurrentPlatformAdmin, get_current_platform_admin
from db.session import get_db
from schemas.onboarding import DashboardStats
from services.onboarding_service import OnboardingService

router = APIRouter(prefix="/dashboard", tags=["Platform · Dashboard"])


def _svc(db: AsyncSession = Depends(get_db)) -> OnboardingService:
    return OnboardingService(db)


@router.get(
    "",
    response_model=DashboardStats,
    status_code=status.HTTP_200_OK,
    summary="Platform dashboard stats",
    description=(
        "Returns platform-wide aggregate counts: tenants (total / active / suspended), "
        "users, branches, devices, and subscription status breakdown. "
        "Platform admin only."
    ),
)
@router.get("/", response_model=DashboardStats, status_code=status.HTTP_200_OK, include_in_schema=False)
async def get_dashboard(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: OnboardingService = Depends(_svc),
) -> DashboardStats:
    return await svc.get_dashboard_stats()
