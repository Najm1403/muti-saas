# models/category_variant_option_group.py
#
# Template join table: attaches a shared VariantOptionGroup to a Category so
# every product in that category picks it up automatically, instead of an
# admin re-attaching the same group (e.g. "RAM") to each laptop one at a
# time. This is a template, not a live indirection — attaching/detaching a
# group here materializes/removes matching ProductVariantOptionGroup rows
# for the category's current products (see
# services/category_variant_option_group_service.py); nothing downstream
# (POS sale validation, offline sync, the Flutter app) needs to know this
# table exists, since they all still read the per-product join table they
# always have.
#
# Always usage_type='inventory_component' — the only mode the dashboard
# offers (see ProductVariantOptionGroup's docstring); a category template
# has no reason to ever produce the legacy 'specification' combination-
# Variant behavior, so that column doesn't exist here at all.

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CategoryVariantOptionGroup(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "category_variant_option_groups"

    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    option_group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("variant_option_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_required: Mapped[bool] = mapped_column(nullable=False, default=True)
    display_order: Mapped[int] = mapped_column(nullable=False, default=0)

    # Mirrors ProductVariantOptionGroup's own selection-rule columns — see
    # that model's docstring for why these are additive alongside is_required.
    min_selections: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    max_selections: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    default_option_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("variant_options.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("category_id", "option_group_id", name="uq_category_variant_option_group"),
    )
