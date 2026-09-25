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
    from models.sale import Sale
    from models.product import Product
    from models.sale_item_option import SaleItemOption
    from models.sale_item_addon import SaleItemAddon
    from models.preparation_station import PreparationStation


class SaleItem(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
    SyncMixin,
):
    """
    Represents one product line inside a Sale.

    Example:

        Sale: SAL-000125

        2 × Cone Ice Cream
        Unit Price: Rs. 150
        Discount:   Rs. 0
        Total:      Rs. 300

    Product information is partially stored as a snapshot so that
    historical sales remain correct if the product changes later.
    """

    __tablename__ = "sale_items"
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("variants.id", ondelete="RESTRICT"), nullable=False, index=True)
    tracked_at_sale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    product_tracking_at_sale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    sale_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Sale to which this item belongs.

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Original product that was sold.

    product_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    # Product name at the time of sale.

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
    )
    # Quantity sold.

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    # Selling price per unit at the time of sale.

    discount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    # Discount applied to this item.

    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    # Final line total after discount and option adjustments.

    preparation_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )
    # KDS item status, e.g. PENDING, PREPARING, READY.
    # Null on pre-KDS records; managed by kitchen staff via future KDS API.

    kitchen_station_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("preparation_stations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Snapshot of Product.preparation_station_id at time of sale.
    # Retained even if the station is later deleted so historical KDS data
    # remains intact.

    # Laptop Store shareable-inventory model: a selected 'inventory_component'
    # (e.g. a RAM stick) is submitted as its own ordinary, independently
    # priced/stocked SaleItem — never a nested child row — so pricing,
    # stock validation and deduction need zero special-casing (see
    # services/pos_sale_service.py). These two fields only exist to (a) let
    # checkout verify a required component group was actually fulfilled and
    # (b) let the receipt group a component visually under its parent line.
    # Plain UUID, no FK: both items in a pair arrive together in the same
    # submitted batch with client-generated ids, so there's no existing row
    # to reference yet at insert time.
    parent_item_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    # References the *shared* group (variant_option_groups), not the
    # per-product attachment row (product_variant_option_groups) — the POS
    # only ever learns the shared group's id via full/delta sync
    # (services/pos_sync_service.py's PosSyncVariantOptionGroup(id=group.id)),
    # and options are matched to their group by that same shared id
    # everywhere else in the sync payload, so this must stay in the same id
    # space or the client could never populate it with a real value.
    satisfies_option_group_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("variant_option_groups.id", ondelete="SET NULL"), nullable=True,
    )
    # Which VariantOption this line represents (e.g. "16GB DDR4") — for
    # server-side pairing verification and receipt display. Distinct from
    # `options` below, which snapshots the values that define THIS line's
    # own Variant combination, not which shared library option it stands in
    # for as a component.
    component_option_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("variant_options.id", ondelete="SET NULL"), nullable=True,
    )

    sale: Mapped["Sale"] = relationship(
        "Sale",
        back_populates="items",
    )

    product: Mapped["Product"] = relationship(
        "Product",
    )

    kitchen_station: Mapped["PreparationStation | None"] = relationship(
        "PreparationStation",
    )

    options: Mapped[list["SaleItemOption"]] = relationship(
        "SaleItemOption",
        back_populates="sale_item",
        cascade="all, delete-orphan",
    )

    addons: Mapped[list["SaleItemAddon"]] = relationship(
        "SaleItemAddon",
        back_populates="sale_item",
        cascade="all, delete-orphan",
    )
