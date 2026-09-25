# api/dependencies.py
#
# FastAPI dependency functions shared across all route modules.
# Import from here — never duplicate auth logic in individual routes.

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import AuthenticationError, ForbiddenError, NotFoundError, ValidationError
from core.security import decode_token
from db.session import get_db

# HTTPBearer reads the Authorization: Bearer <token> header.
# auto_error=False lets us return a clean AuthenticationError instead of
# FastAPI's default 403 when the header is absent.
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    """
    Decoded JWT payload attached to every authenticated request.

    Both fields are extracted from the token — no DB call is made.
    The service layer uses these to scope all queries to the correct tenant.
    """

    user_id: UUID
    tenant_id: UUID


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """
    FastAPI dependency that validates the Bearer token and returns the caller's identity.

    Used as:
        current_user: CurrentUser = Depends(get_current_user)

    Raises AuthenticationError (→ HTTP 401) if:
        - No Authorization header is present
        - The token is expired, tampered with, or malformed
        - The token is not an access token (e.g. a refresh token was sent)
    """

    if not credentials:
        raise AuthenticationError("Authentication token is missing.")

    try:
        payload = decode_token(credentials.credentials)
    except ValidationError:
        raise AuthenticationError("Invalid or expired token.")

    # Reject refresh tokens — they are only valid on the /auth/refresh endpoint.
    if payload.get("type") != "access":
        raise AuthenticationError("A valid access token is required.")

    try:
        user_id = UUID(str(payload["sub"]))
        tenant_id = UUID(str(payload["tenant_id"]))
    except (KeyError, ValueError, TypeError):
        raise AuthenticationError("Token payload is malformed.")

    from models.user import User
    from models.tenant import Tenant
    active = await db.scalar(select(User.id).join(Tenant, User.tenant_id == Tenant.id).where(
        User.id == user_id, User.tenant_id == tenant_id,
        User.is_active.is_(True), User.deleted_at.is_(None),
        Tenant.is_active.is_(True), Tenant.deleted_at.is_(None),
    ))
    if active is None:
        raise AuthenticationError("Account is inactive or unavailable.")
    from core.auth_limits import check_session_age
    await check_session_age(db, payload)
    return CurrentUser(user_id=user_id, tenant_id=tenant_id)


# ================================================================
# PERMISSIONS  (role → permission, with an admin/owner/manager bypass)
# ================================================================

_ADMIN_ROLE_NAMES = {"admin", "owner", "manager", "superadmin", "super admin"}


async def get_user_permissions(
    db: AsyncSession, user_id: UUID, tenant_id: UUID
) -> set[str]:
    """Effective permission codes for a tenant user.

    Returns ``{"*"}`` (all permissions) when the user holds a tenant-owned
    role named Admin / Owner / Manager — the shop's operators
    are never locked out of their own dashboard. Otherwise the concrete set of
    ``permissions.code`` values granted through the user's active roles.
    """
    from models.permission import Permission
    from models.role import Role
    from models.role_permission import RolePermission
    from models.user import User
    from models.user_role import UserRole

    role_names = (
        await db.execute(
            select(Role.name)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user_id,
                UserRole.deleted_at.is_(None),
                Role.tenant_id == tenant_id,
                Role.deleted_at.is_(None),
                Role.is_active.is_(True),
            )
        )
    ).scalars().all()
    if any((n or "").strip().lower() in _ADMIN_ROLE_NAMES for n in role_names):
        return {"*"}

    codes = set((
        await db.execute(
            select(Permission.code)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user_id,
                UserRole.deleted_at.is_(None),
                RolePermission.deleted_at.is_(None),
                Role.tenant_id == tenant_id,
                Role.deleted_at.is_(None),
                Role.is_active.is_(True),
                Permission.deleted_at.is_(None),
                Permission.is_active.is_(True),
            )
        )
    ).scalars().all())

    from models.user_permission import UserPermission
    overrides = (await db.execute(
        select(Permission.code, UserPermission.is_allowed)
        .join(UserPermission, Permission.id == UserPermission.permission_id)
        .where(
            UserPermission.user_id == user_id,
            UserPermission.deleted_at.is_(None),
            Permission.deleted_at.is_(None),
            Permission.is_active.is_(True),
        )
    )).all()
    for code, is_allowed in overrides:
        if is_allowed:
            codes.add(code)
        else:
            codes.discard(code)
    return codes


