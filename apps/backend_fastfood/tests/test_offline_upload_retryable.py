# tests/test_offline_upload_retryable.py
#
# Regression coverage for the retryable/non-retryable classification added to
# POST /pos/sync/upload's per-sale results (see api/v1/pos/sync.py and
# schemas/pos_sync.py::PosUploadResult.retryable).
#
# Background: the Flutter sync outbox previously retried EVERY unsynced sale
# on every 5-minute tick and every reconnect, forever, with no way to stop.
# A sale that fails a deterministic business-rule check (bad/inconsistent
# data, a genuine sale_number conflict) will fail identically no matter how
# many times it's resubmitted, so the client now reads `retryable` to decide
# whether to keep retrying (True — the safe default, for anything
# unexpected) or quarantine the sale locally (False — for our own domain
# exceptions, which are always deterministic). These tests pin the server
# side of that contract: domain exceptions marked retryable=False, anything
# else defaults to True.

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from core.security import create_cashier_token, create_offline_proof
from db.session import get_db
from tests.test_deployment_regressions import sale


async def _upload(db, H, sales: list[dict]):
    async def override():
        yield db
    app.dependency_overrides[get_db] = override
    token = create_cashier_token(
        H["user_a"].id, H["device_a"].id, H["branch_a"].id, H["tenant_a"].id
    )
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test.local") as client:
            return await client.post(
                "/api/v1/pos/sync/upload",
                json={"sales": sales},
                headers={"Authorization": "Bearer " + token},
            )
    finally:
        app.dependency_overrides.clear()


def _offline_payload(H, **overrides):
    data = sale(H).model_dump(mode="json")
    data["id"] = str(uuid4())
    data["items"][0]["variant_id"] = str(H["default_variant_a"].id)
    data["origin_proof"] = create_offline_proof(
        H["user_a"].id, H["device_a"].id, H["branch_a"].id, H["tenant_a"].id
    )
    data.update(overrides)
    return data


@pytest.mark.asyncio
async def test_validation_error_is_not_retryable(db, H):
    H["pvog_a"].is_required = False
    H["user_a"].all_branches = True
    data = _offline_payload(H)
    # Tampered price triggers PosSaleService's server-side price re-verification
    # (ValidationError) — a deterministic rejection: resubmitting the exact
    # same payload will fail the exact same way every time.
    data["items"][0]["unit_price"] = "1.00"
    data["subtotal"] = data["total"] = "1.00"
    data["payments"][0]["amount"] = "1.00"

    resp = await _upload(db, H, [data])
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["errors"] == 1, body
    result = body["results"][0]
    assert result["status"] == "error"
    assert result["retryable"] is False


@pytest.mark.asyncio
async def test_conflicting_sale_number_is_not_retryable(db, H):
    H["pvog_a"].is_required = False
    H["user_a"].all_branches = True
    first = _offline_payload(H)

    ok = await _upload(db, H, [first])
    assert ok.status_code == 200, ok.text
    assert ok.json()["created"] == 1, ok.json()

    # Same sale_number, genuinely different data (a different item quantity
    # and total) — this is a real conflict, not a safe-to-retry duplicate.
    second = _offline_payload(H, sale_number=first["sale_number"])
    second["items"][0]["quantity"] = "2"
    second["items"][0]["total"] = "20"
    second["subtotal"] = second["total"] = "20"
    second["payments"][0]["amount"] = "20"

    resp = await _upload(db, H, [second])
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["errors"] == 1, body
    result = body["results"][0]
    assert result["status"] == "error"
    assert result["retryable"] is False


@pytest.mark.asyncio
async def test_identical_resubmit_of_same_sale_succeeds_without_error(db, H):
    """Sanity check: a genuine offline-retry (exact same sale resubmitted,
    e.g. after a dropped response) must still succeed cleanly — only a
    real conflict should ever be reported, let alone as non-retryable."""
    H["pvog_a"].is_required = False
    H["user_a"].all_branches = True
    data = _offline_payload(H)

    first = await _upload(db, H, [data])
    assert first.status_code == 200, first.text
    assert first.json()["created"] == 1, first.json()

    again = await _upload(db, H, [data])
    assert again.status_code == 200, again.text
    body = again.json()
    assert body["errors"] == 0, body
    assert body["results"][0]["status"] == "created"
