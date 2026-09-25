# api/platform/settings.py
#
# Platform-level settings — read and update key/value configuration.
# Prefix: /api/platform/settings
#
# GET  /  → returns all settings as {key: value | null}
# PATCH/  → accepts {key: value | null} for any subset of keys

from __future__ import annotations

import aiosmtplib
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import CurrentPlatformAdmin, get_current_platform_admin, require_super
from core.email import send_test_email
from core.exceptions import ValidationError
from db.session import get_db
from repositories.platform_admin_repository import PlatformAdminRepository
from schemas.common import MessageResponse
from services.platform_setting_service import PlatformSettingService

router = APIRouter(prefix="/settings", tags=["Platform · Settings"])


def _svc(db: AsyncSession = Depends(get_db)) -> PlatformSettingService:
    return PlatformSettingService(db)


@router.get("", response_model=dict[str, str | None], status_code=status.HTTP_200_OK, summary="Get all platform settings")
@router.get("/", response_model=dict[str, str | None], status_code=status.HTTP_200_OK, include_in_schema=False)
async def get_settings(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformSettingService = Depends(_svc),
) -> dict[str, str | None]:
    return await svc.get_all()


@router.patch("", response_model=dict[str, str | None], status_code=status.HTTP_200_OK, summary="Update platform settings")
@router.patch("/", response_model=dict[str, str | None], status_code=status.HTTP_200_OK, include_in_schema=False)
async def update_settings(
    updates: dict[str, str | None],
    _: CurrentPlatformAdmin = Depends(require_super),
    svc: PlatformSettingService = Depends(_svc),
) -> dict[str, str | None]:
    """Super admin only. Pass any subset of keys to update."""
    return await svc.update(updates)


@router.post(
    "/test-email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a diagnostic email to the signed-in admin",
    description=(
        "Sends a test message using the .env SMTP config and returns the real "
        "SMTP error on failure (unlike the OTP senders, which swallow errors). "
        "Use it to confirm password-reset emails will send. Super admin only."
    ),
)
async def test_email(
    current: CurrentPlatformAdmin = Depends(require_super),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    admin = await PlatformAdminRepository(db).get_by_id(current.admin_id)
    if not admin or not admin.email:
        raise ValidationError("Your platform-admin account has no email address on file.")
    smtp_cfg = await PlatformSettingService(db).get_all()   # Settings-page values win over .env
    try:
        await send_test_email(admin.email, smtp_cfg=smtp_cfg)
    except ValueError as exc:                       # SMTP not configured
        raise ValidationError(str(exc))
    except (aiosmtplib.SMTPException, OSError) as exc:  # auth / connect / TLS failure
        raise ValidationError(f"SMTP send failed: {exc}")
    return MessageResponse(message=f"Test email sent to {admin.email}. Check the inbox (and spam).")
