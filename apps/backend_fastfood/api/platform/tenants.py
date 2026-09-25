# api/platform/tenants.py
#
# Platform-level tenant management — visible to platform admins only.
#
# Standard CRUD uses TenantService.
# Enriched detail + branch management use OnboardingService
# (which can run cross-tenant DB queries that are off-limits to tenant-scoped APIs).
#
# Prefix: /api/platform/tenants

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import CurrentPlatformAdmin, get_current_platform_admin
from core.email import send_platform_recovery_email
from core.exceptions import NotFoundError, ValidationError
from core.security import hash_password
from db.session import get_db
from models.user import User
from schemas.common import MessageResponse
from schemas.onboarding import (
    BranchPlatformCreate,
    BranchPlatformResponse,
    BranchPlatformUpdate,
    DeviceHealthResponse,
    DevicePlatformResponse,
    TenantDetailResponse,
    TenantUserCreate,
    TenantUserResponse,
)
from schemas.tenant import TenantAdminMessageRequest, TenantCreate, TenantResponse, TenantUpdate
from services.onboarding_service import OnboardingService
from services.platform_setting_service import PlatformSettingService
from services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["Platform · Tenants"])


def _svc(db: AsyncSession = Depends(get_db)) -> TenantService:
    return TenantService(db)


def _ob_svc(db: AsyncSession = Depends(get_db)) -> OnboardingService:
    return OnboardingService(db)


# ----------------------------------------------------------------
# ALL DEVICES (cross-tenant) — sync health view
# ----------------------------------------------------------------

@router.get(
    "/devices/all",
    response_model=list[DeviceHealthResponse],
    status_code=status.HTTP_200_OK,
    summary="List all devices (all tenants)",
    description="Returns every device across all tenants for the platform sync-health dashboard. Platform admin only.",
    tags=["Platform · Devices"],
)
async def list_all_devices(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: OnboardingService = Depends(_ob_svc),
) -> list[DeviceHealthResponse]:
    return await svc.list_all_devices()


# ----------------------------------------------------------------
# LIST ALL TENANTS
# ----------------------------------------------------------------

@router.get(
    "",
    response_model=list[TenantResponse],
    status_code=status.HTTP_200_OK,
    summary="List all tenants",
    description="Returns every tenant on the platform. Platform admin only.",
)
@router.get("/", response_model=list[TenantResponse], status_code=status.HTTP_200_OK, include_in_schema=False)
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: TenantService = Depends(_svc),
) -> list[TenantResponse]:
    return await svc.list(skip=skip, limit=limit)


# ----------------------------------------------------------------
# CREATE TENANT
# ----------------------------------------------------------------

@router.post(
    "/",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tenant",
    description="Register a new business account on the platform.",
)
async def create_tenant(
    data: TenantCreate,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: TenantService = Depends(_svc),
) -> TenantResponse:
    return await svc.create(data)


# ----------------------------------------------------------------
# GET TENANT
# ----------------------------------------------------------------

@router.get(
    "/{id}",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tenant",
)
async def get_tenant(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: TenantService = Depends(_svc),
) -> TenantResponse:
    return await svc.get(id)


# ----------------------------------------------------------------
# UPDATE TENANT
# ----------------------------------------------------------------

@router.patch(
    "/{id}",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Update tenant",
)
async def update_tenant(
    id: UUID,
    data: TenantUpdate,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: TenantService = Depends(_svc),
) -> TenantResponse:
    return await svc.update(id, data)


# ----------------------------------------------------------------
# SUSPEND / ACTIVATE
# ----------------------------------------------------------------

@router.post(
    "/{id}/suspend",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Suspend tenant",
    description="Blocks all tenant users from logging in immediately.",
)
async def suspend_tenant(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: TenantService = Depends(_svc),
) -> TenantResponse:
    return await svc.deactivate(id)


@router.post(
    "/{id}/activate",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate tenant",
)
async def activate_tenant(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: TenantService = Depends(_svc),
) -> TenantResponse:
    return await svc.activate(id)


# ----------------------------------------------------------------
# ADMIN MESSAGE — notice shown to the tenant on dashboard login
# ----------------------------------------------------------------

