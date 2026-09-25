# api/v1/dashboard.py
#
# Tenant dashboard stats.
# Prefix: /api/v1/dashboard

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.dashboard import TenantDashboardStats
from services.tenant_dashboard_service import TenantDashboardService

router = APIRouter(prefix="/dashboard", tags=["Tenant Dashboard"])


def _svc(db: AsyncSession = Depends(get_db)) -> TenantDashboardService:
    return TenantDashboardService(db)


@router.get("", response_model=TenantDashboardStats, status_code=status.HTTP_200_OK, summary="Tenant dashboard stats")
@router.get("/", response_model=TenantDashboardStats, status_code=status.HTTP_200_OK, include_in_schema=False)
async def get_dashboard(
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantDashboardService = Depends(_svc),
) -> TenantDashboardStats:
    return await svc.get_stats(tenant_id=current_user.tenant_id)
