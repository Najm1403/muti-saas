"""Catalog down-sync and sale up-sync stay visible across POS and tenant services."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from schemas.pos_sale import (
    PosSaleCreate,
    PosSaleItemCreate,
    PosSalePaymentCreate,
    PosSaleVariantOptionSnapshot,
)
from services.pos_sale_service import PosSaleService
from services.pos_sync_service import PosSyncService


def test_pos_sale_create_accepts_slash_and_slashless_paths():
    from app.main import app

    post_paths = {
        route.path
        for route in app.routes
        if "POST" in getattr(route, "methods", set())
    }
    assert "/api/v1/pos/sales" in post_paths
    assert "/api/v1/pos/sales/" in post_paths
from services.sale_service import SaleService
from services.tenant_report_service import TenantReportService


@pytest.mark.asyncio
async def test_catalog_download_and_pos_sale_reach_tenant_dashboard(db, H):
    snapshot = await PosSyncService(db).full_sync(
        H["branch_a"].id, H["tenant_a"].id
    )
    assert any(product.id == H["prod_a"].id for product in snapshot.products)
    synced_variant = next(
        variant for variant in snapshot.variants if variant.id == H["variant_a"].id
    )
    assert synced_variant.product_name == H["prod_a"].name
    assert synced_variant.variant_name

    sale_number = f"ROUNDTRIP-{uuid4().hex[:10]}"
    sale = PosSaleCreate(
        id=uuid4(),
        sale_number=sale_number,
        sold_at=datetime.now(timezone.utc),
        subtotal=Decimal("11.49"),
        total=Decimal("11.49"),
        items=[
            PosSaleItemCreate(
                variant_id=H["variant_a"].id,
                product_id=H["prod_a"].id,
                product_name=H["prod_a"].name,
                quantity=1,
                unit_price=Decimal("11.49"),
                total=Decimal("11.49"),
                options=[
                    PosSaleVariantOptionSnapshot(
                        variant_option_id=H["opt_a"].id,
                        option_name=H["opt_a"].name,
                    )
                ],
            )
        ],
        payments=[PosSalePaymentCreate(payment_method="Cash", amount=Decimal("11.49"))],
    )

    receipt = await PosSaleService(db).create(
        sale,
        H["branch_a"].id,
        H["device_a"].id,
        H["user_a"].id,
        H["tenant_a"].id,
    )
    assert receipt.sale_number == sale_number

    dashboard_sales = await SaleService(db).list(
        H["branch_a"].id, H["tenant_a"].id
    )
    dashboard_sale = next(row for row in dashboard_sales if row.sale_number == sale_number)
    assert dashboard_sale.id == receipt.sale_id
    assert dashboard_sale.sale_number != str(dashboard_sale.id)
    assert dashboard_sale.cashier_name == H["user_a"].full_name
    assert dashboard_sale.cashier_username == H["user_a"].username

    dashboard_detail = await SaleService(db).get(
        receipt.sale_id, H["tenant_a"].id
    )
    assert dashboard_detail.sale_number == sale_number
    assert dashboard_detail.cashier_name == H["user_a"].full_name
    assert dashboard_detail.cashier_username == H["user_a"].username

    report = await TenantReportService(db).get_summary(
        H["tenant_a"].id,
        date_from=None,
        date_to=None,
        branch_id=H["branch_a"].id,
    )
    assert report.total_revenue >= Decimal("11.49")
