# tests/test_password_flows.py
#
# Every "forgot password" / "reset password" / "change password" path:
#   Tenant   — AuthService.forgot_password / reset_password / change_password
#   Platform — PlatformAuthService.forgot_password / reset_password / change_password
#              + admin_reset_password (super-admin force-set)
#
# The raw OTP is never stored, so these tests set a known SHA-256 hash directly
# and then complete the flow with the matching plain OTP.

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio

from core.exceptions import AuthenticationError, ValidationError
from core.security import hash_password, verify_password
from models.platform_admin import PlatformAdmin
from repositories.platform_admin_repository import PlatformAdminRepository
from repositories.user_repository import UserRepository
from schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
)
from schemas.platform_auth import (
    PlatformChangePasswordRequest,
    PlatformForgotPasswordRequest,
    PlatformLoginRequest,
    PlatformResetPasswordRequest,
)
from services.auth_service import AuthService
from services.platform_auth_service import PlatformAuthService


def _hash(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


# ══════════════════════════════════════════════════════════════
# TENANT — /api/v1/auth/{forgot,reset,change}-password
# ══════════════════════════════════════════════════════════════

class TestTenantForgotReset:
    @pytest.mark.asyncio
    async def test_forgot_stores_hashed_otp_and_never_leaks(self, db, two_tenants):
        svc = AuthService(db)
        t = two_tenants["tenant_a"]
        u = two_tenants["user_a"]

        # unknown tenant / unknown email → silently returns None (no exception, no row change)
        await svc.forgot_password(ForgotPasswordRequest(tenant_code="NOPE_XX", email=u.email))
        await svc.forgot_password(ForgotPasswordRequest(tenant_code=t.tenant_code, email="ghost@nowhere.test"))

        # real account → a hash + expiry are written (the raw OTP is only emailed)
        await svc.forgot_password(ForgotPasswordRequest(tenant_code=t.tenant_code, email=u.email))
        fresh = await UserRepository(db).get_by_email(u.email, t.id)
        assert fresh.password_reset_token and len(fresh.password_reset_token) == 64
        assert fresh.password_reset_expires_at > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_reset_happy_path_then_single_use(self, db, two_tenants):
        svc = AuthService(db)
        t, u = two_tenants["tenant_a"], two_tenants["user_a"]
        otp = "424242"
        await UserRepository(db).update(
            id=u.id, tenant_id=t.id,
            password_reset_token=_hash(otp),
            password_reset_expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        await db.commit()

        # wrong code
        with pytest.raises(AuthenticationError):
            await svc.reset_password(ResetPasswordRequest(
                tenant_code=t.tenant_code, token="000000", new_password="whatever9"))

        # right code
        await svc.reset_password(ResetPasswordRequest(
            tenant_code=t.tenant_code, token=otp, new_password="BrandNewPass1"))

        fresh = await UserRepository(db).get_by_email(u.email, t.id)
        assert verify_password("BrandNewPass1", fresh.password_hash)
        assert fresh.password_reset_token is None                     # cleared

        # login works with the new password
        tok = await svc.login(LoginRequest(
            tenant_code=t.tenant_code, username=u.username, password="BrandNewPass1"))
        assert tok.access_token

        # replay is rejected
        with pytest.raises(AuthenticationError):
            await svc.reset_password(ResetPasswordRequest(
                tenant_code=t.tenant_code, token=otp, new_password="Replay123"))

    @pytest.mark.asyncio
    async def test_reset_expired_otp_rejected(self, db, two_tenants):
        svc = AuthService(db)
        t, u = two_tenants["tenant_a"], two_tenants["user_a"]
        otp = "999999"
        await UserRepository(db).update(
            id=u.id, tenant_id=t.id,
            password_reset_token=_hash(otp),
            password_reset_expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        await db.commit()
        with pytest.raises(AuthenticationError):
            await svc.reset_password(ResetPasswordRequest(
                tenant_code=t.tenant_code, token=otp, new_password="TooLate12"))

    @pytest.mark.asyncio
    async def test_change_password_requires_correct_current(self, db, two_tenants):
        svc = AuthService(db)
        t, u = two_tenants["tenant_a"], two_tenants["user_a"]
        with pytest.raises(ValidationError):
            await svc.change_password(
                user_id=u.id, tenant_id=t.id,
                data=ChangePasswordRequest(current_password="wrong", new_password="NewOne123"))
        await svc.change_password(
            user_id=u.id, tenant_id=t.id,
            data=ChangePasswordRequest(
                current_password=two_tenants["password"], new_password="NewOne123"))
        fresh = await UserRepository(db).get_by_email(u.email, t.id)
        assert verify_password("NewOne123", fresh.password_hash)


# ══════════════════════════════════════════════════════════════
# PLATFORM — /api/platform/auth/{forgot,reset,change}-password
# ══════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def platform_admin(db):
    admin = PlatformAdmin(
        id=uuid4(), email=f"pa_{uuid4().hex[:6]}@example.com", full_name="P Admin",
        password_hash=hash_password("OrigPass123"), is_active=True, is_super=True, role="owner",
    )
    db.add(admin)
    await db.flush()
    return admin


class TestPlatformForgotReset:
    @pytest.mark.asyncio
    async def test_forgot_stores_hash_and_no_enumeration(self, db, platform_admin):
        svc = PlatformAuthService(db)
        # unknown email → no exception, nothing written
        await svc.forgot_password(PlatformForgotPasswordRequest(email="ghost@example.com"))
        # real → hash + expiry written
        await svc.forgot_password(PlatformForgotPasswordRequest(email=platform_admin.email))
        fresh = await PlatformAdminRepository(db).get_by_id(platform_admin.id)
        assert fresh.password_reset_token and len(fresh.password_reset_token) == 64
        assert fresh.password_reset_expires_at > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_reset_happy_path_single_use_and_expiry(self, db, platform_admin):
        svc = PlatformAuthService(db)
        repo = PlatformAdminRepository(db)
        otp = "313131"

        await repo.update(
            platform_admin.id,
            password_reset_token=_hash(otp),
            password_reset_expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        await db.commit()

        with pytest.raises(AuthenticationError):
            await svc.reset_password(PlatformResetPasswordRequest(token="000000", new_password="whatever8"))

        await svc.reset_password(PlatformResetPasswordRequest(token=otp, new_password="FreshAdmin9"))
        fresh = await repo.get_by_id(platform_admin.id)
        assert verify_password("FreshAdmin9", fresh.password_hash)
        assert fresh.password_reset_token is None

        tok = await svc.login(PlatformLoginRequest(email=platform_admin.email, password="FreshAdmin9"))
        assert tok.access_token

        with pytest.raises(AuthenticationError):
            await svc.reset_password(PlatformResetPasswordRequest(token=otp, new_password="Replay88"))

        # expired token
        await repo.update(
            platform_admin.id,
            password_reset_token=_hash("777777"),
            password_reset_expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        await db.commit()
        with pytest.raises(AuthenticationError):
            await svc.reset_password(PlatformResetPasswordRequest(token="777777", new_password="TooLate99"))

    @pytest.mark.asyncio
    async def test_change_password_and_super_force_set(self, db, platform_admin):
        svc = PlatformAuthService(db)
        repo = PlatformAdminRepository(db)

        with pytest.raises(ValidationError):
            await svc.change_password(
                platform_admin.id,
                PlatformChangePasswordRequest(current_password="wrong", new_password="NextPass12"))

        await svc.change_password(
            platform_admin.id,
            PlatformChangePasswordRequest(current_password="OrigPass123", new_password="NextPass12"))
        assert verify_password("NextPass12", (await repo.get_by_id(platform_admin.id)).password_hash)

        # super-admin force-set (no current password needed)
        await svc.admin_reset_password(platform_admin.id, "ForcedPass34")
        assert verify_password("ForcedPass34", (await repo.get_by_id(platform_admin.id)).password_hash)
