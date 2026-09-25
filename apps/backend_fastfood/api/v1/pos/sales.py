# api/v1/pos/sales.py
#
# POS sale endpoints — use cashier JWT.
# One atomic request: sale + payments → receipt.
#
# Receipt access is split into two paths to enforce intentional access:
#   GET /{id}/receipt      — only the cashier who made the sale can use this
#   GET /lookup            — any cashier can look up any branch sale by sale_number;
#                            requires knowing the exact number (explicit intent)
#
# Prefix: /api/v1/pos/sales

from __future__ import annotations
from datetime import datetime
from api.v1.pos._guards import operational_cashier

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentCashier, get_current_cashier
from db.session import get_db
from schemas.pos_sale import PosSaleCreate, PosReceiptResponse
from schemas.refund import PosCancelCreate, PosRefundResult, PosReturnCreate
from services.pos_sale_service import PosSaleService
from services.pos_return_service import PosReturnService

router = APIRouter(prefix="/sales", tags=["POS — Sales"])


def _svc(db: AsyncSession = Depends(get_db)) -> PosSaleService:
    return PosSaleService(db)


def _return_svc(db: AsyncSession = Depends(get_db)) -> PosReturnService:
    return PosReturnService(db)


@router.post(
    "",
    response_model=PosReceiptResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
@router.post(
    "/",
    response_model=PosReceiptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create POS sale",
    description=(
        "Submit a complete sale (items + payments) from the POS app. "
        "branch_id, device_id, and user_id are taken from the cashier JWT — "
        "the app does not need to include them. "
        "Returns a structured receipt ready to render or send to a printer."
    ),
)
async def create_sale(
    data: PosSaleCreate,
    cashier: CurrentCashier = Depends(operational_cashier),
    svc: PosSaleService = Depends(_svc),
) -> PosReceiptResponse:
    return await svc.create(
        data=data,
        branch_id=cashier.branch_id,
        device_id=cashier.device_id,
        user_id=cashier.user_id,
        tenant_id=cashier.tenant_id,
    )


@router.get(
    "/lookup",
    response_model=PosReceiptResponse,
    summary="Look up any branch sale by sale number",
    description=(
        "Explicitly look up any completed sale in this branch by its human-readable "
        "sale_number (e.g. 'LHR01-26-000128'). Unlike GET /{id}/receipt, this endpoint "
        "is not restricted to the calling cashier's own sales — any cashier on the "
        "same branch can retrieve the receipt. "
        "Requiring the exact sale number rather than a UUID creates an audit trail of "
        "deliberate intent. The Flutter app shows a confirmation screen before printing."
    ),
)
async def lookup_receipt(
    sale_number: str = Query(..., description="Exact sale number printed on the receipt."),
    cashier: CurrentCashier = Depends(operational_cashier),
    svc: PosSaleService = Depends(_svc),
) -> PosReceiptResponse:
    return await svc.get_receipt_by_number(
        sale_number=sale_number,
        branch_id=cashier.branch_id,
        tenant_id=cashier.tenant_id,
    )


@router.get("/recent", response_model=list[PosReceiptResponse], summary="List this cashier's recent bills")
async def recent_sales(
    limit: int = Query(20, ge=1, le=200),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    session_id: UUID | None = None,
    cashier: CurrentCashier = Depends(operational_cashier),
    svc: PosSaleService = Depends(_svc),
) -> list[PosReceiptResponse]:
    return await svc.list_recent(
        cashier.branch_id, cashier.device_id, cashier.user_id,
        cashier.tenant_id, limit, date_from, date_to, session_id,
    )


@router.post("/{id}/cancel", response_model=PosRefundResult, summary="Cancel a same-shift bill")
async def cancel_sale(
    id: UUID,
    data: PosCancelCreate,
    cashier: CurrentCashier = Depends(operational_cashier),
    svc: PosReturnService = Depends(_return_svc),
) -> PosRefundResult:
    return await svc.cancel(sale_id=id, data=data, tenant_id=cashier.tenant_id,
                            branch_id=cashier.branch_id, device_id=cashier.device_id,
                            user_id=cashier.user_id)


@router.post("/{id}/return", response_model=PosRefundResult, summary="Return selected invoice items")
async def return_sale_items(
    id: UUID,
    data: PosReturnCreate,
    cashier: CurrentCashier = Depends(operational_cashier),
    svc: PosReturnService = Depends(_return_svc),
) -> PosRefundResult:
    return await svc.return_items(sale_id=id, data=data, tenant_id=cashier.tenant_id,
                                  branch_id=cashier.branch_id, device_id=cashier.device_id,
                                  user_id=cashier.user_id)


@router.get(
    "/{id}/receipt",
    response_model=PosReceiptResponse,
    summary="Get receipt for own sale",
    description=(
        "Re-fetch the receipt for a sale made by the calling cashier. "
        "Returns 404 if the sale belongs to a different cashier. "
        "Use GET /lookup?sale_number=... to print another cashier's sale."
    ),
)
async def get_receipt(
    id: UUID,
    cashier: CurrentCashier = Depends(operational_cashier),
    svc: PosSaleService = Depends(_svc),
) -> PosReceiptResponse:
    return await svc.get_receipt(
        sale_id=id,
        branch_id=cashier.branch_id,
        user_id=cashier.user_id,
        tenant_id=cashier.tenant_id,
    )


@router.post("/offers/preview")
async def preview_offers(data: PosSaleCreate, promo_code: str | None = None,
        cashier: CurrentCashier = Depends(operational_cashier), db: AsyncSession = Depends(get_db)):
    from services.checkout_validation import validate_catalog
    from services.offer_service import OfferService
    await validate_catalog(db, data, cashier.tenant_id, cashier.branch_id)
    offers = await OfferService(db).calculate(data, cashier.tenant_id, cashier.branch_id, promo_code=promo_code)
    return [{key:value for key,value in offer.items() if key != "model"} for offer in offers]
