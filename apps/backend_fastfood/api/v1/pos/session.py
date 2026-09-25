# api/v1/pos/session.py
#
# Cashier shift session management.
# One OPEN session per device at a time.
#
# Prefix: /api/v1/pos/session

from __future__ import annotations
from api.v1.pos._guards import operational_cashier

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentCashier, get_current_cashier
from db.session import get_db
from schemas.pos_session import (
    SessionCloseRequest,
    SessionCloseResponse,
    SessionOpenRequest,
    SessionResponse,
    SessionSummaryResponse,
)
from services.cashier_session_service import CashierSessionService

router = APIRouter(prefix="/session", tags=["POS — Session"])


def _svc(db: AsyncSession = Depends(get_db)) -> CashierSessionService:
    return CashierSessionService(db)


@router.post(
    "/open",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Open cashier session",
    description=(
        "Called when the cashier starts a shift. "
        "Records the opening cash amount for end-of-day reconciliation. "
        "Raises 422 if a session is already open on this device."
    ),
)
async def open_session(
    data: SessionOpenRequest,
    cashier: CurrentCashier = Depends(operational_cashier),
    svc: CashierSessionService = Depends(_svc),
) -> SessionResponse:
    return await svc.open(
        device_id=cashier.device_id,
        user_id=cashier.user_id,
        branch_id=cashier.branch_id,
        tenant_id=cashier.tenant_id,
        data=data,
    )


@router.post(
    "/close",
    response_model=SessionCloseResponse,
    summary="Close cashier session",
    description=(
        "Called at end of shift. Records the closing cash amount and returns the "
        "shift reconciliation summary plus the cash variance. "
        "Raises 404 if no session is open on this device."
    ),
)
async def close_session(
    data: SessionCloseRequest,
    cashier: CurrentCashier = Depends(operational_cashier),
    svc: CashierSessionService = Depends(_svc),
) -> SessionCloseResponse:
    return await svc.close(
        device_id=cashier.device_id,
        user_id=cashier.user_id,
        tenant_id=cashier.tenant_id,
        data=data,
    )


@router.get(
    "/summary",
    response_model=SessionSummaryResponse,
    summary="Current shift reconciliation summary",
    description=(
        "Returns the open session plus live reconciliation figures — sales count, "
        "gross total, totals by payment method, and expected cash "
        "(opening cash + cash sales). Raises 404 if no session is open."
    ),
)
async def get_session_summary(
    cashier: CurrentCashier = Depends(operational_cashier),
    svc: CashierSessionService = Depends(_svc),
) -> SessionSummaryResponse:
    return await svc.summary(
        device_id=cashier.device_id,
        tenant_id=cashier.tenant_id,
    )


@router.get(
    "/current",
    response_model=SessionResponse,
    summary="Get current session",
    description=(
        "Returns the CALLING cashier's own open session on this device. "
        "Raises 404 if none — including when a different cashier left a "
        "session open on this same device; that is never handed to the "
        "caller as if it were theirs."
    ),
)
async def get_current_session(
    cashier: CurrentCashier = Depends(operational_cashier),
    svc: CashierSessionService = Depends(_svc),
) -> SessionResponse:
    return await svc.get_current(
        device_id=cashier.device_id,
        user_id=cashier.user_id,
        tenant_id=cashier.tenant_id,
    )


@router.get(
    "/history",
    response_model=list[SessionResponse],
    summary="Past shifts for this cashier",
    description=(
        "Returns this cashier's closed shifts, newest first, across every "
        "device/branch they worked on — their personal shift history."
    ),
)
async def list_session_history(
    limit: int = Query(default=50, ge=1, le=200),
    cashier: CurrentCashier = Depends(operational_cashier),
    svc: CashierSessionService = Depends(_svc),
) -> list[SessionResponse]:
    return await svc.list_history(
        user_id=cashier.user_id,
        tenant_id=cashier.tenant_id,
        limit=limit,
    )


@router.get(
    "/history/{session_id}/summary",
    response_model=SessionSummaryResponse,
    summary="Reconciliation summary for one past shift",
    description=(
        "Same shape as GET /session/summary but works for a CLOSED session "
        "looked up by id, so a shift's totals stay reviewable after close — "
        "not just once, at the moment of closing. Only the cashier who "
        "owned the shift can view it."
    ),
)
async def get_session_history_summary(
    session_id: UUID,
    cashier: CurrentCashier = Depends(operational_cashier),
    svc: CashierSessionService = Depends(_svc),
) -> SessionSummaryResponse:
    return await svc.history_summary(
        session_id=session_id,
        user_id=cashier.user_id,
        tenant_id=cashier.tenant_id,
    )
