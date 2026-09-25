# api/platform/platform_admins.py
#
# CRUD for platform admin accounts — visible only to platform admins.
#
# "Platform admins" (this file) are the SaaS owner and their team who
# log in to the SuperAdmin dashboard.  They are stored in platform_admins
# and carry JWTs with type="platform_access".
#
# "Tenant users" are managed by tenant admins via api/v1/users.py and
# are stored in the users table with a tenant_id FK.
#
# Prefix: /api/platform/admins

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import CurrentPlatformAdmin, get_current_platform_admin
from core.exceptions import ConflictError, ForbiddenError, NotFoundError
from core.security import hash_password
from db.session import get_db
from repositories.platform_admin_repository import PlatformAdminRepository
from schemas.common import MessageResponse
from services.platform_auth_service import PlatformAuthService
from schemas.platform_auth import (
    PlatformAdminCreate,
    PlatformAdminResponse,
    PlatformAdminUpdate,
)

router = APIRouter(prefix="/admins", tags=["Platform · Admins"])


def _repo(db: AsyncSession = Depends(get_db)) -> PlatformAdminRepository:
    return PlatformAdminRepository(db)


def _require_super(current: CurrentPlatformAdmin) -> CurrentPlatformAdmin:
    """Guard: only super-admins (owner tier) may create or deactivate other platform admins."""
    if not current.is_super:
        raise ForbiddenError("Only super-admins can manage platform admin accounts.")
    return current


def _normalise_role(role: str | None, is_super: bool | None) -> tuple[str, bool]:
    """Resolve the (role, is_super) pair from whatever the caller supplied.

    `role="owner"` and `is_super=True` are the same thing; the role string wins
    when both are present, else the legacy flag is honoured.
    """
    if role:
        role = role.lower()
    elif is_super is not None:
        role = "owner" if is_super else "manager"
    else:
        role = "manager"
    return role, (role == "owner")


# ----------------------------------------------------------------
# LIST
# ----------------------------------------------------------------

@router.get(
    "",                         # /api/platform/admins  (no trailing slash)
    response_model=list[PlatformAdminResponse],
    status_code=status.HTTP_200_OK,
    summary="List platform admins",
    description="Returns all platform admin accounts. Any platform admin can view this list.",
)
@router.get(
    "/",                        # /api/platform/admins/ (trailing slash alias)
    response_model=list[PlatformAdminResponse],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def list_platform_admins(
    skip: int = 0,
    limit: int = 100,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    repo: PlatformAdminRepository = Depends(_repo),
) -> list[PlatformAdminResponse]:
    admins = await repo.list(skip=skip, limit=limit)
    return [PlatformAdminResponse.model_validate(a) for a in admins]


# ----------------------------------------------------------------
# CREATE
# ----------------------------------------------------------------

@router.post(
    "/",
    response_model=PlatformAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create platform admin",
    description="Create a new platform admin account. Requires super-admin privileges.",
)
async def create_platform_admin(
    data: PlatformAdminCreate,
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    repo: PlatformAdminRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db),
) -> PlatformAdminResponse:
    _require_super(current)

    if await repo.get_by_email(str(data.email)):
        raise ConflictError(f"Email '{data.email}' is already registered.")

    role, is_super = _normalise_role(data.role, data.is_super)
    admin = await repo.create(
        email=str(data.email),
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        is_super=is_super,
        role=role,
    )
    await db.commit()
    await db.refresh(admin)
    return PlatformAdminResponse.model_validate(admin)


# ----------------------------------------------------------------
# GET
# ----------------------------------------------------------------

@router.get(
    "/{id}",
    response_model=PlatformAdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Get platform admin",
)
async def get_platform_admin(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    repo: PlatformAdminRepository = Depends(_repo),
) -> PlatformAdminResponse:
    admin = await repo.get_by_id(id)
    if not admin:
        raise NotFoundError("Platform admin not found.")
    return PlatformAdminResponse.model_validate(admin)


# ----------------------------------------------------------------
# UPDATE
# ----------------------------------------------------------------

@router.patch(
    "/{id}",
    response_model=PlatformAdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Update platform admin",
    description=(
        "Update full_name, is_super, or is_active. "
        "Changing is_super or is_active requires super-admin privileges."
    ),
)
async def update_platform_admin(
    id: UUID,
    data: PlatformAdminUpdate,
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    repo: PlatformAdminRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db),
) -> PlatformAdminResponse:
    # Super-only fields
    if (
        data.is_super is not None
        or data.is_active is not None
        or data.role is not None
        or data.can_manage_business_templates is not None
    ):
        _require_super(current)

    admin = await repo.get_by_id(id)
    if not admin:
        raise NotFoundError("Platform admin not found.")

    fields = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    # Keep role <-> is_super consistent whenever either is being changed.
    if "role" in fields or "is_super" in fields:
        role, is_super = _normalise_role(fields.get("role"), fields.get("is_super"))
        fields["role"], fields["is_super"] = role, is_super

    updated = await repo.update(id, **fields)
    await db.commit()
    await db.refresh(updated)
    return PlatformAdminResponse.model_validate(updated)


# ----------------------------------------------------------------
# DEACTIVATE / ACTIVATE
# ----------------------------------------------------------------

@router.post(
    "/{id}/deactivate",
    response_model=PlatformAdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate platform admin",
    description="Block the admin from logging in. Requires super-admin.",
)
async def deactivate_platform_admin(
    id: UUID,
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    repo: PlatformAdminRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db),
) -> PlatformAdminResponse:
    _require_super(current)
    admin = await repo.get_by_id(id)
    if not admin:
        raise NotFoundError("Platform admin not found.")
    if str(id) == str(current.admin_id):
        raise ForbiddenError("You cannot deactivate your own account.")
    updated = await repo.update(id, is_active=False)
    await db.commit()
    await db.refresh(updated)
    return PlatformAdminResponse.model_validate(updated)


@router.post(
    "/{id}/activate",
    response_model=PlatformAdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate platform admin",
    description="Re-enable a deactivated admin account. Requires super-admin.",
)
async def activate_platform_admin(
    id: UUID,
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    repo: PlatformAdminRepository = Depends(_repo),
    db: AsyncSession = Depends(get_db),
) -> PlatformAdminResponse:
    _require_super(current)
    admin = await repo.get_by_id(id)
    if not admin:
        raise NotFoundError("Platform admin not found.")
    updated = await repo.update(id, is_active=True)
    await db.commit()
    await db.refresh(updated)
    return PlatformAdminResponse.model_validate(updated)


# ----------------------------------------------------------------
# RESET PASSWORD  (super-admin only)
# ----------------------------------------------------------------

@router.post(
    "/{id}/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset platform admin password",
    description=(
        "Force-set a new password for any platform admin without needing the current "
        "password. Requires super-admin. Use this to unlock a locked-out colleague. "
        "new_password must be at least 8 characters."
    ),
)
async def reset_platform_admin_password(
    id: UUID,
    new_password: str = Body(..., min_length=8),
    current: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    _require_super(current)
    await PlatformAuthService(db).admin_reset_password(
        target_admin_id=id,
        new_password=new_password,
    )
    return MessageResponse(message="Platform admin password reset successfully.")
