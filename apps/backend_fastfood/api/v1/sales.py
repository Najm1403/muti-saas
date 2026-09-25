# api/v1/sales.py
#
# POS sale transaction routes — tenant scoped.
#
# Position in hierarchy:
#   Tenant → Restaurant → Branch → Device → Sale → SaleItems → SaleItemOptions
#
# This is the core POS endpoint.  The Android tablet (or web POS) submits a
# complete SaleCreate payload with all items and selected options pre-calculated.
# The server validates ownership and totals, then persists the sale atomically.
#
# Payment flow (separate from sale creation):
#   1. POST /sales/          → creates the sale, returns SaleResponse
#   2. POST /payments/       → adds payment(s) to the sale (supports split payment)
#   3. GET  /payments/?sale_id=  → lists all payments for the sale
#
# Offline-first support:
#   The Android app generates UUIDs locally (sale.id, item ids, option ids) and
#   queues sales during offline periods.  On sync, these UUIDs are submitted to
#   the server which preserves them.  Omitting id fields causes server-generated UUIDs.
#
# Connected services / dependencies:
#   - services/sale_service.py    — SaleService (validates, creates, lists, status update)
#   - api/dependencies.py         — get_current_user
#   - db/session.py               — get_db
#   - schemas/sale.py             — SaleCreate, SaleResponse, SaleListResponse, SaleStatusUpdate
#   - schemas/common.py           — MessageResponse
#
# Prefix: /api/v1/sales

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.common import MessageResponse
from schemas.sale import SaleCreate, SaleListResponse, SaleResponse, SaleStatusUpdate
from services.sale_service import SaleService

router = APIRouter(prefix="/sales", tags=["Sales"])


def _svc(db: AsyncSession = Depends(get_db)) -> SaleService:
    """Dependency that instantiates SaleService with the request's DB session."""
    return SaleService(db)


@router.get(
    "/",
    response_model=list[SaleListResponse],
    status_code=status.HTTP_200_OK,
    summary="List sales",
    description=(
        "Returns a paginated list of sales for a branch, ordered newest first. "
        "Returns lightweight SaleListResponse (no nested items) for performance. "
        "Use GET /sales/{id} for the full nested detail. "
        "branch_id must belong to the current tenant."
    ),
)
async def list_sales(
    branch_id: UUID,
    date_from: datetime | None = Query(None, description="Filter: sales on or after this datetime (UTC)."),
    date_to: datetime | None = Query(None, description="Filter: sales on or before this datetime (UTC)."),
    sale_status: str | None = Query(None, alias="status", description="Filter by status: COMPLETED, CANCELLED, or REFUNDED."),
    user_id: UUID | None = Query(None, description="Filter by cashier user."),
    session_id: UUID | None = Query(None, description="Filter by cashier shift."),
    skip: int = 0,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    svc: SaleService = Depends(_svc),
) -> list[SaleListResponse]:
    return await svc.list(
        branch_id=branch_id,
        tenant_id=current_user.tenant_id,
        date_from=date_from,
        date_to=date_to,
        status=sale_status,
        user_id=user_id,
        session_id=session_id,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create sale",
    description=(
        "Records a complete POS sale transaction. "
        "The server validates: branch/device/user ownership, device is active, "
        "user is active, and all submitted totals are arithmetically correct. "
        "Returns the full nested SaleResponse (with items and options). "
        "After creating the sale, submit payment(s) via POST /payments/."
    ),
)
async def create_sale(
    data: SaleCreate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: SaleService = Depends(_svc),
) -> SaleResponse:
    return await svc.create(data=data, tenant_id=current_user.tenant_id)


@router.get(
    "/{id}",
    response_model=SaleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sale",
    description=(
        "Returns a fully nested sale (with items and selected options). "
        "Returns 404 if the sale belongs to a different tenant."
    ),
)
async def get_sale(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: SaleService = Depends(_svc),
) -> SaleResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)


@router.patch(
    "/{id}/status",
    response_model=SaleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update sale status",
    description=(
        "Transition a sale to a new status. "
        "Allowed values: COMPLETED, CANCELLED, REFUNDED. "
        "Use CANCELLED only for an unpaid pending sale. "
        "Use REFUNDED after recording a refund via the refunds endpoint."
    ),
)
async def update_sale_status(
    id: UUID,
    data: SaleStatusUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: SaleService = Depends(_svc),
) -> SaleResponse:
    return await svc.update_status(id=id, tenant_id=current_user.tenant_id, data=data)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete sale",
    description=(
        "Soft-deletes the sale. "
        "Linked payments and refund records are retained for accounting. "
        "The sale stops appearing in list results."
    ),
)
async def delete_sale(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: SaleService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id=id, tenant_id=current_user.tenant_id)
    return MessageResponse(message="Sale deleted.")