@router.put(
    "/{id}/message",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Set tenant notice",
    description=(
        "Sets the free-text notice shown to the tenant as a popup after "
        "dashboard login (billing warnings, policy notes, or any other "
        "instruction). Replaces any existing message — this is one current "
        "notice, not a log."
    ),
)
async def set_tenant_message(
    id: UUID,
    data: TenantAdminMessageRequest,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: TenantService = Depends(_svc),
) -> TenantResponse:
    return await svc.set_admin_message(id, data.message)


@router.delete(
    "/{id}/message",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear tenant notice",
)
async def clear_tenant_message(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: TenantService = Depends(_svc),
) -> TenantResponse:
    return await svc.clear_admin_message(id)


# ----------------------------------------------------------------
# DELETE (soft)
# ----------------------------------------------------------------

@router.delete(
    "/{id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete tenant",
    description="Soft-deletes the tenant. Data is retained but the account becomes inaccessible.",
)
async def delete_tenant(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: TenantService = Depends(_svc),
) -> MessageResponse:
    return await svc.delete(id)


# ----------------------------------------------------------------
# ENRICHED DETAIL (owner info + aggregate counts + subscription)
# ----------------------------------------------------------------

@router.get(
    "/{id}/detail",
    response_model=TenantDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tenant detail",
    description=(
        "Returns enriched tenant data for the platform admin detail screen: "
        "owner name/email/username, user count, branch count, device count, "
        "and active subscription summary. "
        "Uses cross-tenant DB queries — only accessible with a platform token."
    ),
)
async def get_tenant_detail(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: OnboardingService = Depends(_ob_svc),
) -> TenantDetailResponse:
    return await svc.get_tenant_detail(id)


# ----------------------------------------------------------------
# PLATFORM BRANCH MANAGEMENT
# ----------------------------------------------------------------

@router.get(
    "/{id}/branches",
    response_model=list[BranchPlatformResponse],
    status_code=status.HTTP_200_OK,
    summary="List tenant branches",
    description=(
        "Returns all branches for the given tenant with per-branch device counts. "
        "Uses cross-tenant DB access — platform admin only."
    ),
)
async def list_tenant_branches(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: OnboardingService = Depends(_ob_svc),
) -> list[BranchPlatformResponse]:
    return await svc.list_tenant_branches(id)


@router.post(
    "/{id}/branches",
    response_model=BranchPlatformResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tenant branch",
    description=(
        "Creates a new branch under the tenant's business. "
        "The business is resolved automatically from the onboarding record. "
        "Returns 404 if the tenant has no business yet."
    ),
)
async def create_tenant_branch(
    id: UUID,
    data: BranchPlatformCreate,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: OnboardingService = Depends(_ob_svc),
) -> BranchPlatformResponse:
    return await svc.create_tenant_branch(tenant_id=id, data=data)


# ----------------------------------------------------------------
# PLATFORM DEVICE MANAGEMENT
# ----------------------------------------------------------------

@router.get(
    "/{id}/devices",
    response_model=list[DevicePlatformResponse],
    status_code=status.HTTP_200_OK,
    summary="List tenant devices",
    description=(
        "Returns all devices registered across all branches of the given tenant, "
        "with branch name and code included in each row. "
        "Uses cross-tenant DB access — platform admin only."
    ),
)
async def list_tenant_devices(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: OnboardingService = Depends(_ob_svc),
) -> list[DevicePlatformResponse]:
    return await svc.list_tenant_devices(id)

# Devices are created by the tenant (POST /api/v1/devices). Platform emergency
# controls (suspend / reactivate / revoke) live at /api/platform/devices/{id}/...


# ----------------------------------------------------------------
# TENANT USER MANAGEMENT (platform admin view)
# ----------------------------------------------------------------

@router.get(
    "/{id}/users",
    response_model=list[TenantUserResponse],
    status_code=status.HTTP_200_OK,
    summary="List tenant users",
    description=(
        "Returns all users belonging to a tenant with their assigned role names. "
        "Uses cross-tenant DB access — platform admin only."
    ),
)
async def list_tenant_users(
    id: UUID,
    skip: int = 0,
    limit: int = 100,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: OnboardingService = Depends(_ob_svc),
) -> list[TenantUserResponse]:
    return await svc.list_tenant_users(tenant_id=id, skip=skip, limit=limit)


