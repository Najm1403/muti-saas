# schemas/subscription.py

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from models.subscription import BillingCycle, SubscriptionStatus
from schemas.common import APIBaseSchema
from schemas.plan import PlanResponse
from schemas.tenant import TenantResponse


class SubscriptionCreate(APIBaseSchema):
    """Assign a plan to a tenant, starting a new subscription."""

    tenant_id: UUID
    plan_id: UUID
    billing_cycle: BillingCycle
    status: SubscriptionStatus = SubscriptionStatus.TRIAL
    trial_days: int = Field(default=14, ge=0)
    # trial_days=0 means no trial — subscription starts as ACTIVE immediately.
    discount_pct: Decimal | None = Field(default=None, ge=0, le=100, decimal_places=2)
    # Per-tenant discount override. NULL → the plan's cycle-level discount applies.


class SubscriptionUpdate(APIBaseSchema):
    """Editable fields on an existing subscription (platform admin)."""

    plan_id: UUID | None = None
    billing_cycle: BillingCycle | None = None
    discount_pct: Decimal | None = Field(default=None, ge=0, le=100, decimal_places=2)


class SubscriptionExtendTrialRequest(APIBaseSchema):
    """Body for extending an in-progress trial. Super admin only."""

    extend_days: int = Field(
        ..., gt=0, le=365,
        description="Days to add to the current trial_ends_at (and expires_at, by the same amount).",
    )


class SubscriptionExtendGraceRequest(APIBaseSchema):
    """Body for extending a subscription's grace period (per-tenant)."""

    extend_days: int = Field(
        ..., gt=0, le=365,
        description="Days to add to this subscription's grace_period_days.",
    )


class SubscriptionWaiveRequest(APIBaseSchema):
    """Body for forgiving the current due period without a payment."""

    note: str | None = Field(
        default=None, max_length=500,
        description="Why this period was waived — kept on the resulting payment-history row.",
    )


class SubscriptionResponse(APIBaseSchema):
    """Subscription data returned by the API."""

    id: UUID
    tenant_id: UUID
    plan_id: UUID
    billing_cycle: BillingCycle
    status: SubscriptionStatus
    started_at: datetime
    expires_at: datetime
    trial_ends_at: datetime | None
    grace_period_days: int
    discount_pct: Decimal | None = None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SubscriptionDetailResponse(SubscriptionResponse):
    """Extended response that embeds the related plan and tenant."""

    plan: PlanResponse
    tenant: TenantResponse


# ── Payments ──────────────────────────────────────────────────

class RecordPaymentRequest(APIBaseSchema):
    """Body for recording a manual payment against a subscription."""

    amount: Decimal = Field(..., gt=0, decimal_places=2)
    payment_method: str = Field(..., min_length=2, max_length=100,
                                examples=["Bank Transfer", "Cash", "Cheque"])
    reference_number: str | None = Field(default=None, max_length=150)
    notes: str | None = None
    paid_at: datetime
    # paid_at is the actual date money was received, not the recording date.
    list_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    discount_pct: Decimal | None = Field(default=None, ge=0, le=100, decimal_places=2)
    # Optional — when omitted the service derives both from the plan + subscription discount.


class PaymentResponse(APIBaseSchema):
    """Payment record returned by the API."""

    id: UUID
    subscription_id: UUID
    tenant_id: UUID
    amount: Decimal
    list_price: Decimal | None = None
    discount_pct: Decimal | None = None
    billing_cycle: BillingCycle
    period_start: datetime
    period_end: datetime
    payment_method: str
    reference_number: str | None
    notes: str | None
    paid_at: datetime
    recorded_by: UUID
    waived: bool = False
    created_at: datetime


class BillingPreviewResponse(APIBaseSchema):
    """Computed price for a subscription's current plan + billing cycle."""

    billing_cycle: BillingCycle
    list_price: Decimal
    discount_pct: Decimal
    discount_amount: Decimal
    net_price: Decimal


# ── Tenant-facing (read-only, isolated to the caller's tenant) ─

class TenantSubscriptionView(APIBaseSchema):
    """The caller tenant's own subscription summary — no cross-tenant identifiers."""

    plan_name: str
    max_branches: int
    max_devices: int
    max_users: int
    billing_cycle: BillingCycle
    status: SubscriptionStatus
    started_at: datetime
    expires_at: datetime
    trial_ends_at: datetime | None = None
    grace_period_days: int
    list_price: Decimal
    discount_pct: Decimal
    discount_amount: Decimal
    net_price: Decimal


class TenantPaymentView(APIBaseSchema):
    """One payment as shown to the tenant. Omits recorded_by / internal IDs."""

    amount: Decimal
    list_price: Decimal | None = None
    discount_pct: Decimal | None = None
    billing_cycle: BillingCycle
    period_start: datetime
    period_end: datetime
    payment_method: str
    reference_number: str | None = None
    notes: str | None = None
    paid_at: datetime
