# api/platform/dependencies.py
#
# Auth dependency for platform-only routes.
# Accepts ONLY "platform_access" tokens — tenant tokens are rejected.

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.exceptions import AuthenticationError, ForbiddenError, ValidationError
from core.security import decode_token
from models.platform_admin import PlatformAdmin
from repositories.platform_admin_repository import PlatformAdminRepository
from db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

_bearer = HTTPBearer(auto_error=False)

# Coarse platform access tiers (platform_admins.role).
PLATFORM_ROLES = ("owner", "manager", "viewer")
_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@dataclass(frozen=True)
class CurrentPlatformAdmin:
    """
    Decoded identity attached to every authenticated platform request.
    admin_id comes from the JWT; is_super / role / can_manage_business_templates
    are loaded from DB once per request.
    """

    admin_id: UUID
    is_super: bool
    role: str = "manager"
    can_manage_business_templates: bool = False


async def get_current_platform_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> CurrentPlatformAdmin:
    """
    Validates a platform_access Bearer token and returns the admin's identity.

    Raises AuthenticationError (→ 401) if:
        - No Authorization header is present.
        - Token is expired, tampered, or malformed.
        - Token is not type "platform_access" (tenant tokens are rejected here).
        - Admin no longer exists or is inactive.
    """

    if not credentials:
        raise AuthenticationError("Authentication token is missing.")

    try:
        payload = decode_token(credentials.credentials)
    except ValidationError:
        raise AuthenticationError("Invalid or expired token.")

    if payload.get("type") != "platform_access":
        raise AuthenticationError("A valid platform access token is required.")

    try:
        admin_id = UUID(str(payload["sub"]))
    except (KeyError, ValueError, TypeError):
        raise AuthenticationError("Token payload is malformed.")

    admin = await PlatformAdminRepository(db).get_by_id(admin_id)
    if not admin:
        raise AuthenticationError("Platform admin not found.")
    if not admin.is_active:
        raise ForbiddenError("Platform admin account is inactive.")

    from core.auth_limits import check_session_age
    await check_session_age(db, payload)
    role = (getattr(admin, "role", None) or ("owner" if admin.is_super else "manager")).lower()
    return CurrentPlatformAdmin(
        admin_id=admin_id,
        is_super=admin.is_super,
        role=role,
        can_manage_business_templates=bool(getattr(admin, "can_manage_business_templates", False)),
    )


def require_super(current: CurrentPlatformAdmin = Depends(get_current_platform_admin)) -> CurrentPlatformAdmin:
    """Additional guard — restricts route to super admins (== owner tier)."""
    if not current.is_super:
        raise ForbiddenError("Super admin access required.")
    return current


def require_business_template_manage(
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
) -> CurrentPlatformAdmin:
    """Restricts Business Template delete / update to admins explicitly trusted
    with it — an owner always qualifies; a manager only if granted
    `can_manage_business_templates` (api/platform/platform_admins.py, super-only
    to set). This is eligibility only — the actual delete/modules-change route
    also requires a fresh password step-up on top (require_step_up below)."""
    if not (current.is_super or current.can_manage_business_templates):
        raise ForbiddenError(
            "You don't have permission to manage Business Templates. "
            "Ask an owner to grant it.",
            code="BUSINESS_TEMPLATE_MANAGE_REQUIRED",
        )
    return current


def require_step_up(action: str):
    """Route dependency factory — 403s with code STEP_UP_REQUIRED unless the
    request carries a valid `X-Step-Up-Token` header minted (within the last
    few minutes) by THIS SAME admin for THIS SAME action, via
    POST /api/platform/auth/step-up. Scoped to `template_id` from the path so a
    token confirmed for one template can't be replayed against another.

    Used directly (via Depends) on the always-guarded delete route. The
    conditionally-guarded update route instead uses the sibling
    `optional_step_up` below and decides for itself, since whether a step-up is
    even required there depends on what the request body actually changes.
    """

    async def _dep(
        id: UUID,
        request: Request,
        current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    ) -> CurrentPlatformAdmin:
        # Parameter named `id` (not `template_id`) so FastAPI binds it to this
        # route's own `{id}` path segment — see api/platform/business_templates.py.
        if not _valid_step_up(request, current, action, id):
            raise ForbiddenError(
                "Re-enter your password to confirm this action.",
                code="STEP_UP_REQUIRED",
            )
        return current

    return _dep


async def optional_step_up(
    id: UUID,
    request: Request,
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
) -> bool:
    """Like require_step_up, but returns True/False instead of raising — for
    routes where a step-up is only conditionally required (the caller decides,
    based on what's actually changing, whether the missing/invalid case is an
    error). Used by update_business_template for the "only if modules.hidden
    changed" rule."""
    return _valid_step_up(request, current, "update_business_template_modules", id)


def _valid_step_up(
    request: Request, current: CurrentPlatformAdmin, action: str, template_id: UUID
) -> bool:
    token = request.headers.get("X-Step-Up-Token")
    if not token:
        return False
    try:
        payload = decode_token(token)
    except ValidationError:
        return False
    if payload.get("type") != "platform_step_up":
        return False
    if payload.get("action") != action:
        return False
    if payload.get("template_id") != str(template_id):
        return False
    try:
        return UUID(str(payload["sub"])) == current.admin_id
    except (KeyError, ValueError, TypeError):
        return False


async def block_readonly_writes(
    request: Request,
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
) -> CurrentPlatformAdmin:
    """Router-level guard: a ``viewer`` platform admin may read but never write.

    Applied to every platform router except auth (so a viewer can still log in
    and change their own password). ``owner`` and ``manager`` pass through;
    finer owner-only restrictions stay on ``require_super``.
    """
    if request.method.upper() in _WRITE_METHODS and current.role == "viewer":
        raise ForbiddenError(
            "This platform account is read-only. Ask an owner to change your role.",
            code="ROLE_READ_ONLY",
        )
    return current
