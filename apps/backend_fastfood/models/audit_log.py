import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import (
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.tenant import Tenant
    from models.user import User


class AuditLog(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    """
    Records user actions for auditing and compliance.

    Every significant operation (create, update, delete, login)
    is captured with context about who performed it and what was affected.

    Examples:
        User Ahmed created Product: Burger
        User Sara cancelled Sale: SAL-000125
        User Ali logged in from 192.168.1.5
    """

    __tablename__ = "audit_logs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Tenant within which the action occurred.

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # User who performed the action. Null for system-initiated actions.

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    # Action performed, e.g. CREATE, UPDATE, DELETE, LOGIN, LOGOUT.

    module: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    # Module where the action occurred, e.g. sales, products, users.

    entity_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    # Name of the affected model/table, e.g. Sale, Product.

    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
        index=True,
    )
    # Primary key of the affected record.

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    # Human-readable description of the action.

    ip_address: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    # IP address of the client at the time of the action.

    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
    )

    user: Mapped["User | None"] = relationship(
        "User",
    )
