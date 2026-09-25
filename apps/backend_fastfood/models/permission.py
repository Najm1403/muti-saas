from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import (
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.role_permission import RolePermission


class Permission(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    """
    Represents one specific action that a user can perform.

    Permissions are assigned to Roles through RolePermission.

    Examples:
        - sales.view
        - sales.create
        - sales.cancel
        - products.view
        - products.create
        - products.update
        - users.view
        - reports.view

    Permissions are global system definitions. Tenant-specific
    access is determined through the user's roles.
    """

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    # Unique permission identifier, e.g. "sales.create".

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    # Human-readable permission name.

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    # Explanation of what this permission allows.

    module: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    # Module to which the permission belongs, e.g. "sales".

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    # Whether this permission is currently available.

    role_permissions: Mapped[list["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan",
    )