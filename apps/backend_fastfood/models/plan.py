# models/plan.py
#
# Subscription plan offered by the SaaS platform.
# Each plan defines pricing (monthly + yearly) and resource limits.

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Numeric, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.subscription import Subscription


class Plan(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """
    A subscription plan available on the platform.

    Resource limits use -1 to mean "unlimited".

    Pricing:
        price_monthly — billed each month.
        price_yearly  — billed once per year (typically ~10× monthly, 2 months free).
    """

    __tablename__ = "plans"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    # Human-readable name, e.g. "Starter", "Pro", "Enterprise".

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    price_monthly: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    price_yearly: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    # Yearly price is stored as the total annual amount (not monthly × 12).

    discount_monthly_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )

    discount_yearly_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    # Public percentage discounts (0–100) advertised on the pricing page.
    # A per-subscription discount_pct overrides these for a specific tenant.

    max_restaurants: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    max_branches: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    max_users: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )

    max_devices: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2,
    )
    # -1 means no limit on any of the above.

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    # Inactive plans are hidden from new signups but existing subscriptions continue.

    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="plan",
    )
