# api/v1/variant_option_groups.py
#
# Variant Option Group management — shared at the Business level (spec Part B),
# reusable across products via product_variant_option_groups.
# Prefix: /api/v1/variant-option-groups

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user, get_current_business_id
from db.session import get_db
from schemas.common import MessageResponse
from schemas.variant_option_group import (
    CategoryVariantOptionGroupAttach,
    CategoryVariantOptionGroupResponse,
    CategoryVariantOptionGroupUpdate,
    ProductVariantOptionAllowedSet,
    ProductVariantOptionGroupAttach,
    ProductVariantOptionGroupResponse,
    ProductVariantOptionGroupUpdate,
    VariantOptionGroupCreate,
    VariantOptionGroupResponse,
    VariantOptionGroupUpdate,
)
from services.category_variant_option_group_service import CategoryVariantOptionGroupService
from services.variant_option_group_service import VariantOptionGroupService

router = APIRouter(prefix="/variant-option-groups", tags=["Variant Option Groups"])
product_router = APIRouter(tags=["Variant Option Groups"])
category_router = APIRouter(tags=["Variant Option Groups"])


def _svc(db: AsyncSession = Depends(get_db)) -> VariantOptionGroupService:
    return VariantOptionGroupService(db)


def _category_svc(db: AsyncSession = Depends(get_db)) -> CategoryVariantOptionGroupService:
    return CategoryVariantOptionGroupService(db)


@router.get("/", response_model=list[VariantOptionGroupResponse], status_code=status.HTTP_200_OK,
    summary="List the business's shared Variant Option Groups")
async def list_variant_option_groups(
    current_user: CurrentUser = Depends(get_current_user),
    business_id: UUID = Depends(get_current_business_id),
    svc: VariantOptionGroupService = Depends(_svc),
) -> list[VariantOptionGroupResponse]:
    return await svc.list(business_id=business_id, tenant_id=current_user.tenant_id)


