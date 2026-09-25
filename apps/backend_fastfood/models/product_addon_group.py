# models/product_addon_group.py
#
# Join table attaching a shared, Business-level AddonGroup to a specific
# Product. This is deliberately a completely separate table from
# product_variant_option_groups (models/product_variant_option_group.py) —
# never merge the two, that merge is exactly what would let a multi-select
# Add-on choice reach a Variant's combination_key (see spec A1/D4).

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProductAddonGroup(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "product_addon_groups"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    addon_group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("addon_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    display_order: Mapped[int] = mapped_column(nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("product_id", "addon_group_id", name="uq_product_addon_group"),
    )
