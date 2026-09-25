# tests/test_tax_rate_service.py
#
# Tests TaxRateService: CRUD, the single-default-per-tenant invariant,
# and tenant isolation.

from __future__ import annotations

import pytest
import pytest_asyncio
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError
from models.business_template import BusinessTemplate
from models.tax_rate import TaxRate
from models.tenant import Tenant
from schemas.tax_rate import TaxRateCreate, TaxRateUpdate
from services.tax_rate_service import TaxRateService


# ── Fixture ────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def TS(db: AsyncSession, business_template: BusinessTemplate):
    tenant_a = Tenant(id=uuid4(), name="TaxAlpha", tenant_code="T_ALPHA", is_active=True,
                       business_template_id=business_template.id)
    tenant_b = Tenant(id=uuid4(), name="TaxBeta",  tenant_code="T_BETA",  is_active=True,
                       business_template_id=business_template.id)
    db.add_all([tenant_a, tenant_b])
    await db.flush()
    yield dict(tenant_a=tenant_a, tenant_b=tenant_b)


# ══════════════════════════════════════════════════════════════
# CRUD
# ══════════════════════════════════════════════════════════════

class TestTaxRateCRUD:

    @pytest.mark.asyncio
    async def test_create_tax_rate(self, db, TS):
        svc = TaxRateService(db)
        result = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Standard VAT", rate=Decimal("0.1500"), is_inclusive=False, is_default=False
        ))
        assert result.id is not None
        assert result.name == "Standard VAT"
        assert result.rate == Decimal("0.1500")
        assert result.is_inclusive is False
        assert result.is_default is False
        assert result.tenant_id == TS["tenant_a"].id

    @pytest.mark.asyncio
    async def test_create_inclusive_rate(self, db, TS):
        svc = TaxRateService(db)
        result = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Inclusive GST", rate=Decimal("0.0700"), is_inclusive=True, is_default=False
        ))
        assert result.is_inclusive is True

    @pytest.mark.asyncio
    async def test_get_tax_rate(self, db, TS):
        svc = TaxRateService(db)
        created = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Fetch Me", rate=Decimal("0.0500"), is_inclusive=False, is_default=False
        ))
        fetched = await svc.get(created.id, TS["tenant_a"].id)
        assert fetched.id == created.id
        assert fetched.name == "Fetch Me"

    @pytest.mark.asyncio
    async def test_get_wrong_tenant_raises(self, db, TS):
        svc = TaxRateService(db)
        created = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Private", rate=Decimal("0.10"), is_inclusive=False, is_default=False
        ))
        with pytest.raises(NotFoundError):
            await svc.get(created.id, TS["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_list_tax_rates_scoped(self, db, TS):
        svc = TaxRateService(db)
        await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="A Rate", rate=Decimal("0.10"), is_inclusive=False, is_default=False
        ))
        await svc.create(TS["tenant_b"].id, TaxRateCreate(
            name="B Rate", rate=Decimal("0.08"), is_inclusive=False, is_default=False
        ))
        rates_a = await svc.list(TS["tenant_a"].id)
        names = [r.name for r in rates_a]
        assert "A Rate" in names
        assert "B Rate" not in names

    @pytest.mark.asyncio
    async def test_update_name_and_rate(self, db, TS):
        svc = TaxRateService(db)
        created = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Old", rate=Decimal("0.10"), is_inclusive=False, is_default=False
        ))
        updated = await svc.update(created.id, TS["tenant_a"].id,
                                   TaxRateUpdate(name="New", rate=Decimal("0.12")))
        assert updated.name == "New"
        assert updated.rate == Decimal("0.12")

    @pytest.mark.asyncio
    async def test_update_wrong_tenant_raises(self, db, TS):
        svc = TaxRateService(db)
        created = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Mine", rate=Decimal("0.10"), is_inclusive=False, is_default=False
        ))
        with pytest.raises(NotFoundError):
            await svc.update(created.id, TS["tenant_b"].id, TaxRateUpdate(name="Hijacked"))

    @pytest.mark.asyncio
    async def test_delete_tax_rate_soft(self, db, TS):
        svc = TaxRateService(db)
        created = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Delete Me", rate=Decimal("0.05"), is_inclusive=False, is_default=False
        ))
        await svc.delete(created.id, TS["tenant_a"].id)
        with pytest.raises(NotFoundError):
            await svc.get(created.id, TS["tenant_a"].id)

    @pytest.mark.asyncio
    async def test_deleted_absent_from_list(self, db, TS):
        svc = TaxRateService(db)
        created = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Gone", rate=Decimal("0.05"), is_inclusive=False, is_default=False
        ))
        await svc.delete(created.id, TS["tenant_a"].id)
        rates = await svc.list(TS["tenant_a"].id)
        assert created.id not in [r.id for r in rates]

    @pytest.mark.asyncio
    async def test_delete_wrong_tenant_raises(self, db, TS):
        svc = TaxRateService(db)
        created = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Mine", rate=Decimal("0.10"), is_inclusive=False, is_default=False
        ))
        with pytest.raises(NotFoundError):
            await svc.delete(created.id, TS["tenant_b"].id)


