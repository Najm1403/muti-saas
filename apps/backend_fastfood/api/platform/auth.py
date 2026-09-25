# api/platform/auth.py
#
# Authentication routes for platform admins.
# Prefix: /api/platform/auth

from __future__ import annotations
from core.auth_limits import limit_auth

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import CurrentPlatformAdmin, get_current_platform_admin
from db.session import get_db
from repositories.platform_admin_repository import PlatformAdminRepository
from schemas.common import MessageResponse
from schemas.platform_auth import (
    PlatformAdminResponse,
    PlatformChangePasswordRequest,
    PlatformForgotPasswordRequest,
    PlatformLoginRequest,
    PlatformRefreshRequest,
    PlatformResetPasswordRequest,
    PlatformStepUpRequest,
    PlatformStepUpResponse,
    PlatformTokenResponse,
)
from services.platform_auth_service import PlatformAuthService

router = APIRouter(prefix="/auth", tags=["Platform · Auth"], dependencies=[Depends(limit_auth)])


# ----------------------------------------------------------------
# LOGIN  (public)
# ----------------------------------------------------------------

@router.post(
    "/login",
    response_model=PlatformTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Platform admin login",
    description="Authenticate with email + password. Returns a platform-scoped token pair.",
)
async def login(
    data: PlatformLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> PlatformTokenResponse:
    return await PlatformAuthService(db).login(data)


# ----------------------------------------------------------------
# REFRESH  (public)
# ----------------------------------------------------------------

@router.post(
    "/refresh",
    response_model=PlatformTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh platform tokens",
)
async def refresh(
    data: PlatformRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> PlatformTokenResponse:
    return await PlatformAuthService(db).refresh(data)


# ----------------------------------------------------------------
# ME  (protected)
# ----------------------------------------------------------------

@router.get(
    "/me",
    response_model=PlatformAdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Current platform admin",
)
async def get_me(
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> PlatformAdminResponse:
    admin = await PlatformAdminRepository(db).get_by_id(current.admin_id)
    return PlatformAdminResponse.model_validate(admin)


# ----------------------------------------------------------------
# CHANGE PASSWORD  (protected)
# ----------------------------------------------------------------

@router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change platform admin password",
)
async def change_password(
    data: PlatformChangePasswordRequest,
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await PlatformAuthService(db).change_password(admin_id=current.admin_id, data=data)
    return MessageResponse(message="Password changed successfully.")


# ----------------------------------------------------------------
# STEP-UP  (protected) — re-confirm own password before a guarded action
# ----------------------------------------------------------------

@router.post(
    "/step-up",
    response_model=PlatformStepUpResponse,
    status_code=status.HTTP_200_OK,
    summary="Re-confirm password before a high-blast-radius action",
    description=(
        "Verifies the caller's own current password and returns a 5-minute token "
        "scoped to exactly the action + template named in the request — required "
        "in addition to (never instead of) the can_manage_business_templates "
        "permission for deleting a Business Template or changing its "
        "config.modules.hidden. 401 if the password is wrong."
    ),
)
async def step_up(
    data: PlatformStepUpRequest,
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> PlatformStepUpResponse:
    return await PlatformAuthService(db).step_up(admin_id=current.admin_id, data=data)


# ----------------------------------------------------------------
# SELF-SERVICE FORGOT / RESET  (public — no auth)
# ----------------------------------------------------------------

@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Start a platform-admin password reset (emails a 6-digit OTP)",
    description=(
        "Public. Always returns 200 — the response never reveals whether the "
        "email belongs to a platform admin. The OTP expires after "
        "PASSWORD_RESET_EXPIRE_MINUTES and is single-use."
    ),
)
async def forgot_password(
    data: PlatformForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await PlatformAuthService(db).forgot_password(data)
    return MessageResponse(message="If that account exists, a reset code has been sent.")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete a platform-admin password reset with the OTP",
    description="Public. Verifies the 6-digit OTP + expiry, then sets the new password.",
)
async def reset_password(
    data: PlatformResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await PlatformAuthService(db).reset_password(data)
    return MessageResponse(message="Password reset successfully. You can sign in now.")
