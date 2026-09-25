import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import (
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user_role import UserRole
    from models.role_permission import RolePermission


class Role(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    """
    Represents a role within a Tenant.

    A role defines the functional position of a user.

    Examples:
        - Owner
        - Manager
        - Cashier
        - Branch Manager

    Permissions are assigned to roles through RolePermission.
    """

    __tablename__ = "roles"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Tenant that owns this role.

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    # Role name, e.g. "Manager" or "Cashier".

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    # Optional explanation of the role.

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    # Whether this role is currently active.

    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    role_permissions: Mapped[list["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "name",
            name="uq_role_tenant_name",
        ),
    )