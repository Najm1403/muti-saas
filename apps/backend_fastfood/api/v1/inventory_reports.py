# api/v1/inventory_reports.py
#
# Read-only, tenant-wide inventory reports — current/in/out/low stock, the
# stock-adjustment movement ledger, and the branch-to-branch transfer
# register. No business logic here — delegates entirely to
# InventoryReportService.
# Prefix: /api/v1/inventory-reports

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.branch_access import visible_branches
from api.dependencies import CurrentUser, get_current_user, require_module, require_permission
from core.exceptions import ForbiddenError
from db.session import get_db
from schemas.inventory_report import StockMovementRow, StockReportRow, StockTransferRow
from services.inventory_report_service import InventoryReportService
from services.pdf_report_service import build_pdf, data_table, get_branding

router = APIRouter(
    prefix="/inventory-reports", tags=["Inventory Reports"],
    dependencies=[Depends(require_module("inventory"))],
)
view = require_permission("inventory.view")


def _svc(db: AsyncSession = Depends(get_db)) -> InventoryReportService:
    return InventoryReportService(db)


async def _check_branch(current_user: CurrentUser, db: AsyncSession, branch_id: UUID | None) -> None:
    allowed = await visible_branches(db, current_user)
    if allowed is not None and branch_id is not None and branch_id not in allowed:
        raise ForbiddenError("No access to the selected branch.")


@router.get(
    "/stock",
    response_model=list[StockReportRow],
    status_code=status.HTTP_200_OK,
    summary="Stock report (current / in stock / out of stock / low stock)",
)
async def get_stock_report(
    branch_id: UUID | None = None,
    status_: str = Query("all", alias="status"),
    q: str | None = None,
    current_user: CurrentUser = Depends(view),
    svc: InventoryReportService = Depends(_svc),
) -> list[StockReportRow]:
    await _check_branch(current_user, svc.db, branch_id)
    return await svc.stock_report(
        tenant_id=current_user.tenant_id, branch_id=branch_id, status=status_, q=q,
    )


@router.get(
    "/movements",
    response_model=list[StockMovementRow],
    status_code=status.HTTP_200_OK,
    summary="Stock movement ledger (every stock-in/stock-out event)",
)
async def get_movement_report(
    branch_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    movement_type: str | None = None,
    current_user: CurrentUser = Depends(view),
    svc: InventoryReportService = Depends(_svc),
) -> list[StockMovementRow]:
    await _check_branch(current_user, svc.db, branch_id)
    return await svc.movement_report(
        tenant_id=current_user.tenant_id, branch_id=branch_id,
        date_from=date_from, date_to=date_to, movement_type=movement_type,
    )


@router.get(
    "/transfers",
    response_model=list[StockTransferRow],
    status_code=status.HTTP_200_OK,
    summary="Branch-to-branch stock transfer register",
)
async def get_transfer_report(
    branch_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_user: CurrentUser = Depends(view),
    svc: InventoryReportService = Depends(_svc),
) -> list[StockTransferRow]:
    await _check_branch(current_user, svc.db, branch_id)
    return await svc.transfer_report(
        tenant_id=current_user.tenant_id, branch_id=branch_id,
        date_from=date_from, date_to=date_to,
    )


# ── PDF exports — real A4 documents (reportlab), not a browser print ────


