# api/v1/categories.py
#
# Category management routes — tenant scoped.
# Categories sit under the tenant's Business: Tenant → Business → Category.
# A tenant has exactly one Business, so business_id is resolved server-side
# (get_current_business_id) rather than passed by the caller.
# Prefix: /api/v1/categories

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user, get_current_business_id
from db.session import get_db
from schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from schemas.common import MessageResponse
from services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


def _svc(db: AsyncSession = Depends(get_db)) -> CategoryService:
    return CategoryService(db)


@router.get(
    "/",
    response_model=list[CategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List categories",
    description="Returns all active categories for the current tenant's business.",
)
async def list_categories(
    include_inactive: bool = False,
    skip: int = 0,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    business_id: UUID = Depends(get_current_business_id),
    svc: CategoryService = Depends(_svc),
) -> list[CategoryResponse]:
    return await svc.list(
        business_id=business_id,
        tenant_id=current_user.tenant_id,
        include_inactive=include_inactive,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    description="Creates a category under the tenant's business.",
)
async def create_category(
    data: CategoryCreate,
    current_user: CurrentUser = Depends(get_current_user),
    business_id: UUID = Depends(get_current_business_id),
    svc: CategoryService = Depends(_svc),
) -> CategoryResponse:
    return await svc.create(
        business_id=business_id,
        tenant_id=current_user.tenant_id,
        data=data,
    )


@router.get(
    "/{id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get category",
)
async def get_category(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: CategoryService = Depends(_svc),
) -> CategoryResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch(
    "/{id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update category",
)
async def update_category(
    id: UUID,
    data: CategoryUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: CategoryService = Depends(_svc),
) -> CategoryResponse:
    return await svc.update(id=id, tenant_id=current_user.tenant_id, data=data)


@router.post(
    "/{id}/activate",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate category",
)
async def activate_category(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: CategoryService = Depends(_svc),
) -> CategoryResponse:
    return await svc.activate(id=id, tenant_id=current_user.tenant_id)


@router.post(
    "/{id}/deactivate",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate category",
)
async def deactivate_category(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: CategoryService = Depends(_svc),
) -> CategoryResponse:
    return await svc.deactivate(id=id, tenant_id=current_user.tenant_id)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete category",
    description="Soft-deletes the category. Products and sales data are retained.",
)
async def delete_category(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: CategoryService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Category deleted.")
