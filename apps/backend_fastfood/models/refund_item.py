
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import (
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.refund import Refund
    from models.sale_item import SaleItem


class RefundItem(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
):
    """
    Represents one refunded item from an original SaleItem.

    Supports partial refunds.

    Example:

        Original SaleItem:
            Product: Burger
            Quantity: 3
            Unit Price: Rs. 500

        Refund:
            Quantity: 1
            Refund Amount: Rs. 500

    The original SaleItem is never modified.
    """

    __tablename__ = "refund_items"

    refund_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("refunds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Refund to which this item belongs.

    sale_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sale_items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Original sale item being refunded.

    product_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    # Product name snapshot.

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
    )
    # Quantity being refunded.

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    # Original selling price per unit.

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    # Total refund amount for this item.

    refund: Mapped["Refund"] = relationship(
        "Refund",
        back_populates="items",
    )

    sale_item: Mapped["SaleItem"] = relationship(
        "SaleItem",
    )