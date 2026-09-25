# models/addon_item.py
#
# One selectable item within an AddonGroup (e.g. "Extra Cheese", "Onion").
# Carries its own price_delta — this is the only place in the whole system
# where an add-on-style selection affects price (Variant Options never do).

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
    from models.addon_group import AddonGroup


class AddonItem(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
):
    __tablename__ = "addon_items"

    addon_group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("addon_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    price_delta: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )

    default_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # e.g. "Onion" on a burger — pre-checked, removable by the cashier/customer.

    display_order: Mapped[int] = mapped_column(nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    addon_group: Mapped["AddonGroup"] = relationship(
        "AddonGroup",
        back_populates="items",
    )
