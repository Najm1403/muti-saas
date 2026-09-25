# models/addon_group.py
#
# A multi-select group of Add-on Items, shared at the Business level and
# reusable across products via product_addon_groups (see
# models/product_addon_group.py). Selecting Add-on Items NEVER changes which
# Variant (SKU) is being bought and NEVER generates combinations — it only
# adds a price delta on top of whichever Variant was already selected. See
# apps/COMPLETE-IMPLEMENTATION-SPEC.md A1.
#
# Never call this "Modifier" anywhere in code or UI — "Modifier" sitting next
# to "Variant"/"Option" is exactly the naming collision that causes the two
# systems to get conflated by accident.
#
# Examples: "Toppings", "Base Ingredients".

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
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
    from models.addon_item import AddonItem


class AddonGroup(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
):
    __tablename__ = "addon_groups"

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    selection_type: Mapped[str] = mapped_column(String(10), nullable=False, default="multiple")
    # 'single' | 'multiple'. Even 'single' Add-on groups (e.g. "Sauce:
    # Ketchup/Mayo/BBQ") stay Add-ons, not Variants, because the choice
    # doesn't define a separately-stocked SKU — see spec A1's decision rule.

    min_select: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_select: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NULL = unlimited

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    items: Mapped[list["AddonItem"]] = relationship(
        "AddonItem",
        back_populates="addon_group",
        cascade="all, delete-orphan",
    )
