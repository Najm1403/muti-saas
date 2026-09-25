# api/v1/refunds.py
#
# Refund management endpoints — management API (tenant JWT).
#
# A refund is always issued against a specific sale. Supports full and partial
# refunds. The original Sale record is never modified except its status, which
# is set to "REFUNDED" when the refund covers the sale's full total.
#
# Prefix: /api/v1/refunds

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.refund import RefundCreate, RefundResponse
from services.refund_service import RefundService

router = APIRouter(prefix="/refunds", tags=["Refunds"])


def _svc(db: AsyncSession = Depends(get_db)) -> RefundService:
    return RefundService(db)


@router.post(
    "/",
    response_model=RefundResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create refund",
    description=(
        "Issue a full or partial refund against an existing sale. "
        "At least one item must be specified. The refund amount must equal "
        "the sum of the item amounts. "
        "Returns 409 if refund_number already exists for the branch. "
        "Returns 404 if the sale or any referenced SaleItem cannot be found."
    ),
)
async def create_refund(
    data: RefundCreate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: RefundService = Depends(_svc),
) -> RefundResponse:
    return await svc.create(data=data, tenant_id=current_user.tenant_id, created_by=current_user.user_id)


@router.get(
    "/{id}",
    response_model=RefundResponse,
    summary="Get refund",
    description="Return a single refund by UUID.",
)
async def get_refund(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: RefundService = Depends(_svc),
) -> RefundResponse:
    return await svc.get(refund_id=id, tenant_id=current_user.tenant_id)


@router.get(
    "/sale/{sale_id}",
    response_model=list[RefundResponse],
    summary="List refunds for a sale",
    description="Return all refunds issued against a sale, newest first.",
)
async def list_refunds_for_sale(
    sale_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: RefundService = Depends(_svc),
) -> list[RefundResponse]:
    return await svc.list_for_sale(
        sale_id=sale_id, tenant_id=current_user.tenant_id
    )
