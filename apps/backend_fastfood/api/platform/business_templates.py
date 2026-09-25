# api/platform/business_templates.py
#
# Platform-managed BUSINESS TYPE presets (Fast Food / Electronics / ...) —
# spec A3. Also carries the modules catalog route (GET /modules/catalog)
# and enforces config.modules.hidden on save (see business_policy.py).
#
# Prefix: /api/platform/business-templates

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import (
    CurrentPlatformAdmin,
    get_current_platform_admin,
    optional_step_up,
    require_business_template_manage,
    require_step_up,
    require_super,
)
from db.session import get_db
from schemas.business_template import (
    BusinessTemplateCreate,
    BusinessTemplateResponse,
    BusinessTemplateUpdate,
)
from schemas.common import MessageResponse
from services.business_template_service import BusinessTemplateService

router = APIRouter(prefix="/business-templates", tags=["Platform · Business Templates"])


def _svc(db: AsyncSession = Depends(get_db)) -> BusinessTemplateService:
    return BusinessTemplateService(db)


@router.get("/", response_model=list[BusinessTemplateResponse], summary="List business templates")
async def list_business_templates(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: BusinessTemplateService = Depends(_svc),
) -> list[BusinessTemplateResponse]:
    return await svc.list()


@router.post("/", response_model=BusinessTemplateResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a business template (super admin)")
async def create_business_template(
    data: BusinessTemplateCreate,
    _: CurrentPlatformAdmin = Depends(require_super),
    svc: BusinessTemplateService = Depends(_svc),
) -> BusinessTemplateResponse:
    return await svc.create(data)


# Declared ahead of GET /{id} — "modules" would otherwise be swallowed by the
# UUID path param and 422 instead of matching this route.
@router.get("/modules/catalog", response_model=list[dict],
    summary="Every tenant-dashboard module (key/label/group/mandatory)",
    description="The catalog config.modules.hidden entries are validated against — "
                 "used by the template config editor's checkbox grid and the config reference page.")
async def modules_catalog(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
) -> list[dict]:
    from core.modules import module_catalog
    return module_catalog()


@router.get("/{id}", response_model=BusinessTemplateResponse, summary="Get a business template")
async def get_business_template(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: BusinessTemplateService = Depends(_svc),
) -> BusinessTemplateResponse:
    return await svc.get(id)


@router.get("/{id}/tenants", response_model=list[dict], summary="List tenants using a business template")
async def business_template_tenants(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: BusinessTemplateService = Depends(_svc),
) -> list[dict]:
    return await svc.tenants_using(id)


@router.patch("/{id}", response_model=BusinessTemplateResponse,
    summary="Update a business template (requires the manage-templates capability)",
    description=(
        "Requires can_manage_business_templates (owners always qualify). If this "
        "update changes config.modules.hidden, it ALSO requires a fresh "
        "X-Step-Up-Token (POST /auth/step-up, action=update_business_template_modules) "
        "— otherwise 403 STEP_UP_REQUIRED before anything is written. Other config "
        "fields (pricing, product_fields, ...) save with no step-up needed."
    ))
async def update_business_template(
    id: UUID,
    data: BusinessTemplateUpdate,
    _: CurrentPlatformAdmin = Depends(require_business_template_manage),
    step_up_ok: bool = Depends(optional_step_up),
    svc: BusinessTemplateService = Depends(_svc),
) -> BusinessTemplateResponse:
    return await svc.update(id, data, step_up_ok=step_up_ok)


@router.delete("/{id}", response_model=MessageResponse,
    summary="Delete a business template (requires the manage-templates capability + password step-up)",
    description=(
        "Requires can_manage_business_templates (owners always qualify) AND a "
        "fresh X-Step-Up-Token (POST /auth/step-up, action=delete_business_template) "
        "— every time, regardless of how long the capability has been held."
    ))
async def delete_business_template(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(require_business_template_manage),
    __: CurrentPlatformAdmin = Depends(require_step_up("delete_business_template")),
    svc: BusinessTemplateService = Depends(_svc),
) -> MessageResponse:
    await svc.delete(id)
    return MessageResponse(message="Business template deleted.")