@router.post(
    "/{id}/users",
    response_model=TenantUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tenant user",
    description=(
        "Creates a new user inside a tenant from the platform admin UI. "
        "Optionally assigns a role by name. Returns 409 if username is taken."
    ),
)
async def create_tenant_user(
    id: UUID,
    data: TenantUserCreate,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: OnboardingService = Depends(_ob_svc),
) -> TenantUserResponse:
    return await svc.create_tenant_user(tenant_id=id, data=data)


# ----------------------------------------------------------------
# TENANT USER PASSWORD RESET
# ----------------------------------------------------------------

@router.post(
    "/{id}/users/{user_id}/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset tenant user password",
    description=(
        "Force-set a new password for any user within a tenant. "
        "Platform admin only — no current password required. "
        "new_password must be at least 6 characters. "
        "For the tenant owner's email-based OTP recovery use POST /{id}/account-recovery instead."
    ),
)
async def reset_tenant_user_password(
    id: UUID,
    user_id: UUID,
    new_password: str = Body(..., min_length=6),
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == id,
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found in this tenant.")
    user.password_hash = hash_password(new_password)
    await db.commit()
    return MessageResponse(message="User password reset successfully.")


# ----------------------------------------------------------------
# BRANCH UPDATE
# ----------------------------------------------------------------

@router.patch(
    "/{id}/branches/{branch_id}",
    response_model=BranchPlatformResponse,
    status_code=status.HTTP_200_OK,
    summary="Update tenant branch",
    description=(
        "Partial-update a branch (name, address, phone, is_active). "
        "branch_code is not updatable to preserve device codes derived from it."
    ),
)
async def update_tenant_branch(
    id: UUID,
    branch_id: UUID,
    data: BranchPlatformUpdate,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: OnboardingService = Depends(_ob_svc),
) -> BranchPlatformResponse:
    return await svc.update_tenant_branch(tenant_id=id, branch_id=branch_id, data=data)


# ----------------------------------------------------------------
# ACCOUNT RECOVERY
# ----------------------------------------------------------------

@router.post(
    "/{id}/account-recovery",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger owner account recovery",
    description=(
        "Generates a 6-digit OTP for the tenant's owner user, stores its hash, "
        "and sends it to the owner's email via the platform SMTP settings. "
        "Falls back to env-var SMTP if the platform DB settings are not configured."
    ),
)
async def account_recovery(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: TenantService = Depends(_svc),
    ob_svc: OnboardingService = Depends(_ob_svc),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    # 404 guard
    await svc.get(id)

    # Get enriched detail — includes owner_email, owner_name, tenant_code
    detail = await ob_svc.get_tenant_detail(id)
    owner_email = detail.owner_email
    if not owner_email:
        raise ValidationError("Tenant owner has no email address on file.")

    # Fetch the owner User model to store the OTP hash
    result = await db.execute(
        select(User)
        .where(User.tenant_id == id, User.deleted_at.is_(None))
        .order_by(User.created_at)
        .limit(1)
    )
    owner = result.scalar_one_or_none()
    if not owner:
        raise NotFoundError("Tenant owner user not found.")

    # Generate 6-digit OTP, store hash + 30-minute expiry
    otp        = f"{secrets.randbelow(1_000_000):06d}"
    otp_hash   = hashlib.sha256(otp.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    owner.password_reset_token      = otp_hash
    owner.password_reset_expires_at = expires_at
    await db.commit()

    # Read platform SMTP settings from DB
    smtp_cfg = await PlatformSettingService(db).get_all()

    # Fire-and-forget — errors are logged inside, not raised
    await send_platform_recovery_email(
        to_email=owner_email,
        to_name=detail.owner_name or "Tenant Owner",
        tenant_code=detail.tenant_code,
        otp=otp,
        smtp_cfg=smtp_cfg,
    )

    return MessageResponse(
        message=f"Account recovery OTP sent to {owner_email}."
    )
