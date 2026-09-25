# api/v1/users.py
#
# Tenant user management routes — tenant scoped.
#
# Position in hierarchy:
#   Tenant → User
#
# A tenant admin uses these endpoints to create and manage cashier/manager accounts.
# The current user's tenant_id (from JWT) scopes every operation — users can only
# manage accounts within their own tenant.
#
# Password management:
#   - POST /users/          accepts plain-text password (hashed by UserService).
#   - POST /users/{id}/change-password  requires current password for verification.
#   - Admin password reset is done via the auth forgot-password flow, not here.
#
# Connected services / dependencies:
#   - services/user_service.py  — UserService (create, get, list, update, delete)
#   - api/dependencies.py       — get_current_user
#   - db/session.py             — get_db
#   - schemas/user.py           — UserCreate, UserUpdate, UserResponse
#   - schemas/common.py         — MessageResponse
#
# Prefix: /api/v1/users

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user, require_permission, require_tenant_admin
from db.session import get_db
from schemas.branch_assignment import BranchAssignmentResponse, BranchAssignmentUpdate
from schemas.common import MessageResponse
from schemas.permission import UserPermissionState, UserPermissionsUpdate
from schemas.role import RoleResponse, UserRoleAssign
from schemas.user import UserCreate, UserResponse, UserSetPin, UserUpdate
from services.role_service import RoleService
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def _svc(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency that instantiates UserService with the request's DB session."""
    return UserService(db)


def _role_svc(db: AsyncSession = Depends(get_db)) -> RoleService:
    return RoleService(db)


@router.get(
    "/",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List users",
    description=(
        "Returns all active users within the current tenant, with pagination. "
        "Soft-deleted users are excluded."
    ),
)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    svc: UserService = Depends(_svc),
) -> list[UserResponse]:
    return await svc.list(
        tenant_id=current_user.tenant_id, skip=skip, limit=limit
    )


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    description=(
        "Creates a new user account within the current tenant. "
        "username must be unique within the tenant (two tenants may share usernames). "
        "password is hashed server-side — never stored in plain text. "
        "Returns 409 if the username is already taken."
    ),
)
async def create_user(
    data: UserCreate,
    current_user: CurrentUser = Depends(require_permission("users.manage")),
    svc: UserService = Depends(_svc),
) -> UserResponse:
    return await svc.create(tenant_id=current_user.tenant_id, data=data)


@router.get(
    "/{id}/branches",
    response_model=BranchAssignmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user branch assignment",
)
async def get_user_branches(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: UserService = Depends(_svc),
) -> BranchAssignmentResponse:
    return await svc.get_branch_assignment(user_id=id, tenant_id=current_user.tenant_id)


@router.put(
    "/{id}/branches",
    response_model=BranchAssignmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Set user branch assignment",
)
async def set_user_branches(
    id: UUID,
    data: BranchAssignmentUpdate,
    current_user: CurrentUser = Depends(require_permission("users.manage")),
    svc: UserService = Depends(_svc),
) -> BranchAssignmentResponse:
    return await svc.set_branch_assignment(
        user_id=id,
        tenant_id=current_user.tenant_id,
        all_branches=data.all_branches,
        branch_ids=data.branch_ids,
    )


@router.get(
    "/{id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user",
    description="Returns a single user. Returns 404 if they belong to a different tenant.",
)
async def get_user(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: UserService = Depends(_svc),
) -> UserResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch(
    "/{id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user",
    description=(
        "Partially update a user's profile (username, full_name, email, is_active). "
        "Returns 409 if the new username is already taken within the tenant. "
        "To set a new password use POST /{id}/reset-password."
    ),
)
async def update_user(
    id: UUID,
    data: UserUpdate,
    current_user: CurrentUser = Depends(require_permission("users.manage")),
    svc: UserService = Depends(_svc),
) -> UserResponse:
    return await svc.update(id=id, tenant_id=current_user.tenant_id, data=data)


@router.post(
    "/{id}/activate",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate user",
    description="Re-enable a deactivated user account so they can log in again.",
)
async def activate_user(
    id: UUID,
    current_user: CurrentUser = Depends(require_permission("users.manage")),
    svc: UserService = Depends(_svc),
) -> UserResponse:
    return await svc.activate(id=id, tenant_id=current_user.tenant_id)


@router.post(
    "/{id}/deactivate",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate user",
    description=(
        "Disable a user account. The account is not deleted — it can be reactivated. "
        "A deactivated user cannot log in."
    ),
)
async def deactivate_user(
    id: UUID,
    current_user: CurrentUser = Depends(require_permission("users.manage")),
    svc: UserService = Depends(_svc),
) -> UserResponse:
    return await svc.deactivate(id=id, tenant_id=current_user.tenant_id)


