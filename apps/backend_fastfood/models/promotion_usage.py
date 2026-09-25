import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import (
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.promotion import Promotion
    from models.sale import Sale


class PromotionUsage(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    __tablename__ = "promotion_usages"

    promotion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("promotions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sale_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sales.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # SET NULL: keep usage record if sale is voided.

    discount_applied: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    promotion: Mapped["Promotion"] = relationship("Promotion")
    sale: Mapped["Sale | None"] = relationship("Sale")

    __table_args__ = (
        UniqueConstraint(
            "promotion_id",
            "sale_id",
            name="uq_promotion_usage_promotion_sale",
        ),
    )