async def require_tenant_admin(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """Allow security administration only to an Admin/Owner/Super Admin role.

    This deliberately does not rely on ``roles.manage`` or the Manager wildcard;
    a custom role must not be able to grant itself additional access.
    """
    from models.role import Role
    from models.user_role import UserRole

    names = (await db.execute(
        select(Role.name)
        .join(UserRole, Role.id == UserRole.role_id)
        .where(
            UserRole.user_id == current_user.user_id,
            UserRole.deleted_at.is_(None),
            Role.tenant_id == current_user.tenant_id,
            Role.deleted_at.is_(None),
            Role.is_active.is_(True),
        )
    )).scalars().all()
    allowed = {"admin", "owner", "superadmin", "super admin"}
    if not any((name or "").strip().lower() in allowed for name in names):
        raise ForbiddenError("Only a tenant Super Admin or Admin can edit roles and permissions.")
    return current_user


def require_permission(code: str):
    """Route dependency factory — 403 unless the caller holds ``code``.

    Usage:  ``_: CurrentUser = Depends(require_permission("expenses.manage"))``
    """

    async def _dep(
        current_user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> CurrentUser:
        perms = await get_user_permissions(db, current_user.user_id, current_user.tenant_id)
        if "*" not in perms and code not in perms:
            raise ForbiddenError(
                f"Requires the '{code}' permission.", code="PERMISSION_DENIED"
            )
        return current_user

    return _dep


async def tenant_enabled_modules(db: AsyncSession, tenant_id: UUID) -> set[str]:
    """The set of module keys this tenant may use (mandatory ones always in).

    Driven by the tenant's Business Template config (``config.modules.hidden``
    — see services/business_policy.py) rather than any per-tenant override;
    every tenant on the same template sees the same modules. Missing/empty
    hidden list → every module (the default).
    """
    from core.modules import effective_modules_from_hidden
    from services.business_policy import load_business_policy

    policy = await load_business_policy(db, tenant_id)
    hidden = policy.get("modules", {}).get("hidden", [])
    return effective_modules_from_hidden(hidden)


def require_module(key: str):
    """Route dependency factory — 403 unless the tenant's plan includes ``key``.

    The platform controls this per tenant (industry templates). Applied to the
    optional tenant-dashboard routers so a disabled module is unreachable, not
    just hidden in the sidebar.
    """

    async def _dep(
        request: Request,
        current_user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> CurrentUser:
        from core.modules import MODULE_LABEL

        if key not in await tenant_enabled_modules(db, current_user.tenant_id):
            raise ForbiddenError(
                f"The '{MODULE_LABEL.get(key, key)}' module is not enabled for your account.",
                code="MODULE_DISABLED",
            )
        from api.branch_access import enforce_branch_request
        await enforce_branch_request(request, db, current_user, key)
        if request.method in {"GET", "HEAD"}:
            # Module availability is a tenant entitlement, not a user grant.
            # Enforce read access here for routers that do not declare their
            # own view dependency (an explicit dependency may enforce more).
            view_scope = {
                "menu": "categories" if "/categories" in request.scope.get("path", "") else "products",
                "promotions": "products", "deals": "products",
                "kitchen": "sales", "activity": "roles",
                "inventory": "inventory",
            }.get(key, key)
            view_code = "roles.manage" if key in {"activity", "roles"} else f"{view_scope}.view"
            await require_permission(view_code)(current_user, db)
        elif request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            scope = {"menu": "products", "promotions": "products", "deals": "products",
                     "kitchen": "products", "activity": "settings"}.get(key, key)
            if key == "sales":
                code = "sales.create" if request.method == "POST" and "/refunds" not in request.url.path else "sales.cancel"
            else:
                code = scope + ".manage"
            await require_permission(code)(current_user, db)
        return current_user

    return _dep


def require_any_module(*keys: str):
    """Authorize a read resource shared by multiple optional modules."""
    if not keys:
        raise ValueError("At least one module key is required.")

    async def _dep(
        current_user: CurrentUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> CurrentUser:
        from core.modules import MODULE_LABEL

        enabled = await tenant_enabled_modules(db, current_user.tenant_id)
        available = [key for key in keys if key in enabled]
        if not available:
            labels = ", ".join(MODULE_LABEL.get(key, key) for key in keys)
            raise ForbiddenError(
                f"None of the required modules ({labels}) is enabled for your account.",
                code="MODULE_DISABLED",
            )

        permissions = await get_user_permissions(db, current_user.user_id, current_user.tenant_id)
        view_codes = {"menu": "products.view", "inventory": "inventory.view"}
        if "*" not in permissions and not any(
            view_codes.get(key, f"{key}.view") in permissions for key in available
        ):
            raise ForbiddenError(
                "Requires read access to one of the enabled modules.",
                code="PERMISSION_DENIED",
            )
        return current_user

    return _dep


async def get_current_business_id(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """Resolves the caller's one Business (spec A2) — endpoints that used to
    require a restaurant_id/business_id query param no longer need one; the
    tenant has exactly one Business so it can always be looked up server-side."""
    from models.business import Business

    business_id = await db.scalar(
        select(Business.id).where(
            Business.tenant_id == current_user.tenant_id,
            Business.deleted_at.is_(None),
        )
    )
    if business_id is None:
        raise NotFoundError("No business is set up for this tenant.")
    return business_id


@dataclass(frozen=True)
class CurrentDevice:
    """Identity extracted from a device JWT (type='device')."""

    device_id: UUID
    branch_id: UUID
    tenant_id: UUID


@dataclass(frozen=True)
class CurrentCashier:
    """Identity extracted from a cashier JWT (type='cashier').

    Carries enough context to scope every POS operation without extra DB lookups.
    """

    user_id: UUID
    device_id: UUID
    branch_id: UUID
    tenant_id: UUID


async def get_current_device(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentDevice:
    """Dependency for POS endpoints that only need the device identity."""
    if not credentials:
        raise AuthenticationError(
            "Device token is missing.", code="DEVICE_TOKEN_INVALID"
        )
    try:
        payload = decode_token(credentials.credentials)
    except ValidationError:
        raise AuthenticationError(
            "Invalid or expired device token.", code="DEVICE_TOKEN_INVALID"
        )
    if payload.get("type") != "device":
        raise AuthenticationError(
            "A valid device token is required.", code="DEVICE_TOKEN_INVALID"
        )
    try:
        return CurrentDevice(
            device_id=UUID(str(payload["device_id"])),
            branch_id=UUID(str(payload["branch_id"])),
            tenant_id=UUID(str(payload["tenant_id"])),
        )
    except (KeyError, ValueError, TypeError):
        raise AuthenticationError(
            "Device token payload is malformed.", code="DEVICE_TOKEN_INVALID"
        )


async def get_current_cashier(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> CurrentCashier:
    """Dependency for POS endpoints that require an active cashier session."""
    if not credentials:
        raise AuthenticationError("Cashier token is missing.")
    try:
        payload = decode_token(credentials.credentials)
    except ValidationError:
        raise AuthenticationError("Invalid or expired cashier token.")
    if payload.get("type") != "cashier":
        raise AuthenticationError("A valid cashier token is required.")
    from core.auth_limits import check_session_age
    await check_session_age(db, payload)
    try:
        return CurrentCashier(
            user_id=UUID(str(payload["user_id"])),
            device_id=UUID(str(payload["device_id"])),
            branch_id=UUID(str(payload["branch_id"])),
            tenant_id=UUID(str(payload["tenant_id"])),
        )
    except (KeyError, ValueError, TypeError):
        raise AuthenticationError("Cashier token payload is malformed.")
