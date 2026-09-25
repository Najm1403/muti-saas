# tests/test_payment_methods.py
#
# Covers the fixed sale payment-method list (Cash / JazzCash / EasyPaisa /
# Online Transfer / Credit Card):
#   1. core.payment_methods normalisation (aliases, case, invalid)
#   2. Pydantic schema validation at the point payment is taken
#   3. Shift-close session summary — full 5-way breakdown, legacy labels folded in
#   4. Tenant sales report — overall + day-grouped payment-method breakdown

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from pydantic import ValidationError

from core.payment_methods import PAYMENT_METHODS, label_lenient, normalise_payment_method
from models.cashier_session import CashierSession
from schemas.payment import PaymentCreate
from schemas.pos_sale import PosSalePaymentCreate
from services.cashier_session_service import CashierSessionService
from services.tenant_report_service import TenantReportService


# ── 1. normalisation ────────────────────────────────────────────

class TestNormalise:
    @pytest.mark.parametrize("raw,expected", [
        ("Cash", "Cash"), ("cash", "Cash"), (" CASH ", "Cash"),
        ("JazzCash", "JazzCash"), ("jazzcash", "JazzCash"), ("jazz cash", "JazzCash"),
        ("EasyPaisa", "EasyPaisa"), ("easy paisa", "EasyPaisa"),
        ("Online Transfer", "Online Transfer"), ("bank", "Online Transfer"),
        ("bank transfer", "Online Transfer"),
        ("Credit Card", "Credit Card"), ("card", "Credit Card"), ("creditcard", "Credit Card"),
    ])
    def test_aliases_map_to_canonical(self, raw, expected):
        assert normalise_payment_method(raw) == expected

    def test_unknown_raises(self):
        with pytest.raises(ValueError):
            normalise_payment_method("Bitcoin")

    def test_label_lenient_never_raises(self):
        assert label_lenient("cash") == "Cash"
        assert label_lenient("Bitcoin") == "Bitcoin"
        assert label_lenient("") == "Unknown"

    def test_all_five_present(self):
        assert PAYMENT_METHODS == ["Cash", "JazzCash", "EasyPaisa", "Online Transfer", "Credit Card"]


# ── 2. schema validation ────────────────────────────────────────

class TestSchemaValidation:
    def test_pos_payment_normalises_alias(self):
        p = PosSalePaymentCreate(payment_method="jazz cash", amount=Decimal("100"))
        assert p.payment_method == "JazzCash"

    def test_pos_payment_rejects_unknown(self):
        with pytest.raises(ValidationError):
            PosSalePaymentCreate(payment_method="Bitcoin", amount=Decimal("100"))

    def test_payment_create_normalises_alias(self):
        p = PaymentCreate(sale_id=uuid4(), payment_method="card", amount=Decimal("50"))
        assert p.payment_method == "Credit Card"

    def test_payment_create_rejects_unknown(self):
        with pytest.raises(ValidationError):
            PaymentCreate(sale_id=uuid4(), payment_method="Cheque", amount=Decimal("50"))


# ── 3. shift-close summary ──────────────────────────────────────

class TestSessionSummary:
    @pytest_asyncio.fixture
    async def open_session(self, db, H):
        """An OPEN session on device_a spanning sale_a (pay_a = 'CASH', 9.99)."""
        session = CashierSession(
            id=uuid4(),
            device_id=H["device_a"].id,
            user_id=H["user_a"].id,
            branch_id=H["branch_a"].id,
            tenant_id=H["tenant_a"].id,
            opened_at=datetime.now(timezone.utc) - timedelta(hours=1),
            opening_cash=Decimal("100.00"),
            status="OPEN",
        )
        db.add(session)
        await db.flush()
        return session

    @pytest.mark.asyncio
    async def test_all_five_methods_present_and_legacy_folded(self, db, H, open_session):
        svc = CashierSessionService(db)
        resp = await svc.summary(H["device_a"].id, H["tenant_a"].id)
        by_method = resp.summary.by_payment_method

        for m in PAYMENT_METHODS:
            assert m in by_method, f"{m} missing from breakdown"
        # H's pay_a is raw "CASH" — must fold onto canonical "Cash", not a duplicate key
        assert by_method["Cash"] == Decimal("9.99")
        assert by_method["JazzCash"] == Decimal("0.00")
        assert resp.summary.cash_sales_total == Decimal("9.99")
        # The fixture also has a same-shift 9.99 cash refund, so it must be
        # shown and removed from expected drawer cash.
        assert resp.summary.refunds_count == 1
        assert resp.summary.refunds_by_payment_method["Cash"] == Decimal("9.99")
        assert resp.summary.expected_cash == Decimal("100.00")
        assert resp.summary.net_total == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_other_tenants_device_not_counted(self, db, H, open_session):
        # device_b/tenant_b's sale_b ("CARD", 12.99) must not leak into tenant_a's session.
        svc = CashierSessionService(db)
        resp = await svc.summary(H["device_a"].id, H["tenant_a"].id)
        assert resp.summary.by_payment_method["Credit Card"] == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_cash_change_is_not_counted_as_drawer_income(
        self, db, H, open_session
    ):
        H["pay_a"].amount = Decimal("20.00")
        await db.flush()

        summary = (
            await CashierSessionService(db).summary(
                H["device_a"].id, H["tenant_a"].id
            )
        ).summary

        assert summary.by_payment_method["Cash"] == Decimal("9.99")
        assert summary.total_payments == Decimal("9.99")


# ── 4. tenant sales report ──────────────────────────────────────

class TestPaymentMethodReport:
    @pytest.mark.asyncio
    async def test_overall_breakdown_scoped_to_tenant(self, db, H):
        svc = TenantReportService(db)
        points = await svc.get_by_payment_method(
            H["tenant_a"].id, date_from=None, date_to=None, branch_id=None, group_by=None,
        )
        assert len(points) == 1
        point = points[0]
        assert point.period is None
        assert point.total_amount == Decimal("9.99")
        labels = {row.payment_method: row for row in point.breakdown}
        assert labels["Cash"].amount == Decimal("9.99")
        assert labels["Cash"].transactions == 1
        assert "Credit Card" not in labels  # tenant_b's payment must not appear

    @pytest.mark.asyncio
    async def test_tenant_b_sees_its_own_card_payment(self, db, H):
        svc = TenantReportService(db)
        points = await svc.get_by_payment_method(
            H["tenant_b"].id, date_from=None, date_to=None, branch_id=None, group_by=None,
        )
        labels = {row.payment_method: row for row in points[0].breakdown}
        assert labels["Credit Card"].amount == Decimal("12.99")
        assert "Cash" not in labels

    @pytest.mark.asyncio
    async def test_group_by_day_returns_period(self, db, H):
        svc = TenantReportService(db)
        points = await svc.get_by_payment_method(
            H["tenant_a"].id, date_from=None, date_to=None, branch_id=None, group_by="day",
        )
        assert len(points) == 1
        assert points[0].period == datetime.now(timezone.utc).strftime("%Y-%m-%d")
