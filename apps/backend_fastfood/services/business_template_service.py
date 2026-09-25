# services/business_template_service.py
#
# Platform-managed BusinessTemplate CRUD — see spec A3.

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, ForbiddenError, NotFoundError
from core.modules import normalise_hidden_modules
from models.business_template import BusinessTemplate
from models.tenant import Tenant
from schemas.business_template import (
    BusinessTemplateCreate,
    BusinessTemplateResponse,
    BusinessTemplateUpdate,
)
from services.business_policy import enforce_module_hidden_list


class BusinessTemplateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self) -> list[BusinessTemplateResponse]:
        rows = await self.db.scalars(select(BusinessTemplate).order_by(BusinessTemplate.name))
        return [BusinessTemplateResponse.model_validate(t) for t in rows.all()]

    async def get(self, id: UUID) -> BusinessTemplateResponse:
        template = await self.db.get(BusinessTemplate, id)
        if not template:
            raise NotFoundError("Business template not found.")
        return BusinessTemplateResponse.model_validate(template)

    async def create(self, data: BusinessTemplateCreate) -> BusinessTemplateResponse:
        existing = await self.db.scalar(select(BusinessTemplate).where(BusinessTemplate.name == data.name))
        if existing:
            raise ConflictError(f"A business template named '{data.name}' already exists.")
        enforce_module_hidden_list((data.config or {}).get("modules", {}).get("hidden"))
        template = BusinessTemplate(id=uuid4(), name=data.name, config=data.config)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return BusinessTemplateResponse.model_validate(template)

    async def update(
        self, id: UUID, data: BusinessTemplateUpdate, *, step_up_ok: bool = False
    ) -> BusinessTemplateResponse:
        template = await self.db.get(BusinessTemplate, id)
        if not template:
            raise NotFoundError("Business template not found.")
        fields = data.model_dump(exclude_unset=True)
        if "config" in fields:
            new_hidden = normalise_hidden_modules(
                (fields["config"] or {}).get("modules", {}).get("hidden")
            )
            enforce_module_hidden_list(new_hidden)
            old_hidden = normalise_hidden_modules(
                (template.config or {}).get("modules", {}).get("hidden")
            )
            if new_hidden != old_hidden and not step_up_ok:
                raise ForbiddenError(
                    "Re-enter your password to confirm this change to visible modules.",
                    code="STEP_UP_REQUIRED",
                )
        for field, value in fields.items():
            setattr(template, field, value)
        await self.db.commit()
        await self.db.refresh(template)
        return BusinessTemplateResponse.model_validate(template)

    async def delete(self, id: UUID) -> None:
        template = await self.db.get(BusinessTemplate, id)
        if not template:
            raise NotFoundError("Business template not found.")
        in_use = await self.db.scalar(
            select(func.count(Tenant.id)).where(Tenant.business_template_id == id, Tenant.deleted_at.is_(None))
        )
        if in_use:
            raise ConflictError(
                f"This template is used by {in_use} tenant(s) and cannot be deleted."
            )
        await self.db.delete(template)
        await self.db.commit()

    async def tenants_using(self, id: UUID) -> list[dict]:
        rows = await self.db.execute(
            select(Tenant.id, Tenant.name, Tenant.tenant_code)
            .where(Tenant.business_template_id == id, Tenant.deleted_at.is_(None))
            .order_by(Tenant.name)
        )
        return [{"id": r.id, "name": r.name, "tenant_code": r.tenant_code} for r in rows.all()]
