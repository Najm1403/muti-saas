# api/v1/payments.py
#
# Payment routes — tenant scoped.
#
# Position in hierarchy:
#   Tenant → Restaurant → Branch → Sale → Payment
#
# Payments are always linked to an existing sale.  A sale may have multiple
# payments (split payment: e.g. part cash, part card for one transaction).
#
# Typical flow:
#   1. POST /sales/       → create the sale
#   2. POST /payments/    → record payment(s) against that sale
#   3. GET  /payments/?sale_id= → list all payments for a sale
#
# Connected services / dependencies:
#   - services/payment_service.py  — PaymentService (create, get, list_by_sale)
#   - api/dependencies.py          — get_current_user
#   - db/session.py                — get_db
#   - schemas/payment.py           — PaymentCreate, PaymentResponse
#
# Prefix: /api/v1/payments

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user
from db.session import get_db
from schemas.payment import PaymentCreate, PaymentResponse
from services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


def _svc(db: AsyncSession = Depends(get_db)) -> PaymentService:
    """Dependency that instantiates PaymentService with the request's DB session."""
    return PaymentService(db)


@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record payment",
    description=(
        "Records a payment against an existing sale. "
        "May be called multiple times for the same sale_id (split payment). "
        "payment_method must be one of core.payment_methods.PAYMENT_METHODS — "
        "Cash / JazzCash / EasyPaisa / Online Transfer / Credit Card (case/spacing "
        "insensitive; normalised to the canonical label). "
        "reference is optional — use for card transaction or receipt numbers. "
        "Returns 404 if sale_id belongs to a different tenant."
    ),
)
async def create_payment(
    data: PaymentCreate,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PaymentService = Depends(_svc),
) -> PaymentResponse:
    return await svc.create(data=data, tenant_id=current_user.tenant_id)


@router.get(
    "/",
    response_model=list[PaymentResponse],
    status_code=status.HTTP_200_OK,
    summary="List payments for a sale",
    description=(
        "Returns all payment records for the given sale. "
        "sale_id must belong to the current tenant. "
        "Returns 404 (not an empty list) if the sale is not found or cross-tenant."
    ),
)
async def list_payments_by_sale(
    sale_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PaymentService = Depends(_svc),
) -> list[PaymentResponse]:
    return await svc.list_by_sale(sale_id=sale_id, tenant_id=current_user.tenant_id)


@router.get(
    "/{id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get payment",
    description="Returns a single payment record. Returns 404 if cross-tenant.",
)
async def get_payment(
    id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    svc: PaymentService = Depends(_svc),
) -> PaymentResponse:
    return await svc.get(id=id, tenant_id=current_user.tenant_id)