# ══════════════════════════════════════════════════════════════
# Single-default-per-tenant invariant
# ══════════════════════════════════════════════════════════════

class TestTaxRateDefaultInvariant:

    @pytest.mark.asyncio
    async def test_create_with_default_true(self, db, TS):
        svc = TaxRateService(db)
        result = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Default Rate", rate=Decimal("0.15"), is_inclusive=False, is_default=True
        ))
        assert result.is_default is True

    @pytest.mark.asyncio
    async def test_only_one_default_per_tenant_on_create(self, db, TS):
        """
        Creating a second rate with is_default=True must clear the first.
        At all times, at most one rate can be is_default=True per tenant.
        """
        svc = TaxRateService(db)
        rate1 = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="First Default", rate=Decimal("0.10"), is_inclusive=False, is_default=True
        ))
        rate2 = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Second Default", rate=Decimal("0.15"), is_inclusive=False, is_default=True
        ))

        # Reload rate1 from DB directly to check is_default was cleared
        result = await db.execute(select(TaxRate).where(TaxRate.id == rate1.id))
        rate1_db = result.scalar_one_or_none()

        assert rate1_db.is_default is False, "First rate must lose default status"
        assert rate2.is_default is True, "Second rate must be the new default"

    @pytest.mark.asyncio
    async def test_set_default_promotes_and_clears_others(self, db, TS):
        """
        set_default() makes the target the only default,
        clearing all other defaults for the same tenant.
        """
        svc = TaxRateService(db)
        rate1 = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Rate 1", rate=Decimal("0.10"), is_inclusive=False, is_default=True
        ))
        rate2 = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Rate 2", rate=Decimal("0.15"), is_inclusive=False, is_default=False
        ))

        result = await svc.set_default(rate2.id, TS["tenant_a"].id)
        assert result.is_default is True

        # Rate1 must no longer be default
        r1_db = await db.execute(select(TaxRate).where(TaxRate.id == rate1.id))
        assert r1_db.scalar_one_or_none().is_default is False

    @pytest.mark.asyncio
    async def test_set_default_wrong_tenant_raises(self, db, TS):
        svc = TaxRateService(db)
        rate_a = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="A Rate", rate=Decimal("0.10"), is_inclusive=False, is_default=False
        ))
        with pytest.raises(NotFoundError):
            await svc.set_default(rate_a.id, TS["tenant_b"].id)

    @pytest.mark.asyncio
    async def test_tenant_defaults_are_isolated(self, db, TS):
        """
        Each tenant's default is independent — setting a default in tenant A
        must not affect tenant B's rates.
        """
        svc = TaxRateService(db)
        rate_a = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="A Default", rate=Decimal("0.10"), is_inclusive=False, is_default=True
        ))
        rate_b = await svc.create(TS["tenant_b"].id, TaxRateCreate(
            name="B Default", rate=Decimal("0.08"), is_inclusive=False, is_default=True
        ))

        # Both are default for their own tenants independently
        r_a = await svc.get(rate_a.id, TS["tenant_a"].id)
        r_b = await svc.get(rate_b.id, TS["tenant_b"].id)
        assert r_a.is_default is True
        assert r_b.is_default is True

    @pytest.mark.asyncio
    async def test_update_to_default_clears_others(self, db, TS):
        """
        PATCH with is_default=True via update() also enforces the single-default rule.
        """
        svc = TaxRateService(db)
        rate1 = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Rate 1", rate=Decimal("0.10"), is_inclusive=False, is_default=True
        ))
        rate2 = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="Rate 2", rate=Decimal("0.12"), is_inclusive=False, is_default=False
        ))

        await svc.update(rate2.id, TS["tenant_a"].id, TaxRateUpdate(is_default=True))

        r1_db = await db.execute(select(TaxRate).where(TaxRate.id == rate1.id))
        assert r1_db.scalar_one_or_none().is_default is False

    @pytest.mark.asyncio
    async def test_three_rates_only_one_default(self, db, TS):
        """With three rates, calling set_default on the third clears both others."""
        svc = TaxRateService(db)
        r1 = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="R1", rate=Decimal("0.05"), is_inclusive=False, is_default=True
        ))
        r2 = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="R2", rate=Decimal("0.10"), is_inclusive=False, is_default=False
        ))
        r3 = await svc.create(TS["tenant_a"].id, TaxRateCreate(
            name="R3", rate=Decimal("0.15"), is_inclusive=False, is_default=False
        ))

        await svc.set_default(r3.id, TS["tenant_a"].id)

        # Check all three in DB
        all_rates = await db.execute(
            select(TaxRate).where(TaxRate.tenant_id == TS["tenant_a"].id)
        )
        defaults = [r for r in all_rates.scalars().all() if r.is_default]
        assert len(defaults) == 1
        assert defaults[0].id == r3.id
