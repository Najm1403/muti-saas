import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
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
    from models.product import Product
    from models.category import Category
    from models.branch_promotion import BranchPromotion


class Promotion(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    __tablename__ = "promotions"

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

    promo_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    # null = auto-applied; not null = code required

    type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    # PERCENTAGE | FLAT_AMOUNT | BXGY | FREE_ITEM

    discount_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Trigger conditions
    trigger_product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    trigger_category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    trigger_min_qty: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    trigger_min_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    # Reward (used for BXGY and FREE_ITEM types)
    reward_product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )

    reward_category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    reward_quantity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    reward_discount_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    # FREE | PERCENTAGE | FLAT_AMOUNT

    reward_discount_value: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    # Validity
    valid_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    max_uses: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    used_count: Mapped[int] = mapped_column(
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
    trigger_product: Mapped["Product | None"] = relationship(
        "Product", foreign_keys=[trigger_product_id]
    )
    trigger_category: Mapped["Category | None"] = relationship(
        "Category", foreign_keys=[trigger_category_id]
    )
    reward_product: Mapped["Product | None"] = relationship(
        "Product", foreign_keys=[reward_product_id]
    )
    reward_category: Mapped["Category | None"] = relationship(
        "Category", foreign_keys=[reward_category_id]
    )

    branch_assignments: Mapped[list["BranchPromotion"]] = relationship(
        "BranchPromotion",
        cascade="all, delete-orphan",
        foreign_keys="[BranchPromotion.promotion_id]",
    )
