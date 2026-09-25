# services/platform_auth_service.py
#
# Authentication for platform admins only.
# Completely separate from tenant AuthService — different table, different JWT type.

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.email import send_password_reset_otp
from services.platform_setting_service import PlatformSettingService
from core.exceptions import AuthenticationError, ForbiddenError, NotFoundError, ValidationError
from core.security import (
    create_platform_access_token,
    create_platform_refresh_token,
    create_platform_step_up_token,
    decode_token,
    hash_password,
    verify_password,
)
from repositories.platform_admin_repository import PlatformAdminRepository
from schemas.platform_auth import (
    PlatformChangePasswordRequest,
    PlatformForgotPasswordRequest,
    PlatformLoginRequest,
    PlatformRefreshRequest,
    PlatformResetPasswordRequest,
    PlatformStepUpRequest,
    PlatformStepUpResponse,
    PlatformTokenResponse,
)

STEP_UP_TOKEN_MINUTES = 5


class PlatformAuthService:
    """
    Handles login, token refresh, and password management for platform admins.

    Platform tokens carry type="platform_access" (not "access"), so they are
    rejected by tenant endpoints and vice-versa.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PlatformAdminRepository(db)

    # ----------------------------------------------------------------
    # LOGIN
    # ----------------------------------------------------------------

    async def login(self, data: PlatformLoginRequest) -> PlatformTokenResponse:
        """Verify email + password and return a platform token pair."""

        admin = await self.repo.get_by_email(data.email)
        if not admin:
            raise AuthenticationError("Invalid email or password.")

        if not admin.is_active:
            raise ForbiddenError("Platform admin account is inactive.")

        if not verify_password(data.password, admin.password_hash):
            raise AuthenticationError("Invalid email or password.")

        return PlatformTokenResponse(
            access_token=create_platform_access_token(admin.id),
            refresh_token=create_platform_refresh_token(admin.id),
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ----------------------------------------------------------------
    # REFRESH
    # ----------------------------------------------------------------

    async def refresh(self, data: PlatformRefreshRequest) -> PlatformTokenResponse:
        """Exchange a valid platform refresh token for a new token pair."""

        try:
            payload = decode_token(data.refresh_token)
        except ValidationError:
            raise AuthenticationError("Invalid or expired refresh token.")

        if payload.get("type") != "platform_refresh":
            raise AuthenticationError("Provided token is not a platform refresh token.")

        try:
            admin_id = UUID(str(payload["sub"]))
        except (KeyError, ValueError, TypeError):
            raise AuthenticationError("Malformed token payload.")

        admin = await self.repo.get_by_id(admin_id)
        if not admin:
            raise AuthenticationError("Platform admin no longer exists.")
        if not admin.is_active:
            raise ForbiddenError("Platform admin account is inactive.")

        return PlatformTokenResponse(
            access_token=create_platform_access_token(admin.id),
            refresh_token=create_platform_refresh_token(admin.id),
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ----------------------------------------------------------------
    # CHANGE PASSWORD
    # ----------------------------------------------------------------

    async def change_password(
        self,
        admin_id: UUID,
        data: PlatformChangePasswordRequest,
    ) -> None:
        """Change the password of an authenticated platform admin."""

        admin = await self.repo.get_by_id(admin_id)
        if not admin:
            raise NotFoundError("Platform admin not found.")

        if not verify_password(data.current_password, admin.password_hash):
            raise ValidationError("Current password is incorrect.")

        await self.repo.update(admin_id, password_hash=hash_password(data.new_password))
        await self.db.commit()

    # ----------------------------------------------------------------
    # STEP-UP — re-confirm own password immediately before a guarded action
    # ----------------------------------------------------------------

    async def step_up(
        self, admin_id: UUID, data: PlatformStepUpRequest
    ) -> PlatformStepUpResponse:
        """Verifies the admin's own current password and mints a short-lived,
        action+template-scoped token (see core.security.create_platform_step_up_token).
        Does not check `can_manage_business_templates` — that's the route-level
        permission check; this only proves fresh password intent."""

        admin = await self.repo.get_by_id(admin_id)
        if not admin:
            raise NotFoundError("Platform admin not found.")

        if not verify_password(data.password, admin.password_hash):
            raise AuthenticationError("Password is incorrect.")

        token = create_platform_step_up_token(
            admin_id, data.action, data.template_id, minutes=STEP_UP_TOKEN_MINUTES
        )
        return PlatformStepUpResponse(
            step_up_token=token, expires_in=STEP_UP_TOKEN_MINUTES * 60
        )

    async def admin_reset_password(
        self,
        target_admin_id: UUID,
        new_password: str,
    ) -> None:
        """
        Force-set a platform admin's password without verifying the current one.

        Intended for super-admins who need to unlock a locked-out admin account.
        The caller's authorization (is_super check) must be enforced by the router.
        """
        admin = await self.repo.get_by_id(target_admin_id)
        if not admin:
            raise NotFoundError("Platform admin not found.")
        await self.repo.update(target_admin_id, password_hash=hash_password(new_password))
        await self.db.commit()

    # ----------------------------------------------------------------
    # SELF-SERVICE FORGOT / RESET  (public — no auth)
    # ----------------------------------------------------------------

    async def forgot_password(self, data: PlatformForgotPasswordRequest) -> None:
        """Email a 6-digit OTP to the platform admin with this address.

        Always returns None — never reveals whether the account exists. Only the
        SHA-256 hash of the OTP is stored; it expires after
        PASSWORD_RESET_EXPIRE_MINUTES and is single-use.
        """
        admin = await self.repo.get_by_email(str(data.email))
        if not admin or not admin.is_active:
            return

        otp = f"{secrets.randbelow(1_000_000):06d}"
        token_hash = hashlib.sha256(otp.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
        )
        await self.repo.update(
            admin.id,
            password_reset_token=token_hash,
            password_reset_expires_at=expires_at,
        )
        await self.db.commit()

        # Fire-and-forget — SMTP errors are logged inside, never raised.
        smtp_cfg = await PlatformSettingService(self.db).get_all()
        await send_password_reset_otp(to_email=admin.email, otp=otp, smtp_cfg=smtp_cfg)

    async def reset_password(self, data: PlatformResetPasswordRequest) -> None:
        """Complete the reset: verify OTP hash + expiry, set the new password,
        clear the token so it cannot be replayed."""
        token_hash = hashlib.sha256(data.token.encode()).hexdigest()
        admin = await self.repo.get_by_reset_token(token_hash)
        if not admin:
            raise AuthenticationError("Invalid or expired reset token.")

        now = datetime.now(timezone.utc)
        if admin.password_reset_expires_at is None or admin.password_reset_expires_at < now:
            raise AuthenticationError("Invalid or expired reset token.")

        await self.repo.update(
            admin.id,
            password_hash=hash_password(data.new_password),
            password_reset_token=None,
            password_reset_expires_at=None,
        )
        await self.db.commit()