@router.post("/", response_model=VariantOptionGroupResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a Variant Option Group in the shared library")
async def create_variant_option_group(
    data: VariantOptionGroupCreate,
    current_user: CurrentUser = Depends(get_current_user),
    business_id: UUID = Depends(get_current_business_id),
    svc: VariantOptionGroupService = Depends(_svc),
) -> VariantOptionGroupResponse:
    return await svc.create(business_id=business_id, tenant_id=current_user.tenant_id, data=data)


@router.get("/{id}", response_model=VariantOptionGroupResponse, status_code=status.HTTP_200_OK)
async def get_variant_option_group(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionGroupService = Depends(_svc),
) -> VariantOptionGroupResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch("/{id}", response_model=VariantOptionGroupResponse, status_code=status.HTTP_200_OK)
async def update_variant_option_group(
    id: UUID, data: VariantOptionGroupUpdate, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionGroupService = Depends(_svc),
) -> VariantOptionGroupResponse:
    return await svc.update(id=id, tenant_id=current_user.tenant_id, data=data)


@router.post("/{id}/activate", response_model=VariantOptionGroupResponse, status_code=status.HTTP_200_OK)
async def activate_variant_option_group(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionGroupService = Depends(_svc),
) -> VariantOptionGroupResponse:
    return await svc.activate(id=id, tenant_id=current_user.tenant_id)


@router.post("/{id}/deactivate", response_model=VariantOptionGroupResponse, status_code=status.HTTP_200_OK)
async def deactivate_variant_option_group(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionGroupService = Depends(_svc),
) -> VariantOptionGroupResponse:
    return await svc.deactivate(id=id, tenant_id=current_user.tenant_id)


@router.delete("/{id}", response_model=MessageResponse, status_code=status.HTTP_200_OK,
    description="Soft-deletes the group from the shared library. Historical sale_item_options are preserved.")
async def delete_variant_option_group(
    id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionGroupService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Variant option group deleted.")


# ── Product attachment ──────────────────────────────────────────────────

@product_router.get("/products/{product_id}/variant-option-groups", response_model=list[ProductVariantOptionGroupResponse])
async def list_product_variant_option_groups(
    product_id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionGroupService = Depends(_svc),
) -> list[ProductVariantOptionGroupResponse]:
    return await svc.list_for_product(product_id=product_id, tenant_id=current_user.tenant_id)


@product_router.post("/products/{product_id}/variant-option-groups", response_model=ProductVariantOptionGroupResponse,
    status_code=status.HTTP_201_CREATED, summary="Attach a shared Variant Option Group to a product")
async def attach_product_variant_option_group(
    product_id: UUID, data: ProductVariantOptionGroupAttach,
    current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionGroupService = Depends(_svc),
) -> ProductVariantOptionGroupResponse:
    return await svc.attach_to_product(product_id=product_id, tenant_id=current_user.tenant_id, data=data)


@product_router.patch("/products/{product_id}/variant-option-groups/{link_id}", response_model=ProductVariantOptionGroupResponse,
    summary="Change an attached group's usage type, selection rules, or default option")
async def update_product_variant_option_group(
    product_id: UUID, link_id: UUID, data: ProductVariantOptionGroupUpdate,
    current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionGroupService = Depends(_svc),
) -> ProductVariantOptionGroupResponse:
    return await svc.update_attachment(product_id=product_id, tenant_id=current_user.tenant_id, link_id=link_id, data=data)


@product_router.put("/products/{product_id}/variant-option-groups/{link_id}/allowed-options",
    response_model=ProductVariantOptionGroupResponse,
    summary="Restrict which of the group's shared options apply to this product")
async def set_product_variant_option_allowed(
    product_id: UUID, link_id: UUID, data: ProductVariantOptionAllowedSet,
    current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionGroupService = Depends(_svc),
) -> ProductVariantOptionGroupResponse:
    return await svc.set_allowed_options(product_id=product_id, tenant_id=current_user.tenant_id, link_id=link_id, data=data)


@product_router.delete("/products/{product_id}/variant-option-groups/{link_id}", response_model=MessageResponse)
async def detach_product_variant_option_group(
    product_id: UUID, link_id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: VariantOptionGroupService = Depends(_svc),
) -> MessageResponse:
    await svc.detach_from_product(product_id=product_id, tenant_id=current_user.tenant_id, link_id=link_id)
    return MessageResponse(message="Variant option group detached.")


# ── Category attachment ─────────────────────────────────────────────────
#
# Attaching/detaching a group here cascades onto every product currently in
# the category (see CategoryVariantOptionGroupService's module docstring for
# exactly what does and doesn't cascade). The product-level endpoints above
# are unchanged — a product can still be customized individually after
# inheriting a group from its category.

@category_router.get("/categories/{category_id}/variant-option-groups", response_model=list[CategoryVariantOptionGroupResponse],
    summary="List a category's Variant Option Group templates")
async def list_category_variant_option_groups(
    category_id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: CategoryVariantOptionGroupService = Depends(_category_svc),
) -> list[CategoryVariantOptionGroupResponse]:
    return await svc.list_for_category(category_id=category_id, tenant_id=current_user.tenant_id)


@category_router.post("/categories/{category_id}/variant-option-groups", response_model=CategoryVariantOptionGroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Attach a shared Variant Option Group to a category — cascades to every product in it")
async def attach_category_variant_option_group(
    category_id: UUID, data: CategoryVariantOptionGroupAttach,
    current_user: CurrentUser = Depends(get_current_user), svc: CategoryVariantOptionGroupService = Depends(_category_svc),
) -> CategoryVariantOptionGroupResponse:
    return await svc.attach_to_category(category_id=category_id, tenant_id=current_user.tenant_id, data=data)


@category_router.patch("/categories/{category_id}/variant-option-groups/{link_id}", response_model=CategoryVariantOptionGroupResponse,
    summary="Change the category template's required/selection rules (not retroactive to already-attached products)")
async def update_category_variant_option_group(
    category_id: UUID, link_id: UUID, data: CategoryVariantOptionGroupUpdate,
    current_user: CurrentUser = Depends(get_current_user), svc: CategoryVariantOptionGroupService = Depends(_category_svc),
) -> CategoryVariantOptionGroupResponse:
    return await svc.update_attachment(category_id=category_id, tenant_id=current_user.tenant_id, link_id=link_id, data=data)


@category_router.delete("/categories/{category_id}/variant-option-groups/{link_id}", response_model=MessageResponse,
    summary="Detach a group from the category — cascades a detach to its products where safe")
async def detach_category_variant_option_group(
    category_id: UUID, link_id: UUID, current_user: CurrentUser = Depends(get_current_user), svc: CategoryVariantOptionGroupService = Depends(_category_svc),
) -> MessageResponse:
    detached, skipped = await svc.detach_from_category(category_id=category_id, tenant_id=current_user.tenant_id, link_id=link_id)
    message = f"Variant option group detached from the category and {detached} product(s)."
    if skipped:
        message += f" {skipped} product(s) kept it because it's still in use by an existing Variant."
    return MessageResponse(message=message)
