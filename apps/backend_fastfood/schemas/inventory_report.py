# schemas/inventory_report.py
#
# Read-only, tenant-wide inventory reports — current/in/out/low stock, the
# stock-adjustment movement ledger, and the branch-to-branch transfer
# register. See services/inventory_report_service.py.

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from schemas.common import APIBaseSchema

STOCK_REPORT_STATUSES = ("all", "in_stock", "out_of_stock", "low_stock")


class StockReportRow(APIBaseSchema):
    sku: str
    product_name: str
    category_name: str
    sale_price: Decimal
    cost_price: Decimal | None = None
    current_stock: int
    stock_value: Decimal
    last_stock_in: datetime | None = None


class StockMovementRow(APIBaseSchema):
    date: datetime
    sku: str
    product_name: str
    branch_name: str
    movement_type: str
    quantity_change: int | None = None
    resulting_quantity: int
    recorded_by: str | None = None
    note: str | None = None


class StockTransferRow(APIBaseSchema):
    date: datetime
    sku: str
    product_name: str
    from_branch: str
    to_branch: str
    quantity: int
    recorded_by: str | None = None
    note: str | None = None
