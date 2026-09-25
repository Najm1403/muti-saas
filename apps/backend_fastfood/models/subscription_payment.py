# models/subscription_payment.py
#
# Manual payment record — no online payment gateway.
# Platform admin records each payment received (cash, bank transfer, cheque).

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from models.subscription import BillingCycle

if TYPE_CHECKING:
    from models.subscription import Subscription


class SubscriptionPayment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Records a single payment made by a tenant for their subscription.

    No online/card processing — the platform admin records it manually
    after receiving a bank transfer, cash, or cheque.

    Recording a payment:
        1. Validates the subscription is not cancelled.
        2. Sets status → ACTIVE if it was TRIAL/SUSPENDED/EXPIRED.
        3. Extends subscription.expires_at by one billing_cycle period.
    """

    __tablename__ = "subscription_payments"

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Denormalised from subscription for fast tenant-level payment queries.

    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    # The amount actually received (admin may override the auto-computed net price).

    list_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    # Undiscounted plan price for the billing cycle at the time this payment was recorded.

    discount_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    # Discount percentage applied when this payment was recorded (plan-level or per-tenant).

    billing_cycle: Mapped[BillingCycle] = mapped_column(
        Enum(BillingCycle, name="billing_cycle", native_enum=False),
        nullable=False,
    )

    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    # period_start / period_end document what billing period this payment covers.

    payment_method: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    # Free-text: "Bank Transfer", "Cash", "Cheque", "Online Transfer", etc.

    reference_number: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )
    # Bank transaction ref, cheque number, receipt number, etc.

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    waived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    # True when this row represents a platform admin forgiving a due period
    # (amount is 0) rather than money actually received — kept as a real
    # payment-history row (not a separate table) so the period extension and
    # audit trail work identically, but the distinction from a real payment
    # must always stay visible in the record.

    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    recorded_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("platform_admins.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Which platform admin entered this payment record.

    subscription: Mapped["Subscription"] = relationship(
        "Subscription",
        back_populates="payments",
    )
