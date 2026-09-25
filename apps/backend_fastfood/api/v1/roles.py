# api/v1/roles.py
#
# Tenant-scoped roles & permissions management.
# Prefix: /api/v1/roles

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user, require_permission, require_tenant_admin
from db.session import get_db
from schemas.common import MessageResponse
from schemas.role import (
    PermissionResponse,
    RoleCreate,
    RolePermissionAssign,
    RoleResponse,
    RoleUpdate,
    UserRoleAssign,
)
from services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Roles & Permissions"], dependencies=[Depends(require_permission("roles.manage"))])


def _svc(db: AsyncSession = Depends(get_db)) -> RoleService:
    return RoleService(db)


@router.get("", response_model=list[RoleResponse], status_code=status.HTTP_200_OK, summary="List roles")
@router.get("/", response_model=list[RoleResponse], status_code=status.HTTP_200_OK, include_in_schema=False)
async def list_roles(
    current_user: CurrentUser = Depends(get_current_user),
    svc: RoleService = Depends(_svc),
) -> list[RoleResponse]:
    return await svc.list(tenant_id=current_user.tenant_id)


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, summary="Create role")
@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_role(
    data: RoleCreate,
    current_user: CurrentUser = Depends(require_tenant_admin),
    svc: RoleService = Depends(_svc),
) -> RoleResponse:
    return await svc.create(tenant_id=current_user.tenant_id, data=data)


@router.get("/{id}", response_model=RoleResponse, status_code=status.HTTP_200_OK, summary="Get role")
async def get_role(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: RoleService = Depends(_svc),
) -> RoleResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch("/{id}", response_model=RoleResponse, status_code=status.HTTP_200_OK, summary="Update role")
async def update_role(
    id: UUID,
    data: RoleUpdate,
    current_user: CurrentUser = Depends(require_tenant_admin),
    svc: RoleService = Depends(_svc),
) -> RoleResponse:
    return await svc.update(id=id, tenant_id=current_user.tenant_id, data=data)


@router.delete("/{id}", response_model=MessageResponse, status_code=status.HTTP_200_OK, summary="Delete role")
async def delete_role(
    id: UUID,
    current_user: CurrentUser = Depends(require_tenant_admin),
    svc: RoleService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Role deleted.")


# ── Permissions ──────────────────────────────────────────────────

@router.get("/permissions/all", response_model=list[PermissionResponse], status_code=status.HTTP_200_OK,
            summary="List all system permissions")
async def list_all_permissions(
    _: CurrentUser = Depends(get_current_user),
    svc: RoleService = Depends(_svc),
) -> list[PermissionResponse]:
    return await svc.list_permissions()


@router.get("/{id}/permissions", response_model=list[PermissionResponse], status_code=status.HTTP_200_OK,
            summary="List permissions assigned to a role")
async def list_role_permissions(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: RoleService = Depends(_svc),
) -> list[PermissionResponse]:
    return await svc.list_role_permissions(role_id=id, tenant_id=current_user.tenant_id)


@router.post("/{id}/permissions", response_model=MessageResponse, status_code=status.HTTP_200_OK,
             summary="Assign permission to role")
async def assign_permission(
    id: UUID,
    data: RolePermissionAssign,
    current_user: CurrentUser = Depends(require_tenant_admin),
    svc: RoleService = Depends(_svc),
) -> MessageResponse:
    await svc.assign_permission(role_id=id, permission_id=data.permission_id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Permission assigned.")


@router.delete("/{id}/permissions/{permission_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK,
               summary="Remove permission from role")
async def remove_permission(
    id: UUID,
    permission_id: UUID,
    current_user: CurrentUser = Depends(require_tenant_admin),
    svc: RoleService = Depends(_svc),
) -> MessageResponse:
    await svc.remove_permission(role_id=id, permission_id=permission_id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Permission removed.")


# ── User-Role assignment (on roles router for convenience) ────────

@router.get("/{id}/users", response_model=list[dict], status_code=status.HTTP_200_OK,
            summary="List users with this role")
async def list_role_users(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: RoleService = Depends(_svc),
) -> list[dict]:
    # Verify role belongs to tenant
    await svc.get(id=id, tenant_id=current_user.tenant_id)
    from sqlalchemy import select
    from models.user import User
    from models.user_role import UserRole
    db = svc.db
    result = await db.execute(
        select(User).join(UserRole, User.id == UserRole.user_id)
        .where(
            UserRole.role_id == id,
            UserRole.deleted_at.is_(None),
            User.deleted_at.is_(None),
            User.tenant_id == current_user.tenant_id,
        )
    )
    return [{"id": str(u.id), "username": u.username, "full_name": u.full_name} for u in result.scalars().all()]
