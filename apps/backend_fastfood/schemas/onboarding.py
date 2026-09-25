# schemas/onboarding.py
#
# Request and response schemas for platform-level tenant onboarding.
#
# OnboardingCreate  — single payload that creates Tenant + Owner + Role +
#                     Business + Branch + Subscription in one transaction.
# OnboardingResponse — confirmation returned after a successful onboard.
# TenantDetailResponse — enriched tenant view for the platform admin UI
#                        (includes owner info, counts, subscription).
# BranchPlatformCreate / BranchPlatformResponse — platform-side branch
#                        management (no tenant JWT required).
#
# Depends on: models/subscription.py (BillingCycle, SubscriptionStatus)
# Used by:    services/onboarding_service.py
#             api/platform/onboarding.py
#             api/platform/tenants.py

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from models.subscription import BillingCycle, SubscriptionStatus
from schemas.common import APIBaseSchema


# ================================================================
# ONBOARDING — CREATE
# ================================================================

class OnboardingCreate(APIBaseSchema):
    """
    Full tenant onboarding payload.

    All entities are created in a single atomic transaction:
      Tenant → Owner User → Admin Role → Business → Branch → Subscription
      (plus category/variant-group/addon-group seeding from the Business Template)

    Codes (tenant_code, branch_code) are normalised to uppercase on input.
    Username is normalised to lowercase.
    """

    # ── Business (→ Tenant + Business) ──────────────────────────
    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Business display name.",
    )
    business_template_id: UUID = Field(
        ...,
        description="Business type (Fast Food / Electronics / ...) — drives Variant/Add-on "
                     "seeding, inventory strictness, pricing fields, and POS layout.",
    )
    tenant_code: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique short code for the tenant (e.g. ABC001). Stored as uppercase.",
    )
    country: str | None = Field(None, max_length=100)
    timezone: str | None = Field(None, max_length=100)
    currency: str = Field(
        default="Rs.",
        max_length=8,
        description="Money display string for this shop's POS (e.g. 'Rs.', '$').",
    )

    # ── Owner (→ User) ─────────────────────────────────────────────
    owner_name: str = Field(..., min_length=1, max_length=150)
    owner_username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Login username. Stored as lowercase.",
    )
    owner_email: str = Field(..., min_length=5, max_length=255)

    # ── Subscription ───────────────────────────────────────────────
    plan_id: UUID | None = Field(
        None,
        description="Leave null to create the tenant without a plan.",
    )
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    trial_days: int = Field(
        default=14,
        ge=0,
        le=365,
        description="0 = no trial, tenant starts as ACTIVE immediately.",
    )

    # ── Initial Branch ─────────────────────────────────────────────
    branch_name: str = Field(..., min_length=1, max_length=150)
    branch_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique within the tenant's business. Stored as uppercase.",
    )

    # ── Validators ─────────────────────────────────────────────────

    @field_validator("tenant_code", "branch_code", mode="before")
    @classmethod
    def uppercase_codes(cls, v: str) -> str:
        """Normalise codes to uppercase so ABC001 and abc001 are the same code."""
        return v.strip().upper() if isinstance(v, str) else v

    @field_validator("owner_username", mode="before")
    @classmethod
    def lowercase_username(cls, v: str) -> str:
        """Usernames are case-insensitive; store lowercase for consistent lookup."""
        return v.strip().lower() if isinstance(v, str) else v


# ================================================================
# ONBOARDING — RESPONSE (confirmation screen data)
# ================================================================

class OnboardingResponse(APIBaseSchema):
    """
    Returned immediately after a successful onboarding transaction.
    Contains the generated IDs and display values for all created entities.
    No password is returned — the owner uses Account Recovery to set theirs.
    """

    # Tenant
    tenant_id: UUID
    tenant_name: str
    tenant_code: str

    # Owner
    user_id: UUID
    owner_name: str
    owner_username: str
    owner_email: str

    # Business (auto-created)
    business_id: UUID

    # Branch
    branch_id: UUID
    branch_name: str
    branch_code: str

    # Subscription (null when no plan_id was provided)
    subscription_id: UUID | None = None
    plan_name: str | None = None
    trial_days: int | None = None

    # One-time credential — shown once on the confirmation screen.
    # Owner must change this via Account Recovery or first login.
    owner_temp_password: str


# ================================================================
# TENANT DETAIL — enriched platform admin view
# ================================================================

class TenantDetailResponse(APIBaseSchema):
    """
    Enriched tenant information for the platform admin detail screen.

    Includes:
      • Basic tenant fields
      • Owner's display name, email, and username (first admin user)
      • Aggregate counts: users, branches, devices (queried server-side)
      • Active subscription summary
    """

    # Tenant
    id: UUID
    name: str
    tenant_code: str
    is_active: bool
    created_at: datetime
    business_template_id: UUID | None = None
    business_template_name: str | None = None

    # Owner (first admin user; null if none found)
    owner_name: str | None = None
    owner_email: str | None = None
    owner_username: str | None = None

    # Counts (queried via cross-tenant DB access — platform admin only)
    user_count: int = 0
    branch_count: int = 0
    device_count: int = 0

    # Subscription summary
    subscription_id: UUID | None = None
    subscription_status: str | None = None
    plan_name: str | None = None
    trial_ends_at: datetime | None = None
    expires_at: datetime | None = None


