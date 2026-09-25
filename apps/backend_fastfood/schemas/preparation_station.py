# schemas/preparation_station.py

from uuid import UUID

from pydantic import Field

from schemas.common import (
    APIBaseSchema,
    UUIDResponseSchema,
    TimestampResponseSchema,
)


class PreparationStationCreate(APIBaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    display_order: int = Field(default=0, ge=0)
    is_active: bool = True


class PreparationStationUpdate(APIBaseSchema):
    name: str | None = Field(None, min_length=1, max_length=100)
    display_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class PreparationStationResponse(UUIDResponseSchema, TimestampResponseSchema):
    branch_id: UUID
    name: str
    display_order: int
    is_active: bool
