# api/v1/pos/sync.py
#
# POS data synchronization endpoints.
#
# full  — initial device setup or full refresh (download everything for the branch).
# delta — pull only records changed since a given timestamp (periodic background sync).
# upload — push a batch of offline-queued sales to the cloud.
#
# Prefix: /api/v1/pos/sync

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentCashier, CurrentDevice
from api.v1.pos._guards import operational_cashier, operational_device
from core.exceptions import ConflictError, NotFoundError, ValidationError
from core.security import decode_token
from uuid import UUID
from db.session import get_db
from schemas.pos_sync import (
    PosDeltaSyncResponse,
    PosOfflineSale,
    PosUploadRequest,
    PosUploadResponse,
    PosUploadResult,
    PosSyncResponse,
)
from services.pos_sync_service import PosSyncService
from services.pos_sale_service import PosSaleService

router = APIRouter(prefix="/sync", tags=["POS — Sync"])


def _sync_svc(db: AsyncSession = Depends(get_db)) -> PosSyncService:
    return PosSyncService(db)


@router.get(
    "/full",
    response_model=PosSyncResponse,
    summary="Full sync",
    description=(
        "Download the complete branch menu: categories, products with options, "
        "tax rates, active deals, and active promotions. "
        "Use on first launch or after a long offline period."
    ),
)
async def full_sync(
    device: CurrentDevice = Depends(operational_device),
    svc: PosSyncService = Depends(_sync_svc),
) -> PosSyncResponse:
    return await svc.full_sync(
        branch_id=device.branch_id,
        tenant_id=device.tenant_id,
    )


@router.get(
    "/delta",
    response_model=PosDeltaSyncResponse,
    summary="Delta sync",
    description=(
        "Download only records changed since the given ISO datetime. "
        "Call periodically (e.g. every 5–10 minutes) to keep the local DB fresh. "
        "Use ?since= with the synced_at timestamp from the previous sync response."
    ),
)
async def delta_sync(
    since: datetime = Query(..., description="ISO-8601 datetime of the last successful sync."),
    device: CurrentDevice = Depends(operational_device),
    svc: PosSyncService = Depends(_sync_svc),
) -> PosDeltaSyncResponse:
    return await svc.delta_sync(
        branch_id=device.branch_id,
        tenant_id=device.tenant_id,
        since=since,
    )


@router.post(
    "/upload",
    response_model=PosUploadResponse,
    summary="Upload offline sales",
    description=(
        "Submit a batch of sales that were created offline. "
        "Each sale is processed independently — duplicates (same sale_number + branch) "
        "are silently skipped, errors are reported per sale. "
        "The response counts created/duplicates/errors for the full batch."
    ),
)
async def upload_offline_sales(
    data: PosUploadRequest,
    cashier: CurrentCashier = Depends(operational_cashier),
    db: AsyncSession = Depends(get_db),
) -> PosUploadResponse:
    from schemas.pos_sale import (
        PosSaleCreate,
        PosSaleItemCreate,
        PosSaleVariantOptionSnapshot,
        PosSaleAddonSelection,
        PosSalePaymentCreate,
    )

    results: list[PosUploadResult] = []
    created = duplicates = errors = 0

    for offline in data.sales:
        try:
            if not offline.origin_proof:
                raise ValidationError("Offline sale lacks its original cashier proof; manual reconciliation required.")
            origin = decode_token(offline.origin_proof)
            if origin.get("type") != "offline_sale_origin" or any(
                origin.get(key) != str(getattr(cashier, key)) for key in ("tenant_id", "branch_id", "device_id")):
                raise ValidationError("Offline sale origin does not match this device.")
            when = offline.sold_at.timestamp()
            if not origin["iat"] - 60 <= when <= origin["sale_until"]:
                raise ValidationError("Offline sale falls outside its authorized cashier window.")
            origin_user = UUID(origin["user_id"])
            # Build a PosSaleCreate from the offline payload.
            sale_data = PosSaleCreate(
                id=offline.id,
                sale_number=offline.sale_number,
                sold_at=offline.sold_at,
                subtotal=offline.subtotal,
                discount=offline.discount,
                total=offline.total,
                tax_amount=offline.tax_amount,
                tax_rate=offline.tax_rate,
                promotion_id=offline.promotion_id,
                deal_id=offline.deal_id,
                session_id=offline.session_id,
                items=[
                    PosSaleItemCreate(
                        id=i.id,
                        variant_id=i.variant_id,
                        product_id=i.product_id,
                        product_name=i.product_name,
                        quantity=i.quantity,
                        unit_price=i.unit_price,
                        discount=i.discount,
                        total=i.total,
                        options=[
                            PosSaleVariantOptionSnapshot(
                                id=o.id,
                                variant_option_id=o.variant_option_id,
                                option_name=o.option_name,
                            )
                            for o in i.options
                        ],
                        addons=[
                            PosSaleAddonSelection(
                                id=a.id,
                                addon_item_id=a.addon_item_id,
                                addon_name=a.addon_name,
                                price_delta=a.price_delta,
                                was_removed=a.was_removed,
                            )
                            for a in i.addons
                        ],
                        parent_item_id=i.parent_item_id,
                        satisfies_option_group_id=i.satisfies_option_group_id,
                        component_option_id=i.component_option_id,
                    )
                    for i in offline.items
                ],
                payments=[
                    PosSalePaymentCreate(
                        payment_method=p.payment_method,
                        amount=p.amount,
                        reference=p.reference,
                    )
                    for p in offline.payments
                ],
            )
            svc = PosSaleService(db)
            receipt = await svc.create(
                data=sale_data,
                branch_id=cashier.branch_id,
                device_id=cashier.device_id,
                user_id=origin_user,
                tenant_id=cashier.tenant_id,
            )
            results.append(
                PosUploadResult(
                    sale_number=offline.sale_number,
                    sale_id=receipt.sale_id,
                    status="created",
                )
            )
            created += 1
        except Exception as exc:
            # Roll back only this sale's partial writes.
            await db.rollback()
            # A domain exception (bad/inconsistent data, a genuine sale_number
            # conflict, a missing reference) is a deterministic rejection: the
            # exact same payload will fail the exact same way no matter how
            # many times the device resubmits it. Anything else (an
            # unexpected bug, a DB hiccup) might succeed on a later attempt,
            # so it stays retryable — the safe default. Without this
            # distinction a single permanently-invalid queued sale retries
            # forever (every periodic sync tick and every reconnect),
            # surfacing the same error to the cashier indefinitely.
            retryable = not isinstance(exc, (ValidationError, ConflictError, NotFoundError))
            results.append(
                PosUploadResult(
                    sale_number=offline.sale_number,
                    sale_id=None,
                    status="error",
                    error=str(exc),
                    retryable=retryable,
                )
            )
            errors += 1

    return PosUploadResponse(
        total=len(data.sales),
        created=created,
        duplicates=duplicates,
        errors=errors,
        results=results,
    )
