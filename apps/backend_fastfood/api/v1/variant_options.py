# api/v1/variant_options.py
#
# Variant Option management — leaf nodes of a Variant Option Group.
# Prefix: /api/v1/variant-options

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.common import MessageResponse
from schemas.variant_option import (
    VariantOptionComponentSet,
    VariantOptionCreate,
    VariantOptionResponse,
    VariantOptionUpdate,
)
from services.variant_option_service import VariantOptionService

router = APIRouter(prefix="/variant-options", tags=["Variant Options"])


def _svc(db: AsyncSession = Depends(get_db)) -> VariantOptionService:
    return VariantOptionService(db)


@router.get("/", response_model=list[VariantOptionResponse], status_code=status.HTTP_200_OK)
async def list_variant_options(
    option_group_id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionService = Depends(_svc),
) -> list[VariantOptionResponse]:
    return await svc.list(option_group_id=option_group_id, tenant_id=current_user.tenant_id)


@router.post("/", response_model=VariantOptionResponse, status_code=status.HTTP_201_CREATED)
async def create_variant_option(
    option_group_id: UUID, data: VariantOptionCreate, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionService = Depends(_svc),
) -> VariantOptionResponse:
    return await svc.create(option_group_id=option_group_id, tenant_id=current_user.tenant_id, data=data)


@router.get("/{id}", response_model=VariantOptionResponse, status_code=status.HTTP_200_OK)
async def get_variant_option(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionService = Depends(_svc),
) -> VariantOptionResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch("/{id}", response_model=VariantOptionResponse, status_code=status.HTTP_200_OK)
async def update_variant_option(
    id: UUID, data: VariantOptionUpdate, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionService = Depends(_svc),
) -> VariantOptionResponse:
    return await svc.update(id=id, tenant_id=current_user.tenant_id, data=data)


@router.post("/{id}/activate", response_model=VariantOptionResponse, status_code=status.HTTP_200_OK)
async def activate_variant_option(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionService = Depends(_svc),
) -> VariantOptionResponse:
    return await svc.activate(id=id, tenant_id=current_user.tenant_id)


@router.post("/{id}/deactivate", response_model=VariantOptionResponse, status_code=status.HTTP_200_OK)
async def deactivate_variant_option(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionService = Depends(_svc),
) -> VariantOptionResponse:
    return await svc.deactivate(id=id, tenant_id=current_user.tenant_id)


@router.delete("/{id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def delete_variant_option(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Variant option deleted.")


@router.post("/{id}/component", response_model=VariantOptionResponse, status_code=status.HTTP_200_OK,
    summary="Track this option as a shared inventory component",
    description=(
        "Auto-creates the one real Product+Variant this option now represents (Laptop Store "
        "shareable-inventory model) — every product that attaches this option's group with "
        "usage_type='inventory_component' shares this same stock. No-op if already tracked."
    ))
async def set_variant_option_component(
    id: UUID, data: VariantOptionComponentSet,
    current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionService = Depends(_svc),
) -> VariantOptionResponse:
    return await svc.set_inventory_component(id=id, tenant_id=current_user.tenant_id, data=data)


@router.delete("/{id}/component", response_model=VariantOptionResponse, status_code=status.HTTP_200_OK,
    summary="Stop tracking this option as a shared inventory component",
    description="Blocked while the component still has stock anywhere or has ever been sold.")
async def unset_variant_option_component(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionService = Depends(_svc),
) -> VariantOptionResponse:
    return await svc.unset_inventory_component(id=id, tenant_id=current_user.tenant_id)
