# schemas/role.py

from uuid import UUID

from pydantic import Field

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
)


class RoleCreate(APIBaseSchema):
    """
    Data required to create a role within a tenant.

    Role names must be unique per tenant (enforced at DB level).
    """

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class RoleUpdate(APIBaseSchema):
    """
    Fields that may be updated on an existing role.
    """

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class RoleResponse(UUIDResponseSchema, TimestampResponseSchema):
    """
    Role record returned by the API.
    """

    tenant_id: UUID
    name: str
    description: str | None
    is_active: bool


class PermissionResponse(UUIDResponseSchema):
    code: str
    name: str
    description: str | None
    module: str
    is_active: bool


class RolePermissionAssign(APIBaseSchema):
    """
    Request body for granting a permission to a role.
    """

    permission_id: UUID


class RolePermissionRemove(APIBaseSchema):
    """
    Request body for revoking a permission from a role.
    """

    permission_id: UUID


class UserRoleAssign(APIBaseSchema):
    role_id: UUID
