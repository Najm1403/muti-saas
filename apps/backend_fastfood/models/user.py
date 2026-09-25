import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint
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
    from models.user_role import UserRole
    from models.user_branch import UserBranch


class User(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    """
    Represents a user who can access the SaaS application.

    A user belongs to a Tenant and can later be assigned one or more
    Roles through the UserRole model.

    Examples:
        - Owner
        - Manager
        - Cashier
        - Branch Manager

    Authentication credentials and authorization roles are kept
    separate from the User's basic identity information.
    """

    __tablename__ = "users"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Tenant to which the user belongs.

    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    # Login username.

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    # User's display name.

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    # Optional email address.

    password_reset_token: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    # SHA-256 hex digest of the OTP sent to the user. Never store the raw OTP.

    password_reset_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # UTC expiry of the reset OTP. Null when no reset is in progress.

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    # Hashed password. Never store a plain-text password.

    pin_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    # Hashed 4-6 digit PIN used for quick staff sign-in on the POS tablet.
    # Null when the user has no PIN set — POS login then falls back to password.

    photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    # Optional avatar shown for this staff member on the POS staff-picker grid.

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    # Whether the user can log in.

    all_branches: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    max_discount_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    # Ceiling on this cashier's manual discount, as a percent of subtotal
    # (see services/offer_service.py::validate). Null means no explicit cap:
    # any amount is allowed once the sales.discount permission is held.
    # Irrelevant without that permission — this only narrows it, never grants it.

    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="users",
    )

    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    branch_assignments: Mapped[list["UserBranch"]] = relationship(
        "UserBranch",
        cascade="all, delete-orphan",
        foreign_keys="[UserBranch.user_id]",
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "username",
            name="uq_user_tenant_username",
        ),
    )

    @property
    def has_pin(self) -> bool:
        """True when a POS quick sign-in PIN has been set for this user."""
        return self.pin_hash is not None