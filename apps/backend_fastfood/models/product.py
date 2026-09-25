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
    from models.category import Category
    from models.variant_option_group import VariantOptionGroup
    from models.addon_group import AddonGroup
    from models.product_branch import ProductBranch
    from models.preparation_station import PreparationStation
    from models.variant import Variant


class Product(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
):
    __tablename__ = "products"
    allow_inventory_tracking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    image_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # sku / warranty / specs (see models/product_spec.py) are optional,
    # never-required fields shown or hidden per business template
    # (template.config.product_fields — spec G2). A Fast Food template
    # leaves these off; an Electronics-style template turns them on.
    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    warranty: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # NO base_price column — every product always has a default Variant
    # (via default_variant_id below) whose sale_price is the sellable price.
    # See spec D1.

    display_order: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    all_branches: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    preparation_station_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("preparation_stations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # KDS routing: which station prepares this product.
    # Null means no designated station. SET NULL on station deletion so
    # historical SaleItems retain their snapshot kitchen_station_id.

    default_variant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("variants.id", ondelete="SET NULL"),
        nullable=True,
    )
    # The zero-option Variant auto-created alongside this product (spec D1).
    # SET NULL rather than a hard dependency: the Variant row itself is
    # deleted via ondelete="RESTRICT" on Variant.product_id, so this FK only
    # ever goes null if the pointer is intentionally cleared.

    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="products",
    )

    # Variant Option Groups attached to this product. Groups themselves are
    # shared at the Business level (models/variant_option_group.py) — this is
    # a many-to-many view through product_variant_option_groups, so deleting
    # a product never deletes a shared group, only the attachment row.
    variant_option_groups: Mapped[list["VariantOptionGroup"]] = relationship(
        "VariantOptionGroup",
        secondary="product_variant_option_groups",
        viewonly=True,
    )

    # Add-on Groups attached to this product — same shared-library shape as
    # above, via product_addon_groups. Never feeds into variant generation
    # (see spec A1/D4) — this relationship exists purely for display/listing.
    addon_groups: Mapped[list["AddonGroup"]] = relationship(
        "AddonGroup",
        secondary="product_addon_groups",
        viewonly=True,
    )

    branch_assignments: Mapped[list["ProductBranch"]] = relationship(
        "ProductBranch",
        cascade="all, delete-orphan",
        foreign_keys="[ProductBranch.product_id]",
    )

    preparation_station: Mapped["PreparationStation | None"] = relationship(
        "PreparationStation",
    )

    default_variant: Mapped["Variant | None"] = relationship(
        "Variant",
        foreign_keys=[default_variant_id],
    )
