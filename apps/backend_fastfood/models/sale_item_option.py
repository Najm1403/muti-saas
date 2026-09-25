"""SaleItemOption connects the Variant Options selected by the customer to a
particular sold item. Display/audit snapshot ONLY — no price. Every price
effect of a customer's selection is either baked into the Variant's
sale_price snapshot (unit_price on SaleItem) or recorded on SaleItemAddon
(models/sale_item_addon.py). Never add a price field back here — that is
exactly the Variant/Add-on conflation this system exists to prevent.
"""
import uuid

from sqlalchemy import ForeignKey, String
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
    from models.sale_item import SaleItem
    from models.variant_option import VariantOption


class SaleItemOption(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
):
    """
    Represents a Variant Option selected for a specific SaleItem.

    VariantOption defines what is available in the menu.
    SaleItemOption records what the customer actually selected.

    Example:
        SaleItem: Electronics — Phone (RAM: 8GB, Color: Black)

    Option name is stored as a snapshot so that historical sales remain
    correct even if the menu option changes later.
    """

    __tablename__ = "sale_item_options"

    sale_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sale_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Sale item to which this selected option belongs.

    variant_option_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("variant_options.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Original Variant Option that was selected.

    option_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    # Option name at the time of sale, e.g. "8GB".

    sale_item: Mapped["SaleItem"] = relationship(
        "SaleItem",
        back_populates="options",
    )

    variant_option: Mapped["VariantOption"] = relationship(
        "VariantOption",
    )
