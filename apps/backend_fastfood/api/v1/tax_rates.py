# api/v1/tax_rates.py
#
# Tax rate management routes — tenant scoped.
#
# Tax rates are applied to sales at the POS. Only one rate may be the
# default at any time; the set-default endpoint enforces this invariant.
#
# Connected services / dependencies:
#   - services/tax_rate_service.py  — TaxRateService
#   - api/dependencies.py           — get_current_user
#   - db/session.py                 — get_db
#   - schemas/tax_rate.py           — TaxRateCreate, TaxRateUpdate, TaxRateResponse
#   - schemas/common.py             — MessageResponse
#
# Prefix: /api/v1/tax-rates

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.common import MessageResponse
from schemas.tax_rate import TaxRateCreate, TaxRateResponse, TaxRateUpdate
from services.tax_rate_service import TaxRateService

router = APIRouter(prefix="/tax-rates", tags=["Tax Rates"])


def _svc(db: AsyncSession = Depends(get_db)) -> TaxRateService:
    """Dependency that instantiates TaxRateService with the request's DB session."""
    return TaxRateService(db)


@router.get(
    "/",
    response_model=list[TaxRateResponse],
    status_code=status.HTTP_200_OK,
    summary="List tax rates",
    description="Returns all tax rates for the current tenant.",
)
async def list_tax_rates(
    current_user: CurrentUser = Depends(get_current_user),
    svc: TaxRateService = Depends(_svc),
) -> list[TaxRateResponse]:
    return await svc.list(tenant_id=current_user.tenant_id)


@router.post(
    "/",
    response_model=TaxRateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tax rate",
    description=(
        "Creates a new tax rate. If is_default=True, all other tax rates for this tenant "
        "are automatically set to is_default=False."
    ),
)
async def create_tax_rate(
    data: TaxRateCreate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TaxRateService = Depends(_svc),
) -> TaxRateResponse:
    return await svc.create(tenant_id=current_user.tenant_id, data=data)


@router.get(
    "/{id}",
    response_model=TaxRateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tax rate",
)
async def get_tax_rate(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TaxRateService = Depends(_svc),
) -> TaxRateResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch(
    "/{id}",
    response_model=TaxRateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update tax rate",
    description="Partially update a tax rate. Only provided fields are changed.",
)
async def update_tax_rate(
    id: UUID,
    data: TaxRateUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TaxRateService = Depends(_svc),
) -> TaxRateResponse:
    return await svc.update(id=id, tenant_id=current_user.tenant_id, data=data)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete tax rate",
    description="Soft-deletes the tax rate.",
)
async def delete_tax_rate(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TaxRateService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Tax rate deleted.")


@router.post(
    "/{id}/set-default",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Set tax rate as default",
    description=(
        "Marks this tax rate as the tenant default. "
        "All other tax rates for this tenant are automatically cleared."
    ),
)
async def set_default_tax_rate(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: TaxRateService = Depends(_svc),
) -> MessageResponse:
    await svc.set_default(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Tax rate set as default.")
