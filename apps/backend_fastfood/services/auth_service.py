# services/auth_service.py
#
# Handles authentication-only logic: login, token refresh, password change,
# forgot-password OTP, and reset-password confirmation.
# No routes, no DB schema logic — only credentials and JWT operations.

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
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from core.config import settings
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
)


class AuthService:
    """
    Orchestrates authentication for the multi-tenant SaaS system.

    Login flow:
        tenant_code → find tenant → verify active
        username    → find user inside tenant → verify active
        password    → verify hash
        → issue access token + refresh token (both carry tenant_id)

    The tenant_id is embedded in every JWT so downstream services
    can enforce tenant isolation without an extra DB lookup.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.tenant_repo = TenantRepository(db)

    # ----------------------------------------------------------------
    # LOGIN
    # ----------------------------------------------------------------

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Verify credentials and return a new access + refresh token pair."""

        # Intentionally vague error: never reveal whether the tenant or
        # the password was wrong — avoids tenant enumeration.
        _invalid = "Invalid tenant, username, or password."

        tenant = await self.tenant_repo.get_by_code(data.tenant_code)
        if not tenant:
            raise AuthenticationError(_invalid)

        if not tenant.is_active:
            raise ForbiddenError("Tenant account is inactive.")

        user = await self.user_repo.get_by_username(
            username=data.username,
            tenant_id=tenant.id,
        )
        if not user:
            raise AuthenticationError(_invalid)

        if not user.is_active:
            raise ForbiddenError("User account is inactive.")

        if not verify_password(data.password, user.password_hash):
            raise AuthenticationError(_invalid)

        return TokenResponse(
            access_token=create_access_token(user.id, tenant.id),
            refresh_token=create_refresh_token(user.id, tenant.id),
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ----------------------------------------------------------------
    # REFRESH
    # ----------------------------------------------------------------

    async def refresh(self, data: RefreshRequest) -> TokenResponse:
        """Validate a refresh token and issue a new access + refresh token pair."""

        # decode_token raises ValidationError (not jwt.InvalidTokenError —
        # that is already caught inside decode_token itself).
        try:
            payload = decode_token(data.refresh_token)
        except ValidationError:
            raise AuthenticationError("Invalid or expired refresh token.")

        if payload.get("type") != "refresh":
            raise AuthenticationError("Provided token is not a refresh token.")

        try:
            user_id = UUID(str(payload["sub"]))
            tenant_id = UUID(str(payload["tenant_id"]))
        except (KeyError, ValueError, TypeError):
            raise AuthenticationError("Malformed token payload.")

        # Confirm the user and tenant still exist and are active.
        user = await self.user_repo.get_by_id(id=user_id, tenant_id=tenant_id)
        if not user:
            raise AuthenticationError("User no longer exists.")
        if not user.is_active:
            raise ForbiddenError("User account is inactive.")

        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise AuthenticationError("Tenant no longer exists.")
        if not tenant.is_active:
            raise ForbiddenError("Tenant account is inactive.")

        return TokenResponse(
            access_token=create_access_token(user.id, tenant.id),
            refresh_token=create_refresh_token(user.id, tenant.id),
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ----------------------------------------------------------------
    # CHANGE PASSWORD
    # ----------------------------------------------------------------

    async def change_password(
        self,
        user_id: UUID,
        tenant_id: UUID,
        data: ChangePasswordRequest,
    ) -> None:
        """Change the password of an authenticated user.

        Verifies the current password before accepting the new one.
        """

        user = await self.user_repo.get_by_id(id=user_id, tenant_id=tenant_id)
        if not user:
            raise NotFoundError("User not found.")

        if not verify_password(data.current_password, user.password_hash):
            raise ValidationError("Current password is incorrect.")

        await self.user_repo.update(
            id=user_id,
            tenant_id=tenant_id,
            password_hash=hash_password(data.new_password),
        )
        await self.db.commit()

    # ----------------------------------------------------------------
    # FORGOT PASSWORD
    # ----------------------------------------------------------------

    async def forgot_password(self, data: ForgotPasswordRequest) -> None:
        """Initiate a password reset by sending a 6-digit OTP to the user's email.

        Security notes:
            - Always returns None — never reveals whether the tenant or email exists.
            - The raw OTP is emailed; only its SHA-256 hash is stored in the DB.
            - OTP expires after PASSWORD_RESET_EXPIRE_MINUTES (default: 15 min).
        """

        # Silently bail on unknown tenants — never expose account existence.
        tenant = await self.tenant_repo.get_by_code(data.tenant_code)
        if not tenant or not tenant.is_active:
            return

        user = await self.user_repo.get_by_email(
            email=data.email,
            tenant_id=tenant.id,
        )
        if not user or not user.is_active:
            return

        # Generate a cryptographically random 6-digit OTP (zero-padded).
        otp = f"{secrets.randbelow(1_000_000):06d}"
        token_hash = hashlib.sha256(otp.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
        )

        await self.user_repo.update(
            id=user.id,
            tenant_id=tenant.id,
            password_reset_token=token_hash,
            password_reset_expires_at=expires_at,
        )
        await self.db.commit()

        # Fire-and-forget email — errors are logged inside, not raised.
        smtp_cfg = await PlatformSettingService(self.db).get_all()
        await send_password_reset_otp(to_email=user.email, otp=otp, smtp_cfg=smtp_cfg)

    # ----------------------------------------------------------------
    # RESET PASSWORD
    # ----------------------------------------------------------------

    async def reset_password(self, data: ResetPasswordRequest) -> None:
        """Complete a password reset using the OTP received by the user.

        Verifies the OTP hash and expiry, then replaces the password and
        clears the reset token so it cannot be reused.

        Raises:
            AuthenticationError: If the token is invalid, expired, or the
                                  tenant/user is not found.
        """

        tenant = await self.tenant_repo.get_by_code(data.tenant_code)
        if not tenant or not tenant.is_active:
            raise AuthenticationError("Invalid or expired reset token.")

        token_hash = hashlib.sha256(data.token.encode()).hexdigest()

        user = await self.user_repo.get_by_reset_token(
            token_hash=token_hash,
            tenant_id=tenant.id,
        )
        if not user:
            raise AuthenticationError("Invalid or expired reset token.")

        # Guard against replayed or time-expired tokens.
        now = datetime.now(timezone.utc)
        if user.password_reset_expires_at is None or user.password_reset_expires_at < now:
            raise AuthenticationError("Invalid or expired reset token.")

        await self.user_repo.update(
            id=user.id,
            tenant_id=tenant.id,
            password_hash=hash_password(data.new_password),
            password_reset_token=None,
            password_reset_expires_at=None,
        )
        await self.db.commit()
