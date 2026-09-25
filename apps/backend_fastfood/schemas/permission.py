# schemas/permission.py

from uuid import UUID

from pydantic import Field

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
)


class PermissionResponse(UUIDResponseSchema, TimestampResponseSchema):
    """
    System permission returned by the API.

    Permissions are seeded by the system and are read-only via the API.
    They are assigned to roles through RolePermission.

    Examples:
        sales.view, sales.create, sales.cancel
        products.view, products.create, products.update
        users.view, users.create
        reports.view
    """

    code: str
    name: str
    description: str | None
    module: str
    is_active: bool


class UserPermissionState(APIBaseSchema):
    """One permission and its effective state for a tenant user."""

    id: UUID
    code: str
    name: str
    description: str | None
    module: str
    checked: bool
    inherited: bool
    overridden: bool


class UserPermissionsUpdate(APIBaseSchema):
    """The complete desired effective permission set for a user."""

    permission_ids: list[UUID] = Field(default_factory=list)