# ================================================================
# PLATFORM BRANCH MANAGEMENT
# ================================================================

class BranchPlatformCreate(APIBaseSchema):
    """
    Create a branch for a specific tenant directly from the platform admin UI.
    Used by POST /api/platform/tenants/{tenant_id}/branches.

    The business is resolved automatically (the tenant's one Business,
    created during onboarding).
    """

    name: str = Field(..., min_length=1, max_length=150)
    branch_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Must be unique within the tenant's business. Stored as uppercase.",
    )
    address: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=30)
    is_active: bool = True

    @field_validator("branch_code", mode="before")
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.strip().upper() if isinstance(v, str) else v


class BranchPlatformResponse(APIBaseSchema):
    """Branch data as seen by the platform admin."""

    id: UUID
    name: str
    branch_code: str
    address: str | None
    phone: str | None
    is_active: bool
    business_id: UUID
    created_at: datetime

    # Aggregate counts populated by the service (not FK columns on Branch)
    user_count: int = 0
    device_count: int = 0


# ================================================================
# PLATFORM DEVICE MANAGEMENT  (read + emergency controls)
# ================================================================
# Devices are created by the tenant (POST /api/v1/devices). The platform admin
# only lists them and can suspend / reactivate / revoke in an emergency
# (/api/platform/devices/{id}/...).

class DevicePlatformResponse(APIBaseSchema):
    """Device record as seen by the platform admin — includes branch name."""

    id: UUID
    branch_id: UUID
    branch_name: str
    branch_code: str
    device_code: str
    name: str
    device_type: str
    status: str
    suspended_scope: str | None = None
    is_active: bool
    is_activated: bool = False
    last_sync_at: datetime | None = None
    activated_at: datetime | None = None
    created_at: datetime


class DeviceHealthResponse(DevicePlatformResponse):
    """All-tenant device view for the platform sync-health page."""

    tenant_id: UUID
    tenant_name: str
    tenant_code: str
    contact: str | None = None   # branch phone number


# ================================================================
# PLATFORM BRANCH UPDATE
# ================================================================

class BranchPlatformUpdate(APIBaseSchema):
    """Partial update for a tenant branch from the platform admin UI."""

    name: str | None = Field(None, min_length=1, max_length=150)
    address: str | None = None
    phone: str | None = None
    is_active: bool | None = None


# ================================================================
# TENANT USER MANAGEMENT (platform admin view)
# ================================================================

class TenantUserCreate(APIBaseSchema):
    """Create a user inside a tenant from the platform admin UI."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Login username. Stored as lowercase.",
    )
    full_name: str = Field(..., min_length=1, max_length=150)
    email: str | None = Field(None, max_length=255)
    password: str = Field(..., min_length=4, description="Plain-text — hashed server-side.")
    pin: str | None = Field(
        None,
        min_length=4,
        max_length=6,
        pattern=r"^\d+$",
        description="Optional 4-6 digit POS quick sign-in PIN — hashed server-side.",
    )
    photo_url: str | None = Field(None, max_length=500)
    role_name: str = Field(
        default="Staff",
        description="Exact name of an existing role in this tenant.",
    )

    @field_validator("username", mode="before")
    @classmethod
    def lowercase_username(cls, v: str) -> str:
        return v.strip().lower() if isinstance(v, str) else v


class TenantUserResponse(APIBaseSchema):
    """User record as seen by the platform admin — includes role names."""

    id: UUID
    tenant_id: UUID
    username: str
    full_name: str
    email: str | None
    is_active: bool
    created_at: datetime
    roles: list[str] = []


# ================================================================
# DASHBOARD STATS
# ================================================================

class DashboardStats(APIBaseSchema):
    """Aggregate platform stats for the super-admin dashboard."""

    total_tenants: int
    active_tenants: int
    suspended_tenants: int
    trial_tenants: int
    total_users: int
    total_branches: int
    total_devices: int
    subscriptions_active: int
    subscriptions_trial: int
    subscriptions_expired: int


# ================================================================
# ACTIVITY / AUDIT LOG
# ================================================================

class ActivityLogResponse(APIBaseSchema):
    """One audit log entry as seen by the platform admin."""

    id: UUID
    tenant_id: UUID
    tenant_name: str | None
    user_id: UUID | None
    username: str | None
    action: str
    module: str
    entity_type: str | None
    entity_id: UUID | None
    description: str | None
    ip_address: str | None
    created_at: datetime
