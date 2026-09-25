# api/v1/subscription.py
#
# Tenant-facing, read-only billing endpoints.
# Prefix: /api/v1/subscription
#
# Every handler derives the tenant from the caller's JWT (current_user.tenant_id)
# and never accepts a tenant_id / subscription_id from the path or query. A tenant
# can only see its own subscription and its own payment history.

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.subscription import TenantPaymentView, TenantSubscriptionView
from services.tenant_subscription_service import TenantSubscriptionService

router = APIRouter(prefix="/subscription", tags=["Tenant Subscription"])


def _svc(db: AsyncSession = Depends(get_db)) -> TenantSubscriptionService:
    return TenantSubscriptionService(db)


@router.get(
    "",
    response_model=TenantSubscriptionView,
    status_code=status.HTTP_200_OK,
    summary="Current subscription (billing summary)",
)
@router.get("/", response_model=TenantSubscriptionView, status_code=status.HTTP_200_OK, include_in_schema=False)
async def get_current_subscription(
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantSubscriptionService = Depends(_svc),
) -> TenantSubscriptionView:
    return await svc.get_current(tenant_id=current_user.tenant_id)


@router.get(
    "/payments",
    response_model=list[TenantPaymentView],
    status_code=status.HTTP_200_OK,
    summary="Payment history for the current tenant",
)
async def list_my_payments(
    skip: int = 0,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TenantSubscriptionService = Depends(_svc),
) -> list[TenantPaymentView]:
    return await svc.list_payments(tenant_id=current_user.tenant_id, skip=skip, limit=limit)