def _pdf(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/stock/pdf", summary="Stock report — PDF")
async def get_stock_report_pdf(
    branch_id: UUID | None = None,
    status_: str = Query("all", alias="status"),
    q: str | None = None,
    current_user: CurrentUser = Depends(view),
    svc: InventoryReportService = Depends(_svc),
) -> Response:
    await _check_branch(current_user, svc.db, branch_id)
    rows = await svc.stock_report(
        tenant_id=current_user.tenant_id, branch_id=branch_id, status=status_, q=q,
    )
    business_name, logo_bytes, branch_line, currency = await get_branding(
        svc.db, current_user.tenant_id, branch_id,
    )

    total_qty = sum(r.current_stock for r in rows)
    total_value = sum(r.stock_value for r in rows)
    table = data_table(
        ["SKU", "Product", "Category", "Sale Price", "Current Stock", "Stock Value", "Last Stock In"],
        [
            [r.sku, r.product_name, r.category_name, f"{currency} {r.sale_price:.2f}",
             r.current_stock, f"{currency} {r.stock_value:.2f}",
             r.last_stock_in.strftime("%d %b %Y") if r.last_stock_in else "—"]
            for r in rows
        ],
        numeric_cols={3, 4, 5},
        col_fractions=[0.15, 0.24, 0.12, 0.14, 0.11, 0.14, 0.10],
        totals=["", "", "", "", total_qty, f"{currency} {total_value:.2f}", ""] if rows else None,
    )
    pdf_bytes = await build_pdf(
        business_name=business_name, logo_bytes=logo_bytes, branch_line=branch_line,
        report_title="Stock Report", flowables=[table],
    )
    return _pdf(pdf_bytes, "stock-report.pdf")


@router.get("/movements/pdf", summary="Stock movement ledger — PDF")
async def get_movement_report_pdf(
    branch_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    movement_type: str | None = None,
    current_user: CurrentUser = Depends(view),
    svc: InventoryReportService = Depends(_svc),
) -> Response:
    await _check_branch(current_user, svc.db, branch_id)
    rows = await svc.movement_report(
        tenant_id=current_user.tenant_id, branch_id=branch_id,
        date_from=date_from, date_to=date_to, movement_type=movement_type,
    )
    business_name, logo_bytes, branch_line, _currency = await get_branding(
        svc.db, current_user.tenant_id, branch_id,
    )

    table = data_table(
        ["Date", "SKU", "Product", "Branch", "Type", "Qty Change", "Resulting Qty", "By", "Note"],
        [
            [r.date.strftime("%d %b %Y"), r.sku, r.product_name, r.branch_name, r.movement_type,
             r.quantity_change if r.quantity_change is not None else "—",
             r.resulting_quantity, r.recorded_by or "—", r.note or ""]
            for r in rows
        ],
        numeric_cols={5, 6},
        col_fractions=[0.09, 0.14, 0.18, 0.09, 0.11, 0.08, 0.10, 0.11, 0.10],
    )
    pdf_bytes = await build_pdf(
        business_name=business_name, logo_bytes=logo_bytes, branch_line=branch_line,
        report_title="Stock Movement", flowables=[table],
    )
    return _pdf(pdf_bytes, "stock-movement.pdf")


@router.get("/transfers/pdf", summary="Branch-to-branch stock transfer register — PDF")
async def get_transfer_report_pdf(
    branch_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    current_user: CurrentUser = Depends(view),
    svc: InventoryReportService = Depends(_svc),
) -> Response:
    await _check_branch(current_user, svc.db, branch_id)
    rows = await svc.transfer_report(
        tenant_id=current_user.tenant_id, branch_id=branch_id,
        date_from=date_from, date_to=date_to,
    )
    business_name, logo_bytes, branch_line, _currency = await get_branding(
        svc.db, current_user.tenant_id, branch_id,
    )

    table = data_table(
        ["Date", "SKU", "Product", "From Branch", "To Branch", "Quantity", "By", "Note"],
        [
            [r.date.strftime("%d %b %Y"), r.sku, r.product_name, r.from_branch, r.to_branch,
             r.quantity, r.recorded_by or "—", r.note or ""]
            for r in rows
        ],
        numeric_cols={5},
        col_fractions=[0.10, 0.13, 0.20, 0.13, 0.13, 0.09, 0.12, 0.10],
    )
    pdf_bytes = await build_pdf(
        business_name=business_name, logo_bytes=logo_bytes, branch_line=branch_line,
        report_title="Stock Transfers", flowables=[table],
    )
    return _pdf(pdf_bytes, "stock-transfers.pdf")
