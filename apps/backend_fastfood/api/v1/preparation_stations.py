# api/v1/preparation_stations.py
#
# Management endpoints for preparation stations (KDS-ready, V1).
# Stations are scoped to a branch and represent physical kitchen areas
# (e.g. Kitchen, Coffee Station). Products are linked to stations so that
# SaleItems can carry a kitchen_station_id for future KDS routing.
#
# Prefix: /api/v1/branches/{branch_id}/preparation-stations

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.preparation_station import (
    PreparationStationCreate,
    PreparationStationResponse,
    PreparationStationUpdate,
)
from services.preparation_station_service import PreparationStationService

router = APIRouter(
    prefix="/branches/{branch_id}/preparation-stations",
    tags=["Preparation Stations"],
)


def _svc(db: AsyncSession = Depends(get_db)) -> PreparationStationService:
    return PreparationStationService(db)


@router.get("/queue")
async def kitchen_queue(branch_id: UUID, current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)):
    from services.kitchen_service import KitchenService
    return await KitchenService(db).queue(branch_id, current_user)


@router.patch("/queue/{item_id}")
async def update_kitchen_item(branch_id: UUID, item_id: UUID, data: dict,
        current_user: CurrentUser = Depends(get_current_user), db=Depends(get_db)):
    from services.kitchen_service import KitchenService
    return await KitchenService(db).advance(branch_id, item_id, data.get("status"), current_user)


@router.post(
    "/",
    response_model=PreparationStationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create preparation station",
    description=(
        "Add a named kitchen/preparation area to a branch. "
        "Returns 409 if a station with the same name already exists for this branch."
    ),
)
async def create_station(
    branch_id: UUID,
    data: PreparationStationCreate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PreparationStationService = Depends(_svc),
) -> PreparationStationResponse:
    return await svc.create(
        branch_id=branch_id, data=data, tenant_id=current_user.tenant_id
    )


@router.get(
    "/",
    response_model=list[PreparationStationResponse],
    summary="List preparation stations",
    description="Return all preparation stations for a branch, ordered by display_order then name.",
)
async def list_stations(
    branch_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PreparationStationService = Depends(_svc),
) -> list[PreparationStationResponse]:
    return await svc.list(branch_id=branch_id, tenant_id=current_user.tenant_id)


@router.get(
    "/{station_id}",
    response_model=PreparationStationResponse,
    summary="Get preparation station",
    description="Return a single preparation station by UUID.",
)
async def get_station(
    branch_id: UUID,
    station_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PreparationStationService = Depends(_svc),
) -> PreparationStationResponse:
    return await svc.get(station_id=station_id, tenant_id=current_user.tenant_id)


@router.patch(
    "/{station_id}",
    response_model=PreparationStationResponse,
    summary="Update preparation station",
    description="Update name, display_order, or is_active. All fields optional.",
)
async def update_station(
    branch_id: UUID,
    station_id: UUID,
    data: PreparationStationUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PreparationStationService = Depends(_svc),
) -> PreparationStationResponse:
    return await svc.update(
        station_id=station_id, data=data, tenant_id=current_user.tenant_id
    )


@router.delete(
    "/{station_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete preparation station",
    description=(
        "Soft-delete a preparation station. Products linked to this station retain "
        "their kitchen_station_id on existing SaleItems (historical accuracy). "
        "The station stops appearing in list responses."
    ),
)
async def delete_station(
    branch_id: UUID,
    station_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PreparationStationService = Depends(_svc),
) -> None:
    await svc.delete(station_id=station_id, tenant_id=current_user.tenant_id)


