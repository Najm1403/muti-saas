# models/sale_item_addon.py
#
# The Add-on equivalent of sale_item_options — priced independently, unlike
# SaleItemOption. price_delta_at_sale is always the SERVER-VERIFIED delta
# (see services/pos_sale_service.py's resolve_addon_price_deltas / spec D7),
# never trusted verbatim from the client payload.

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String
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
    from models.addon_item import AddonItem


class SaleItemAddon(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
):
    __tablename__ = "sale_item_addons"

    sale_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sale_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    addon_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("addon_items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    addon_name: Mapped[str] = mapped_column(String(100), nullable=False)  # snapshot
    price_delta_at_sale: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    was_removed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # True when a default_selected Add-on Item was deselected by the customer
    # (e.g. "no onion") — still recorded, so the kitchen ticket can print it.

    sale_item: Mapped["SaleItem"] = relationship(
        "SaleItem",
        back_populates="addons",
    )
    addon_item: Mapped["AddonItem"] = relationship(
        "AddonItem",
    )