@router.post(
    "/{id}/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Admin reset password",
    description=(
        "Set a new password for any user within the tenant without needing the "
        "current password. Intended for admins who need to unlock a forgotten "
        "or compromised account. new_password must be at least 6 characters."
    ),
)
async def reset_password(
    id: UUID,
    new_password: str = Body(..., min_length=6),
    current_user: CurrentUser = Depends(require_permission("users.manage")),
    svc: UserService = Depends(_svc),
) -> MessageResponse:
    await svc.admin_reset_password(
        id=id,
        tenant_id=current_user.tenant_id,
        new_password=new_password,
    )
    return MessageResponse(message="Password reset successfully.")


@router.post(
    "/{id}/set-pin",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Set staff POS PIN",
    description=(
        "Set or replace a user's 4-6 digit quick sign-in PIN for the POS tablet "
        "staff picker. Admin action — no current PIN required."
    ),
)
async def set_pin(
    id: UUID,
    data: UserSetPin,
    current_user: CurrentUser = Depends(require_permission("users.manage")),
    svc: UserService = Depends(_svc),
) -> UserResponse:
    return await svc.set_pin(
        id=id,
        tenant_id=current_user.tenant_id,
        pin=data.pin,
    )


@router.post(
    "/{id}/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change own password",
    description=(
        "Change a user's password. current_password must match the stored hash. "
        "new_password must be at least 6 characters. "
        "Returns 401 if current_password is incorrect. "
        "Use POST /{id}/reset-password if you need to reset without the current password."
    ),
)
async def change_password(
    id: UUID,
    current_password: str = Body(..., min_length=1),
    new_password: str = Body(..., min_length=6),
    current_user: CurrentUser = Depends(get_current_user),
    svc: UserService = Depends(_svc),
) -> MessageResponse:
    await svc.change_password(
        id=id,
        tenant_id=current_user.tenant_id,
        current_password=current_password,
        new_password=new_password,
    )
    return MessageResponse(message="Password changed successfully.")


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete user",
    description=(
        "Soft-deletes the user account (sets deleted_at). "
        "The user's historical sales records are preserved. "
        "A deleted user cannot log in."
    ),
)
async def delete_user(
    id: UUID,
    current_user: CurrentUser = Depends(require_permission("users.manage")),
    svc: UserService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="User deleted.")


# ── User-Role assignment ──────────────────────────────────────────

@router.get(
    "/{id}/roles",
    response_model=list[RoleResponse],
    status_code=status.HTTP_200_OK,
    summary="List user roles",
)
async def list_user_roles(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: RoleService = Depends(_role_svc),
) -> list[RoleResponse]:
    return await svc.list_user_roles(user_id=id, tenant_id=current_user.tenant_id)


@router.post(
    "/{id}/roles",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign role to user",
)
async def assign_user_role(
    id: UUID,
    data: UserRoleAssign,
    current_user: CurrentUser = Depends(require_tenant_admin),
    svc: RoleService = Depends(_role_svc),
) -> MessageResponse:
    await svc.assign_user_role(user_id=id, role_id=data.role_id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Role assigned.")


@router.delete(
    "/{id}/roles/{role_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove role from user",
)
async def remove_user_role(
    id: UUID,
    role_id: UUID,
    current_user: CurrentUser = Depends(require_tenant_admin),
    svc: RoleService = Depends(_role_svc),
) -> MessageResponse:
    await svc.remove_user_role(user_id=id, role_id=role_id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Role removed.")


@router.get(
    "/{id}/permissions",
    response_model=list[UserPermissionState],
    summary="List a user's effective permissions",
)
async def list_user_permissions(
    id: UUID,
    current_user: CurrentUser = Depends(require_tenant_admin),
    svc: RoleService = Depends(_role_svc),
) -> list[UserPermissionState]:
    return await svc.list_user_permissions(id, current_user.tenant_id)


@router.put(
    "/{id}/permissions",
    response_model=list[UserPermissionState],
    summary="Replace a user's effective permissions",
)
async def replace_user_permissions(
    id: UUID,
    data: UserPermissionsUpdate,
    current_user: CurrentUser = Depends(require_tenant_admin),
    svc: RoleService = Depends(_role_svc),
) -> list[UserPermissionState]:
    return await svc.replace_user_permissions(
        id, current_user.tenant_id, data.permission_ids
    )
