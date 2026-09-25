import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import (
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.business import Business
    from models.user import User


class Tenant(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    """
    Represents one customer/business account in the multi-tenant SaaS system.

    A tenant is the top-level owner of the application's data. A tenant has
    exactly ONE Business (see spec A2) — if an operator needs two business
    types (e.g. a burger place and a mobile shop), they get two separate
    Tenant accounts, never two Businesses under one Tenant.

    Example:

        Tenant: ABC Foods

            └── Business (exactly one)
                  ├── Branch
                  │     └── Devices
                  └── ...

            └── Users / Roles

    Each tenant's data must remain isolated from other tenants.
    """

    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    # Business/company name.

    tenant_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    # Human-readable unique identifier for the tenant.

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    # Whether the tenant can currently use the SaaS system.

    # Which BUSINESS TYPE this tenant is (Fast Food / Electronics / ...).
    # Drives Variant/Add-on seeding, inventory strictness, pricing fields,
    # and POS layout — see apps/COMPLETE-IMPLEMENTATION-SPEC.md Part C.
    # Required: every tenant is onboarded with a business template.
    business_template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("business_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # A free-text notice a platform admin sets for this tenant — billing
    # warnings, policy notes, or any other instruction that should reach the
    # tenant. Shown as a popup on the tenant dashboard after login (see
    # schemas.auth.MeResponse). One current message at a time, not a log —
    # set_admin_message()/clear_admin_message() in TenantService are the only
    # writers. Separate from the automatic subscription PAST_DUE/SUSPENDED
    # banner, which is derived, not stored here.
    admin_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_message_set_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    business: Mapped["Business"] = relationship(
        "Business",
        back_populates="tenant",
        uselist=False,
        cascade="all, delete-orphan",
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
