import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Integer, UniqueConstraint
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
    from models.deal_item import DealItem
    from models.branch_deal import BranchDeal


class Deal(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    __tablename__ = "deals"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    deal_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    image_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    fixed_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    # If set: sell bundle at this price.

    discount_value: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    # OR: deduct from individual item totals.

    discount_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    # FLAT | PERCENTAGE

    valid_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    all_branches: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant")

    items: Mapped[list["DealItem"]] = relationship(
        "DealItem",
        back_populates="deal",
        cascade="all, delete-orphan",
    )

    branch_assignments: Mapped[list["BranchDeal"]] = relationship(
        "BranchDeal",
        cascade="all, delete-orphan",
        foreign_keys="[BranchDeal.deal_id]",
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "deal_code",
            name="uq_deal_tenant_deal_code",
        ),
    )
