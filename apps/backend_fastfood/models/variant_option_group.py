# models/variant_option_group.py
#
# A group of Variant Selection values, shared at the Business level and reusable
# across products via product_variant_option_groups. New dashboard attachments use
# usage_type='inventory_component': a selection resolves to the linked component
# product's Variant and never generates a host-product combination Variant.
#
# Selection limits and is_required live on ProductVariantOptionGroup because the
# same shared group may have different rules on different products.
#
# Examples: RAM, Storage, and Colors. Colors is used specially by Add Product to
# create priced/stocked product Variants; it is not attached later from product detail.

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
    from models.variant_option import VariantOption


class VariantOptionGroup(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
):
    __tablename__ = "variant_option_groups"

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    options: Mapped[list["VariantOption"]] = relationship(
        "VariantOption",
        back_populates="option_group",
        cascade="all, delete-orphan",
    )
