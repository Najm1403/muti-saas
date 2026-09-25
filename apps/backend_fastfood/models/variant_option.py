# models/variant_option.py
#
# One selectable value within a VariantOptionGroup (e.g. "8GB", "Large").
#
# NO price field here. A create-time Color's full price lives on its product
# Variant; an inventory component's price/stock lives on the linked component
# product's default Variant; price-only deltas belong to Add-on Items.
#
# component_product_id (Laptop Store shareable-inventory model): set ONCE,
# in the Variant Options library, when this option is marked "track as
# inventory component" — auto-creates one small real Product (its own
# category, own default Variant, own VariantBranchStock) that
# this option now represents. Every product that later attaches this
# option's group with usage_type='inventory_component' (see
# ProductVariantOptionGroup) automatically shares THIS ONE stock pool — no
# further per-product linking step. NULL means this option is a plain label
# only (the 'specification' case — describes a fixed configuration, never
# independently stocked).

import uuid

from sqlalchemy import Boolean, ForeignKey, String
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
    from models.variant_option_group import VariantOptionGroup


class VariantOption(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
):
    __tablename__ = "variant_options"

    option_group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("variant_option_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Option group to which this option belongs.

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    # Name displayed to the POS user, e.g. "8GB".

    display_order: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    # Controls the order in which options appear in the POS.

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    # Whether this option is currently available for selection.

    component_product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # See module docstring — NULL unless this option is tracked as a shared
    # inventory component.

    option_group: Mapped["VariantOptionGroup"] = relationship(
        "VariantOptionGroup",
        back_populates="options",
    )
