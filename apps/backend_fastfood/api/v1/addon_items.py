# api/v1/addon_items.py
#
# Add-on Item management — leaf nodes of an Add-on Group.
# Prefix: /api/v1/addon-items

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.addon_item import AddonItemCreate, AddonItemResponse, AddonItemUpdate
from schemas.common import MessageResponse
from services.addon_item_service import AddonItemService

router = APIRouter(prefix="/addon-items", tags=["Add-on Items"])


def _svc(db: AsyncSession = Depends(get_db)) -> AddonItemService:
    return AddonItemService(db)


@router.get("/", response_model=list[AddonItemResponse], status_code=status.HTTP_200_OK)
async def list_addon_items(
    addon_group_id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: AddonItemService = Depends(_svc),
) -> list[AddonItemResponse]:
    return await svc.list(addon_group_id=addon_group_id, tenant_id=current_user.tenant_id)


@router.post("/", response_model=AddonItemResponse, status_code=status.HTTP_201_CREATED)
async def create_addon_item(
    addon_group_id: UUID, data: AddonItemCreate, current_user: CurrentUser = Depends(get_current_user), svc: AddonItemService = Depends(_svc),
) -> AddonItemResponse:
    return await svc.create(addon_group_id=addon_group_id, tenant_id=current_user.tenant_id, data=data)


@router.get("/{id}", response_model=AddonItemResponse, status_code=status.HTTP_200_OK)
async def get_addon_item(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: AddonItemService = Depends(_svc),
) -> AddonItemResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch("/{id}", response_model=AddonItemResponse, status_code=status.HTTP_200_OK)
async def update_addon_item(
    id: UUID, data: AddonItemUpdate, current_user: CurrentUser = Depends(get_current_user), svc: AddonItemService = Depends(_svc),
) -> AddonItemResponse:
    return await svc.update(id=id, tenant_id=current_user.tenant_id, data=data)


@router.post("/{id}/activate", response_model=AddonItemResponse, status_code=status.HTTP_200_OK)
async def activate_addon_item(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: AddonItemService = Depends(_svc),
) -> AddonItemResponse:
    return await svc.activate(id=id, tenant_id=current_user.tenant_id)


@router.post("/{id}/deactivate", response_model=AddonItemResponse, status_code=status.HTTP_200_OK)
async def deactivate_addon_item(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: AddonItemService = Depends(_svc),
) -> AddonItemResponse:
    return await svc.deactivate(id=id, tenant_id=current_user.tenant_id)


@router.delete("/{id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def delete_addon_item(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: AddonItemService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Add-on item deleted.")
