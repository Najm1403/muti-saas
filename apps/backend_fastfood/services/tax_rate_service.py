# services/tax_rate_service.py
#
# CRUD service for tax rates, scoped to a tenant.
# Only one tax rate may be is_default=True per tenant at any time.

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError
from models.tax_rate import TaxRate
from schemas.tax_rate import (
    TaxRateCreate,
    TaxRateResponse,
    TaxRateUpdate,
)


class TaxRateService:
    """Manages tax rates scoped to a tenant."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _clear_defaults(self, tenant_id: UUID) -> None:
        """Set all tax rates for this tenant to is_default=False."""
        result = await self.db.execute(
            select(TaxRate).where(
                TaxRate.tenant_id == tenant_id,
                TaxRate.deleted_at.is_(None),
                TaxRate.is_default.is_(True),
            )
        )
        for rate in result.scalars().all():
            rate.is_default = False

    async def create(
        self, tenant_id: UUID, data: TaxRateCreate
    ) -> TaxRateResponse:
        if data.is_default:
            await self._clear_defaults(tenant_id)

        rate = TaxRate(
            tenant_id=tenant_id,
            name=data.name,
            rate=data.rate,
            is_inclusive=data.is_inclusive,
            is_default=data.is_default,
        )
        self.db.add(rate)
        await self.db.commit()
        await self.db.refresh(rate)
        return TaxRateResponse.model_validate(rate)

    async def get(self, id: UUID, tenant_id: UUID) -> TaxRateResponse:
        result = await self.db.execute(
            select(TaxRate).where(
                TaxRate.id == id,
                TaxRate.tenant_id == tenant_id,
                TaxRate.deleted_at.is_(None),
            )
        )
        rate = result.scalar_one_or_none()
        if not rate:
            raise NotFoundError("Tax rate not found.")
        return TaxRateResponse.model_validate(rate)

    async def list(self, tenant_id: UUID) -> list[TaxRateResponse]:
        result = await self.db.execute(
            select(TaxRate).where(
                TaxRate.tenant_id == tenant_id,
                TaxRate.deleted_at.is_(None),
            )
        )
        rates = result.scalars().all()
        return [TaxRateResponse.model_validate(r) for r in rates]

    async def update(
        self, id: UUID, tenant_id: UUID, data: TaxRateUpdate
    ) -> TaxRateResponse:
        result = await self.db.execute(
            select(TaxRate).where(
                TaxRate.id == id,
                TaxRate.tenant_id == tenant_id,
                TaxRate.deleted_at.is_(None),
            )
        )
        rate = result.scalar_one_or_none()
        if not rate:
            raise NotFoundError("Tax rate not found.")

        fields = data.model_dump(exclude_unset=True)

        # If setting as default, clear all other defaults first.
        if fields.get("is_default") is True:
            await self._clear_defaults(tenant_id)

        for field, value in fields.items():
            setattr(rate, field, value)

        await self.db.commit()
        await self.db.refresh(rate)
        return TaxRateResponse.model_validate(rate)

    async def delete(self, id: UUID, tenant_id: UUID) -> None:
        result = await self.db.execute(
            select(TaxRate).where(
                TaxRate.id == id,
                TaxRate.tenant_id == tenant_id,
                TaxRate.deleted_at.is_(None),
            )
        )
        rate = result.scalar_one_or_none()
        if not rate:
            raise NotFoundError("Tax rate not found.")
        rate.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def set_default(self, id: UUID, tenant_id: UUID) -> TaxRateResponse:
        """Mark the given tax rate as the default, clearing all others."""
        result = await self.db.execute(
            select(TaxRate).where(
                TaxRate.id == id,
                TaxRate.tenant_id == tenant_id,
                TaxRate.deleted_at.is_(None),
            )
        )
        rate = result.scalar_one_or_none()
        if not rate:
            raise NotFoundError("Tax rate not found.")

        await self._clear_defaults(tenant_id)
        rate.is_default = True
        await self.db.commit()
        await self.db.refresh(rate)
        return TaxRateResponse.model_validate(rate)
