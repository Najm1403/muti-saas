# api/v1/addon_groups.py
#
# Add-on Group management — shared at the Business level, reusable across
# products via product_addon_groups. Never feeds into variant generation
# (spec A1/D4) — this section never talks to the Variant endpoints.
# Prefix: /api/v1/addon-groups

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user, get_current_business_id
from db.session import get_db
from schemas.addon_group import (
    AddonGroupCreate,
    AddonGroupResponse,
    AddonGroupUpdate,
    ProductAddonGroupAttach,
    ProductAddonGroupResponse,
)
from schemas.common import MessageResponse
from services.addon_group_service import AddonGroupService

router = APIRouter(prefix="/addon-groups", tags=["Add-on Groups"])
product_router = APIRouter(tags=["Add-on Groups"])


def _svc(db: AsyncSession = Depends(get_db)) -> AddonGroupService:
    return AddonGroupService(db)


@router.get("/", response_model=list[AddonGroupResponse], status_code=status.HTTP_200_OK,
    summary="List the business's shared Add-on Groups")
async def list_addon_groups(
    current_user: CurrentUser = Depends(get_current_user),
    business_id: UUID = Depends(get_current_business_id),
    svc: AddonGroupService = Depends(_svc),
) -> list[AddonGroupResponse]:
    return await svc.list(business_id=business_id, tenant_id=current_user.tenant_id)


@router.post("/", response_model=AddonGroupResponse, status_code=status.HTTP_201_CREATED,
    summary="Create an Add-on Group in the shared library")
async def create_addon_group(
    data: AddonGroupCreate,
    current_user: CurrentUser = Depends(get_current_user),
    business_id: UUID = Depends(get_current_business_id),
    svc: AddonGroupService = Depends(_svc),
) -> AddonGroupResponse:
    return await svc.create(business_id=business_id, tenant_id=current_user.tenant_id, data=data)


@router.get("/{id}", response_model=AddonGroupResponse, status_code=status.HTTP_200_OK)
async def get_addon_group(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: AddonGroupService = Depends(_svc),
) -> AddonGroupResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch("/{id}", response_model=AddonGroupResponse, status_code=status.HTTP_200_OK)
async def update_addon_group(
    id: UUID, data: AddonGroupUpdate, current_user: CurrentUser = Depends(get_current_user), svc: AddonGroupService = Depends(_svc),
) -> AddonGroupResponse:
    return await svc.update(id=id, tenant_id=current_user.tenant_id, data=data)


@router.post("/{id}/activate", response_model=AddonGroupResponse, status_code=status.HTTP_200_OK)
async def activate_addon_group(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: AddonGroupService = Depends(_svc),
) -> AddonGroupResponse:
    return await svc.activate(id=id, tenant_id=current_user.tenant_id)


@router.post("/{id}/deactivate", response_model=AddonGroupResponse, status_code=status.HTTP_200_OK)
async def deactivate_addon_group(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: AddonGroupService = Depends(_svc),
) -> AddonGroupResponse:
    return await svc.deactivate(id=id, tenant_id=current_user.tenant_id)


@router.delete("/{id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def delete_addon_group(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: AddonGroupService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Add-on group deleted.")


# ── Product attachment ──────────────────────────────────────────────────

@product_router.get("/products/{product_id}/addon-groups", response_model=list[ProductAddonGroupResponse])
async def list_product_addon_groups(
    product_id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: AddonGroupService = Depends(_svc),
) -> list[ProductAddonGroupResponse]:
    return await svc.list_for_product(product_id=product_id, tenant_id=current_user.tenant_id)


@product_router.post("/products/{product_id}/addon-groups", response_model=ProductAddonGroupResponse,
    status_code=status.HTTP_201_CREATED, summary="Attach a shared Add-on Group to a product")
async def attach_product_addon_group(
    product_id: UUID, data: ProductAddonGroupAttach,
    current_user: CurrentUser = Depends(get_current_user), svc: AddonGroupService = Depends(_svc),
) -> ProductAddonGroupResponse:
    return await svc.attach_to_product(product_id=product_id, tenant_id=current_user.tenant_id, data=data)


@product_router.delete("/products/{product_id}/addon-groups/{link_id}", response_model=MessageResponse)
async def detach_product_addon_group(
    product_id: UUID, link_id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: AddonGroupService = Depends(_svc),
) -> MessageResponse:
    await svc.detach_from_product(product_id=product_id, tenant_id=current_user.tenant_id, link_id=link_id)
    return MessageResponse(message="Add-on group detached.")
