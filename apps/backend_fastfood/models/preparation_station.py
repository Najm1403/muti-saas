import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import (
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.branch import Branch


class PreparationStation(
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    """
    A named kitchen or preparation area within a branch.

    Examples: Kitchen, Coffee Station, Ice Cream Counter.

    Products reference a PreparationStation so that a future KDS screen for
    that station shows only the items it needs to prepare. A null
    preparation_station_id on a product means it has no designated station.
    """

    __tablename__ = "preparation_stations"

    branch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    branch: Mapped["Branch"] = relationship("Branch")
