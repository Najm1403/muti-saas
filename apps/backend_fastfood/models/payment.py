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
    from models.sale import Sale


class Payment(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
):
    """
    Represents a payment made against a Sale.

    A sale can have one or multiple payments.

    Examples:
        - Cash
        - Card
        - Bank Transfer
        - Digital Wallet

    Multiple Payment records allow split payments for a single sale.
    """

    __tablename__ = "payments"

    sale_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Sale to which this payment belongs.

    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    # Method used for payment, e.g. CASH, CARD, BANK, DIGITAL.

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    # Amount received through this payment method.

    tendered_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    # Original tender for receipts; amount is the net applied collection.

    reference: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )
    # Optional transaction/reference number for card or digital payments.

    sale: Mapped["Sale"] = relationship(
        "Sale",
        back_populates="payments",
    )

    