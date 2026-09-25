# models/subscription.py
#
# A tenant's subscription to a plan.
# One tenant → one active subscription at a time.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.plan import Plan
    from models.tenant import Tenant
    from models.subscription_payment import SubscriptionPayment


class BillingCycle(str, enum.Enum):
    """How often the subscription is billed."""
    MONTHLY = "MONTHLY"
    YEARLY  = "YEARLY"


class SubscriptionStatus(str, enum.Enum):
    """Lifecycle state of a subscription."""
    TRIAL     = "TRIAL"      # Free trial period — not yet billed.
    ACTIVE    = "ACTIVE"     # Paid and within the valid period.
    PAST_DUE  = "PAST_DUE"   # expires_at has passed but still within the
                              # per-subscription grace period — access is
                              # NOT restricted yet; this is a warning stage.
    SUSPENDED = "SUSPENDED"  # Grace period elapsed with no payment, or a
                              # platform admin suspended directly (non-payment,
                              # violation). Blocks POS access.
    CANCELLED = "CANCELLED"  # Tenant or admin cancelled — will not renew.
    EXPIRED   = "EXPIRED"    # Legacy value, retained for old data/API
                              # compatibility. New lapses use PAST_DUE then
                              # SUSPENDED instead — see SubscriptionService.
                              # evaluate_and_sync().


class Subscription(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Links a Tenant to a Plan for a billing period.

    Lifecycle:
        TRIAL → ACTIVE (first payment recorded)
        ACTIVE → PAST_DUE (expires_at passed; still within grace_period_days —
            automatic, evaluated on read, not a scheduled job)
        PAST_DUE → SUSPENDED (grace period elapsed with no payment — automatic)
        PAST_DUE → ACTIVE (payment recorded, or admin waives the due period)
        ACTIVE / PAST_DUE / SUSPENDED → SUSPENDED (platform admin suspends directly)
        SUSPENDED → ACTIVE (reactivated, or a waived period)
        ACTIVE / PAST_DUE / SUSPENDED → CANCELLED

    Renewal:
        Recording a payment (or waiving the due period) via SubscriptionPayment
        extends expires_at by one billing_cycle period automatically and
        resets status to ACTIVE.

    See SubscriptionService.evaluate_and_sync() for the automatic PAST_DUE/
    SUSPENDED transitions, and extend_grace()/waive() for the manual-override
    actions a platform admin can take on top of the automatic lifecycle.
    """

    __tablename__ = "subscriptions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    billing_cycle: Mapped[BillingCycle] = mapped_column(
        Enum(BillingCycle, name="billing_cycle", native_enum=False),
        nullable=False,
    )

    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status", native_enum=False),
        nullable=False,
        default=SubscriptionStatus.TRIAL,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    # Extended by one billing_cycle each time a payment is recorded.

    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    grace_period_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )
    # Days after expires_at during which status shows PAST_DUE (a warning
    # stage, access not restricted) before auto-transitioning to SUSPENDED.
    # Per-subscription so a platform admin can extend it for one tenant
    # without changing the default for everyone else.

    discount_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    # Per-tenant negotiated discount (0–100). When set it REPLACES the plan-level
    # discount for this subscription's billing cycle. NULL → fall back to the plan.

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="subscriptions")
    payments: Mapped[list["SubscriptionPayment"]] = relationship(
        "SubscriptionPayment",
        back_populates="subscription",
        order_by="SubscriptionPayment.paid_at",
    )

    __table_args__ = (
        # Enforce one active/trial subscription per tenant at the DB level.
        Index(
            "ix_subscriptions_tenant_active",
            "tenant_id",
            "status",
        ),
    )
