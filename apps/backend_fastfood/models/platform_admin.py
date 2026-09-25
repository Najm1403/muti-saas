# models/platform_admin.py
#
# Platform-level administrator — NOT a tenant user.
# These accounts belong to the SaaS owner and can manage all tenants.

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PlatformAdmin(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    A human who logs into the Platform API on behalf of the SaaS company.

    Completely separate from tenant users:
        - Lives in its own table (platform_admins), not users.
        - Authenticated via platform-specific JWTs (type: "platform_access").
        - Has no tenant_id — operates across all tenants.

    Roles:
        is_super=True  → can create/delete other platform admins.
        is_super=False → can manage tenants and subscriptions but not admins.
    """

    __tablename__ = "platform_admins"

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_super: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Coarse access tier for non-super admins. Kept in sync with is_super:
    #   owner   → full access  (is_super = True)
    #   manager → all modules except plans / settings / admin-management / destructive deletes
    #   viewer  → read-only (every POST/PATCH/DELETE on the platform API is blocked)
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="manager",
        server_default="manager",
    )

    # Explicit, single-purpose capability grant — a 'manager' admin can be
    # trusted with Business Template delete / config.modules.hidden changes
    # without being promoted to full owner. Owners always have this
    # implicitly (is_super bypasses the check); only settable by a super
    # admin (api/platform/platform_admins.py::update_platform_admin). Even
    # with this granted, the action itself still requires a fresh password
    # step-up (see core.security.create_platform_step_up_token) — this flag
    # only controls eligibility, never skips that confirmation.
    can_manage_business_templates: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Self-service "forgot password" — SHA-256 hash of the 6-digit OTP + its expiry.
    # Cleared once the reset completes (single-use).
    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_reset_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
