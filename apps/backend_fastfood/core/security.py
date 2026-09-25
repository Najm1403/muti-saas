# core/security.py
#
# Security primitives only — no routes, no DB queries, no business logic.
# Answers: how to hash a password, verify it, create a JWT, decode a JWT.

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from core.config import settings
from core.exceptions import ValidationError


# ============================================================
# PASSWORD HASHING
# ============================================================

# Explicitly use bcrypt — pwdlib[bcrypt] is installed, not argon2.
# PasswordHash.recommended() would try argon2 first and fail.
password_hasher = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    """Hash a plain-text password using the recommended algorithm (bcrypt).
    Store the returned hash — never the original password."""
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored hash, False otherwise."""
    return password_hasher.verify(plain_password, hashed_password)


# ============================================================
# JWT
# ============================================================

def create_access_token(user_id: UUID, tenant_id: UUID) -> str:
    """Create a short-lived JWT access token (default: 60 min).

    Payload includes sub (user_id), tenant_id, token type, and expiry.
    tenant_id is embedded so every authenticated request carries
    the tenant scope without an extra DB lookup.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: UUID, tenant_id: UUID) -> str:
    """Create a long-lived JWT refresh token (default: 30 days).

    Used only to issue a new access token — not to authorise API actions.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_platform_access_token(admin_id: UUID) -> str:
    """Create a short-lived JWT access token for a platform admin (default: 60 min).

    Deliberately has NO tenant_id — platform admins operate across all tenants.
    Token type is "platform_access" so tenant endpoints reject it outright.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(admin_id),
        "type": "platform_access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_platform_step_up_token(
    admin_id: UUID, action: str, template_id: UUID | None, minutes: int = 5
) -> str:
    """Create a short-lived, single-action-scoped JWT proving the platform admin
    just re-entered their own password (POST /api/platform/auth/step-up).

    Scoped to `action` + `template_id` (not just the admin) so a token minted to
    confirm deleting template A can't be replayed against template B, or reused
    for a different guarded action, within its short window. Required on top of
    (never instead of) the `can_manage_business_templates` capability check —
    that flag controls eligibility, this token proves fresh intent.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(admin_id),
        "type": "platform_step_up",
        "action": action,
        "template_id": str(template_id) if template_id else None,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_platform_refresh_token(admin_id: UUID) -> str:
    """Create a long-lived refresh token for a platform admin (default: 30 days)."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(admin_id),
        "type": "platform_refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_device_token(device_id: UUID, branch_id: UUID, tenant_id: UUID) -> str:
    """Create a long-lived JWT for an activated POS device (default: 30 days).

    Carried by the device in all POS API requests. Scopes the device to a
    single branch and tenant — the POS cannot access data outside its branch.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(device_id),
        "device_id": str(device_id),
        "branch_id": str(branch_id),
        "tenant_id": str(tenant_id),
        "type": "device",
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_cashier_token(
    user_id: UUID, device_id: UUID, branch_id: UUID, tenant_id: UUID
) -> str:
    """Create a short-lived JWT for a cashier logged in on a POS device (default: 12 h).

    The cashier re-authenticates at the start of every shift. Carrying device_id
    and branch_id in the token means every sale is automatically scoped without
    extra DB lookups.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "user_id": str(user_id),
        "device_id": str(device_id),
        "branch_id": str(branch_id),
        "tenant_id": str(tenant_id),
        "type": "cashier",
        "iat": now,
        "exp": now + timedelta(hours=12),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Returns the payload dict on success.

    Raises core.exceptions.ValidationError if the token is expired,
    tampered with, or otherwise invalid — keeping library exceptions
    out of the service and route layers.
    """
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.InvalidTokenError as exc:
        raise ValidationError(str(exc)) from exc


def create_offline_proof(user_id: UUID, device_id: UUID, branch_id: UUID, tenant_id: UUID) -> str:
    """Non-authentication proof of the cashier's authorized offline sale window."""
    now = datetime.now(timezone.utc)
    return jwt.encode({"type": "offline_sale_origin", "user_id": str(user_id),
        "device_id": str(device_id), "branch_id": str(branch_id), "tenant_id": str(tenant_id),
        "iat": int(now.timestamp()), "sale_until": int((now + timedelta(hours=12)).timestamp())},
        settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
