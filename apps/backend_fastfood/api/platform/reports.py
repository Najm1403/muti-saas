# api/platform/reports.py
#
# Platform reporting endpoints — aggregated analytics for super admins.
# Prefix: /api/platform/reports
#
# All endpoints require a valid platform admin JWT.
# No write operations — purely read/aggregate.

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import CurrentPlatformAdmin, get_current_platform_admin
from db.session import get_db
from schemas.report import (
    ActivitySummary,
    BranchReport,
    DeviceReport,
    PlanPerformanceItem,
    PlatformSummary,
    RevenueReport,
    SubscriptionReport,
    TenantReport,
    UserReport,
)
from services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Platform · Reports"])


def _svc(db: AsyncSession = Depends(get_db)) -> ReportService:
    return ReportService(db)


# ════════════════════════════════════════════════════════════════
# GET /summary
# ════════════════════════════════════════════════════════════════

@router.get(
    "/summary",
    response_model=PlatformSummary,
    status_code=status.HTTP_200_OK,
    summary="Platform summary KPIs",
    description=(
        "Returns total tenants, users, active devices, and estimated MRR "
        "from all active/trial subscriptions. Suitable for dashboard stat cards."
    ),
)
@router.get("/summary/", response_model=PlatformSummary, status_code=status.HTTP_200_OK, include_in_schema=False)
async def get_summary(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: ReportService = Depends(_svc),
) -> PlatformSummary:
    return await svc.get_summary()


# ════════════════════════════════════════════════════════════════
# GET /tenants
# ════════════════════════════════════════════════════════════════

@router.get(
    "/tenants",
    response_model=TenantReport,
    status_code=status.HTTP_200_OK,
    summary="Tenant growth report",
    description=(
        "Counts total, new, active, suspended tenants and subscription status breakdown. "
        "Includes a monthly growth curve for the last 6 months. "
        "`days` controls the 'new this period' window."
    ),
)
@router.get("/tenants/", response_model=TenantReport, status_code=status.HTTP_200_OK, include_in_schema=False)
async def get_tenant_report(
    days: int = Query(default=30, ge=1, le=365, description="Look-back window for 'new this period'"),
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: ReportService = Depends(_svc),
) -> TenantReport:
    return await svc.get_tenant_report(days=days)


# ════════════════════════════════════════════════════════════════
# GET /subscriptions
# ════════════════════════════════════════════════════════════════

@router.get(
    "/subscriptions",
    response_model=SubscriptionReport,
    status_code=status.HTTP_200_OK,
    summary="Subscription status breakdown",
    description=(
        "Counts subscriptions by status (ACTIVE, TRIAL, EXPIRED, SUSPENDED, CANCELLED), "
        "plan-level breakdown with revenue contribution, MRR and ARR estimates."
    ),
)
@router.get("/subscriptions/", response_model=SubscriptionReport, status_code=status.HTTP_200_OK, include_in_schema=False)
async def get_subscription_report(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: ReportService = Depends(_svc),
) -> SubscriptionReport:
    return await svc.get_subscription_report()


# ════════════════════════════════════════════════════════════════
# GET /plans
# ════════════════════════════════════════════════════════════════

@router.get(
    "/plans",
    response_model=list[PlanPerformanceItem],
    status_code=status.HTTP_200_OK,
    summary="Plan performance report",
    description=(
        "For each plan: number of active/trial tenants, percentage of total tenant base, "
        "and estimated monthly revenue contribution."
    ),
)
@router.get("/plans/", response_model=list[PlanPerformanceItem], status_code=status.HTTP_200_OK, include_in_schema=False)
async def get_plan_performance(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: ReportService = Depends(_svc),
) -> list[PlanPerformanceItem]:
    return await svc.get_plan_performance()


# ════════════════════════════════════════════════════════════════
# GET /branches
# ════════════════════════════════════════════════════════════════

@router.get(
    "/branches",
    response_model=BranchReport,
    status_code=status.HTTP_200_OK,
    summary="Branch distribution report",
    description=(
        "Total active branches across the platform, broken down per tenant "
        "with each tenant's plan limit for branches."
    ),
)
@router.get("/branches/", response_model=BranchReport, status_code=status.HTTP_200_OK, include_in_schema=False)
async def get_branch_report(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: ReportService = Depends(_svc),
) -> BranchReport:
    return await svc.get_branch_report()


# ════════════════════════════════════════════════════════════════
# GET /devices
# ════════════════════════════════════════════════════════════════

@router.get(
    "/devices",
    response_model=DeviceReport,
    status_code=status.HTTP_200_OK,
    summary="Device health report",
    description=(
        "Platform-wide device counts: total, activated, never-activated, online "
        "(synced within 2 hours), offline, disabled. Per-tenant breakdown included."
    ),
)
@router.get("/devices/", response_model=DeviceReport, status_code=status.HTTP_200_OK, include_in_schema=False)
async def get_device_report(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: ReportService = Depends(_svc),
) -> DeviceReport:
    return await svc.get_device_report()


# ════════════════════════════════════════════════════════════════
# GET /users
# ════════════════════════════════════════════════════════════════

@router.get(
    "/users",
    response_model=UserReport,
    status_code=status.HTTP_200_OK,
    summary="User distribution report",
    description=(
        "Platform-wide user counts: total, active, disabled, "
        "role breakdown (owners/managers/staff), and per-tenant breakdown."
    ),
)
@router.get("/users/", response_model=UserReport, status_code=status.HTTP_200_OK, include_in_schema=False)
async def get_user_report(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: ReportService = Depends(_svc),
) -> UserReport:
    return await svc.get_user_report()


# ════════════════════════════════════════════════════════════════
# GET /activity
# ════════════════════════════════════════════════════════════════

@router.get(
    "/activity",
    response_model=ActivitySummary,
    status_code=status.HTTP_200_OK,
    summary="Activity summary report",
    description=(
        "Counts key events in the given look-back window: "
        "tenant creations, device registrations, branch creations, user creations, "
        "logins, and failed login attempts."
    ),
)
@router.get("/activity/", response_model=ActivitySummary, status_code=status.HTTP_200_OK, include_in_schema=False)
async def get_activity_report(
    days: int = Query(default=30, ge=1, le=365, description="Look-back window in days"),
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: ReportService = Depends(_svc),
) -> ActivitySummary:
    return await svc.get_activity_report(days=days)


# ════════════════════════════════════════════════════════════════
# GET /revenue
# ════════════════════════════════════════════════════════════════

@router.get(
    "/revenue",
    response_model=RevenueReport,
    status_code=status.HTTP_200_OK,
    summary="Revenue report",
    description=(
        "This month vs last month payment totals with growth percentage. "
        "Revenue broken down by plan. Monthly trend for the last 6 months."
    ),
)
@router.get("/revenue/", response_model=RevenueReport, status_code=status.HTTP_200_OK, include_in_schema=False)
async def get_revenue_report(
    days: int = Query(default=30, ge=1, le=365, description="Look-back window (informational; month boundaries are fixed)"),
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: ReportService = Depends(_svc),
) -> RevenueReport:
    return await svc.get_revenue_report(days=days)
