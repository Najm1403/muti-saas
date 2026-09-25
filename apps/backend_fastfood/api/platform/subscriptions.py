# api/platform/subscriptions.py
#
# Subscription management — assign plans to tenants, record payments, manage lifecycle.
# Prefix: /api/platform/subscriptions

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import CurrentPlatformAdmin, get_current_platform_admin, require_super
from db.session import get_db
from models.subscription import SubscriptionStatus
from schemas.subscription import (
    BillingPreviewResponse,
    PaymentResponse,
    RecordPaymentRequest,
    SubscriptionCreate,
    SubscriptionExtendGraceRequest,
    SubscriptionExtendTrialRequest,
    SubscriptionResponse,
    SubscriptionUpdate,
    SubscriptionWaiveRequest,
)
from services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Platform · Subscriptions"])


def _svc(db: AsyncSession = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)


# ----------------------------------------------------------------
# LIST
# ----------------------------------------------------------------

@router.get("", response_model=list[SubscriptionResponse], status_code=status.HTTP_200_OK, summary="List subscriptions", description="Filter by status or tenant_id.")
@router.get("/", response_model=list[SubscriptionResponse], status_code=status.HTTP_200_OK, include_in_schema=False)
async def list_subscriptions(
    status_filter: SubscriptionStatus | None = Query(default=None, alias="status"),
    tenant_id: UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: SubscriptionService = Depends(_svc),
) -> list[SubscriptionResponse]:
    return await svc.list(status=status_filter, tenant_id=tenant_id, skip=skip, limit=limit)


# ----------------------------------------------------------------
# CREATE — assign plan to tenant
# ----------------------------------------------------------------

@router.post(
    "/",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign plan to tenant",
    description="Creates a new subscription. A tenant can only have one active/trial subscription.",
)
async def create_subscription(
    data: SubscriptionCreate,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: SubscriptionService = Depends(_svc),
) -> SubscriptionResponse:
    return await svc.create(data)


# ----------------------------------------------------------------
# GET
# ----------------------------------------------------------------

@router.get(
    "/{id}",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get subscription",
)
async def get_subscription(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: SubscriptionService = Depends(_svc),
) -> SubscriptionResponse:
    return await svc.get(id)


@router.patch(
    "/{id}",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update subscription",
    description="Currently updates the per-tenant discount percentage (0–100).",
)
async def update_subscription(
    id: UUID,
    data: SubscriptionUpdate,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: SubscriptionService = Depends(_svc),
) -> SubscriptionResponse:
    return await svc.update(id, data)


@router.get(
    "/{id}/billing-preview",
    response_model=BillingPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Billing preview",
    description=(
        "Returns the list price, effective discount %, discount amount and net price "
        "for this subscription's plan and billing cycle. Use it to pre-fill the "
        "record-payment amount."
    ),
)
async def get_billing_preview(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: SubscriptionService = Depends(_svc),
) -> BillingPreviewResponse:
    return await svc.get_billing_preview(id)


# ----------------------------------------------------------------
# TRIAL EXTENSION — super admin only
# ----------------------------------------------------------------

@router.post(
    "/{id}/extend-trial",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extend trial period",
    description=(
        "Adds the given number of days to the subscription's trial end and "
        "expiry dates. Super admin only. Only valid while status is TRIAL."
    ),
)
async def extend_trial(
    id: UUID,
    data: SubscriptionExtendTrialRequest,
    _: CurrentPlatformAdmin = Depends(require_super),
    svc: SubscriptionService = Depends(_svc),
) -> SubscriptionResponse:
    return await svc.extend_trial(id, data)


# ----------------------------------------------------------------
# LIFECYCLE
# ----------------------------------------------------------------

@router.post(
    "/{id}/suspend",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Suspend subscription",
    description="Blocks the tenant's access. Reversible via /reactivate.",
)
async def suspend_subscription(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: SubscriptionService = Depends(_svc),
) -> SubscriptionResponse:
    return await svc.suspend(id)


@router.post(
    "/{id}/reactivate",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Reactivate subscription",
)
async def reactivate_subscription(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: SubscriptionService = Depends(_svc),
) -> SubscriptionResponse:
    return await svc.reactivate(id)


@router.post(
    "/{id}/extend-grace",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extend grace period",
    description=(
        "Adds days to this subscription's grace period — the window after "
        "expires_at during which status shows PAST_DUE (a warning only; "
        "access is not restricted) before it automatically becomes SUSPENDED. "
        "Per-tenant, so one tenant can be given more time without changing "
        "the default for anyone else."
    ),
)
async def extend_grace(
    id: UUID,
    data: SubscriptionExtendGraceRequest,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: SubscriptionService = Depends(_svc),
) -> SubscriptionResponse:
    return await svc.extend_grace(id, data)


@router.post(
    "/{id}/waive",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Waive the current due period",
    description=(
        "Forgives the current billing period without requiring payment — "
        "extends expires_at by one billing cycle and sets status -> ACTIVE, "
        "exactly like Record Payment, except the resulting payment-history "
        "row has amount 0 and is flagged waived=true so it's never confused "
        "with money actually received."
    ),
)
async def waive_subscription(
    id: UUID,
    data: SubscriptionWaiveRequest,
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: SubscriptionService = Depends(_svc),
) -> PaymentResponse:
    return await svc.waive(id, data, recorded_by=current.admin_id)


@router.post(
    "/{id}/cancel",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel subscription",
    description="Permanently cancels. Cannot be undone — create a new subscription instead.",
)
async def cancel_subscription(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: SubscriptionService = Depends(_svc),
) -> SubscriptionResponse:
    return await svc.cancel(id)


# ----------------------------------------------------------------
# PAYMENTS
# ----------------------------------------------------------------

@router.post(
    "/{id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record payment",
    description=(
        "Record a manual payment (bank transfer, cash, cheque). "
        "Automatically extends the subscription by one billing period and sets status → ACTIVE."
    ),
)
async def record_payment(
    id: UUID,
    data: RecordPaymentRequest,
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: SubscriptionService = Depends(_svc),
) -> PaymentResponse:
    return await svc.record_payment(
        subscription_id=id,
        data=data,
        recorded_by=current.admin_id,
    )


@router.get(
    "/{id}/payments",
    response_model=list[PaymentResponse],
    status_code=status.HTTP_200_OK,
    summary="Payment history",
)
async def list_payments(
    id: UUID,
    skip: int = 0,
    limit: int = 50,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: SubscriptionService = Depends(_svc),
) -> list[PaymentResponse]:
    return await svc.list_payments(subscription_id=id, skip=skip, limit=limit)
