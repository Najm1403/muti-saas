# models/product_variant_option_group.py
#
# Join table that makes a shared VariantOptionGroup (Business-level) usable
# on a specific Product. Carries the per-product override of whether that
# group is required — the same shared group (for example, "RAM") might be required on
# one product and optional on another, so this can't live on the group
# itself.
#
# usage_type (Laptop Store shareable-inventory model, spec sections 17/18):
# what THIS product's use of THIS group means — never inferred from the
# group's name:
#   'inventory_component'  — never generates a combination Variant for this
#                            product at all. A selected value resolves
#                            straight to that VariantOption's own shared
#                            component_product_id stock instead. This is the
#                            only behavior the dashboard offers, and the
#                            default for every new attachment.
#   'specification'        — legacy only, no longer offered by the UI:
#                            describes a fixed configuration; selected values
#                            become part of this product's own combination
#                            Variant (option_value_ids/combination_key),
#                            generating an independently priced/stocked SKU
#                            scoped to this product. Existing rows created
#                            before this change keep working as-is (the
#                            combination-Variant machinery in
#                            variant_service.py is untouched) — nothing new
#                            can be created this way going forward.

import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProductVariantOptionGroup(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "product_variant_option_groups"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    option_group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("variant_option_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    display_order: Mapped[int] = mapped_column(nullable=False, default=0)

    usage_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="inventory_component", server_default="inventory_component"
    )

    # Selection rules (spec section 19) — additive, alongside is_required
    # rather than replacing it (is_required already has call sites in
    # offer_service.py, pos_sync_service.py, sellability checks, and
    # several tests; min/max only needs to add new capability, e.g. a
    # laptop with two RAM slots, without touching any of that).
    min_selections: Mapped[int] = mapped_column(nullable=False, default=1, server_default="0")
    max_selections: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    default_option_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("variant_options.id", ondelete="SET NULL"), nullable=True
    )

    # Set when this attachment was materialized from the product's category
    # template (CategoryVariantOptionGroup) rather than attached one-off by
    # an admin directly on this product — see
    # services/category_variant_option_group_service.py. Lets a category
    # edit (add/remove a group) or a product's category change cascade
    # correctly: only rows that trace back to a given category are ever
    # auto-detached, so a manually/one-off attached group is never silently
    # removed. NULL forever for a manual attachment; SET NULL if the source
    # category itself is later deleted (the row and its customization stay,
    # just without a traceable origin).
    source_category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )

    __table_args__ = (
        UniqueConstraint("product_id", "option_group_id", name="uq_product_variant_option_group"),
    )
