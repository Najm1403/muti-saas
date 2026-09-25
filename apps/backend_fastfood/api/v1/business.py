# api/v1/business.py
#
# Business management routes — tenant admin only. A tenant has exactly one
# Business (spec A2) — created during onboarding, never via this API.
# Prefix: /api/v1/business

from __future__ import annotations

import io
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import CurrentUser, get_current_user, get_current_business_id, require_permission
from db.session import get_db
from schemas.business import BusinessResponse, BusinessUpdate
from services.business_service import BusinessService
from core.exceptions import ValidationError

router = APIRouter(prefix="/business", tags=["Business"])
_LOGO_DIR = Path(__file__).resolve().parents[2] / "media" / "business-logos"
_LOGO_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_LOGO_BYTES = 3 * 1024 * 1024


def _svc(db: AsyncSession = Depends(get_db)) -> BusinessService:
    return BusinessService(db)


@router.get(
    "/",
    response_model=BusinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the tenant's business",
)
async def get_business(
    current_user: CurrentUser = Depends(get_current_user),
    svc: BusinessService = Depends(_svc),
) -> BusinessResponse:
    return await svc.get_for_tenant(tenant_id=current_user.tenant_id)


@router.patch(
    "/",
    response_model=BusinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Update the tenant's business",
)
async def update_business(
    data: BusinessUpdate,
    current_user: CurrentUser = Depends(require_permission("settings.manage")),
    business_id=Depends(get_current_business_id),
    svc: BusinessService = Depends(_svc),
) -> BusinessResponse:
    return await svc.update(id=business_id, tenant_id=current_user.tenant_id, data=data)


@router.post("/logo", response_model=BusinessResponse, summary="Upload the shop receipt logo")
async def upload_business_logo(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_permission("settings.manage")),
    business_id=Depends(get_current_business_id),
    svc: BusinessService = Depends(_svc),
) -> BusinessResponse:
    if file.content_type not in _LOGO_TYPES:
        raise ValidationError("Logo must be a PNG, JPEG, or WebP image.")
    raw = await file.read(_MAX_LOGO_BYTES + 1)
    if len(raw) > _MAX_LOGO_BYTES:
        raise ValidationError("Logo must be 3 MB or smaller.")
    try:
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw)))
        image.load()
    except (UnidentifiedImageError, OSError):
        raise ValidationError("That file is not a readable image.")
    image.thumbnail((600, 300), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    image.convert("RGBA").save(output, format="PNG", optimize=True)
    _LOGO_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{business_id}.png"
    (_LOGO_DIR / filename).write_bytes(output.getvalue())
    return await svc.update_logo(
        id=business_id,
        tenant_id=current_user.tenant_id,
        logo_path=f"/media/business-logos/{filename}",
    )


@router.get(
    "/template-config",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Effective Business Template config for this tenant",
    description=(
        "Read-only copy of the tenant's BusinessTemplate.config (spec Part C) — "
        "variants, addons, inventory, pricing, product_fields, pos, categories. "
        "The tenant dashboard uses this only to show/hide optional UI (e.g. "
        "product_fields.sku/specs/warranty, spec G2); it is never authoritative "
        "for enforcement, which stays server-side (services/business_policy.py, D6)."
    ),
)
async def get_template_config(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from services.business_policy import load_business_policy
    return await load_business_policy(db, current_user.tenant_id)
