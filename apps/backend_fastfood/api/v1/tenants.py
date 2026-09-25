# api/v1/tenants.py
#
# Tenant management routes — super-admin only.
# Tenant is the root of the hierarchy: Tenant → Business → Branch → Device → User → Sale.
# NOTE: this router is not currently mounted in app/main.py — the live tenant
# creation path is the platform onboarding endpoint (api/platform/onboarding.py).

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.common import MessageResponse
from schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from services.tenant_service import TenantService


router = APIRouter(prefix="/tenants", tags=["Tenants"])


def _service(db: AsyncSession = Depends(get_db)) -> TenantService:
    """Dependency that builds a TenantService bound to the current DB session."""
    return TenantService(db)


# ----------------------------------------------------------------
# LIST
# ----------------------------------------------------------------

@router.get(
    "/",
    response_model=list[TenantResponse],
    status_code=status.HTTP_200_OK,
    summary="List tenants",
)
async def list_tenants(
    skip: int = 0,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    service: TenantService = Depends(_service),
) -> list[TenantResponse]:
    return await service.list(skip=skip, limit=limit)


# ----------------------------------------------------------------
# CREATE
# ----------------------------------------------------------------

@router.post(
    "/",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tenant",
    description="Register a new business account. tenant_code must be globally unique.",
)
async def create_tenant(
    data: TenantCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: TenantService = Depends(_service),
) -> TenantResponse:
    return await service.create(data)


# ----------------------------------------------------------------
# GET
# ----------------------------------------------------------------

@router.get(
    "/{id}",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tenant",
)
async def get_tenant(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: TenantService = Depends(_service),
) -> TenantResponse:
    return await service.get(id)


# ----------------------------------------------------------------
# UPDATE
# ----------------------------------------------------------------

@router.patch(
    "/{id}",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Update tenant",
    description="Partially update a tenant. Only provided fields are changed.",
)
async def update_tenant(
    id: UUID,
    data: TenantUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service: TenantService = Depends(_service),
) -> TenantResponse:
    return await service.update(id, data)


# ----------------------------------------------------------------
# ACTIVATE / DEACTIVATE
# ----------------------------------------------------------------

@router.post(
    "/{id}/activate",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate tenant",
)
async def activate_tenant(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: TenantService = Depends(_service),
) -> TenantResponse:
    return await service.activate(id)


@router.post(
    "/{id}/deactivate",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate tenant",
)
async def deactivate_tenant(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: TenantService = Depends(_service),
) -> TenantResponse:
    return await service.deactivate(id)


# ----------------------------------------------------------------
# DELETE (soft)
# ----------------------------------------------------------------

@router.delete(
    "/{id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete tenant",
    description="Soft-deletes the tenant. Data is retained but the account becomes inaccessible.",
)
async def delete_tenant(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: TenantService = Depends(_service),
) -> MessageResponse:
    return await service.delete(id)
