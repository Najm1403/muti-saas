# schemas/platform_auth.py
#
# Request/response shapes for the Platform Admin auth endpoints.
# Kept separate from tenant auth schemas (schemas/auth.py).

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import EmailStr, Field

from schemas.common import APIBaseSchema

PlatformRole = Literal["owner", "manager", "viewer"]


class PlatformLoginRequest(APIBaseSchema):
    """Credentials used by a platform admin to log in."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class PlatformTokenResponse(APIBaseSchema):
    """JWT pair returned after a successful platform admin login or refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class PlatformRefreshRequest(APIBaseSchema):
    """Refresh token submitted to obtain a new platform access token."""

    refresh_token: str


class PlatformAdminResponse(APIBaseSchema):
    """Public profile of a platform admin returned by the API."""

    id: UUID
    email: str
    full_name: str
    is_active: bool
    is_super: bool
    role: str = "manager"          # owner | manager | viewer
    can_manage_business_templates: bool = False
    created_at: datetime
    updated_at: datetime


class PlatformChangePasswordRequest(APIBaseSchema):
    """Password change submitted by an authenticated platform admin."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class PlatformForgotPasswordRequest(APIBaseSchema):
    """Start a self-service reset — a 6-digit OTP is emailed to this address."""

    email: EmailStr


class PlatformResetPasswordRequest(APIBaseSchema):
    """Complete the reset with the OTP received by email."""

    token: str = Field(..., description="The 6-digit OTP from the email.")
    new_password: str = Field(..., min_length=8)


# ================================================================
# PLATFORM ADMIN CRUD (used by the Platform Users management page)
# ================================================================

class PlatformAdminCreate(APIBaseSchema):
    """
    Payload to create a new platform admin account.
    Only a super-admin (owner) can do this.
    """

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=150)
    password: str = Field(..., min_length=8, description="Plain-text — hashed before storage.")
    role: PlatformRole = Field(
        default="manager",
        description="owner = full access · manager = all except plans/settings/admins · viewer = read-only.",
    )
    # Legacy flag — still accepted; `owner` role is authoritative when both are sent.
    is_super: bool | None = Field(default=None, deprecated=True)


class PlatformAdminUpdate(APIBaseSchema):
    """Fields that a platform admin (or super-admin) can update."""

    full_name: str | None = Field(None, min_length=1, max_length=150)
    role: PlatformRole | None = None
    is_super: bool | None = None
    is_active: bool | None = None
    can_manage_business_templates: bool | None = Field(
        None,
        description="Explicit grant to delete Business Templates and change their "
                     "config.modules.hidden — super-admin only to set. Owners have this "
                     "implicitly regardless of the stored value.",
    )


class PlatformStepUpRequest(APIBaseSchema):
    """Re-confirms the current platform admin's own password immediately before a
    high-blast-radius action (Business Template delete / modules.hidden change).
    Returns a short-lived token scoped to exactly that action + target, so it
    can't be replayed against a different template or a different action."""

    password: str = Field(..., min_length=1)
    action: Literal["delete_business_template", "update_business_template_modules"]
    template_id: UUID


class PlatformStepUpResponse(APIBaseSchema):
    step_up_token: str
    expires_in: int  # seconds
