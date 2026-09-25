# services/preparation_station_service.py
#
# CRUD for preparation stations (KDS-ready, V1 management only).
# Stations are scoped to a branch; all queries verify tenant ownership via
# Branch → Restaurant → tenant_id.

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError
from models.branch import Branch
from models.preparation_station import PreparationStation
from models.business import Business
from schemas.preparation_station import (
    PreparationStationCreate,
    PreparationStationResponse,
    PreparationStationUpdate,
)


class PreparationStationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _to_schema(self, station: PreparationStation) -> PreparationStationResponse:
        return PreparationStationResponse(
            id=station.id,
            branch_id=station.branch_id,
            name=station.name,
            display_order=station.display_order,
            is_active=station.is_active,
            created_at=station.created_at,
            updated_at=station.updated_at,
        )

    def _scoped(self, tenant_id: UUID):
        return (
            select(PreparationStation)
            .join(Branch, PreparationStation.branch_id == Branch.id)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Business.tenant_id == tenant_id,
                PreparationStation.deleted_at.is_(None),
            )
        )

    async def _verify_branch(self, branch_id: UUID, tenant_id: UUID) -> None:
        result = await self.db.execute(
            select(Branch)
            .join(Business, Branch.business_id == Business.id)
            .where(
                Branch.id == branch_id,
                Business.tenant_id == tenant_id,
                Branch.deleted_at.is_(None),
            )
        )
        if not result.scalar_one_or_none():
            raise NotFoundError("Branch not found.")

    async def create(
        self, branch_id: UUID, data: PreparationStationCreate, tenant_id: UUID
    ) -> PreparationStationResponse:
        await self._verify_branch(branch_id, tenant_id)

        # Guard duplicate name within branch.
        dup = await self.db.execute(
            select(PreparationStation).where(
                PreparationStation.branch_id == branch_id,
                PreparationStation.name == data.name,
                PreparationStation.deleted_at.is_(None),
            )
        )
        if dup.scalar_one_or_none():
            raise ConflictError(
                f"A preparation station named '{data.name}' already exists for this branch."
            )

        station = PreparationStation(
            id=uuid4(),
            branch_id=branch_id,
            name=data.name,
            display_order=data.display_order,
            is_active=data.is_active,
        )
        self.db.add(station)
        await self.db.commit()
        await self.db.refresh(station)
        return self._to_schema(station)

    async def list(
        self, branch_id: UUID, tenant_id: UUID
    ) -> list[PreparationStationResponse]:
        await self._verify_branch(branch_id, tenant_id)
        result = await self.db.execute(
            self._scoped(tenant_id)
            .where(PreparationStation.branch_id == branch_id)
            .order_by(PreparationStation.display_order, PreparationStation.name)
        )
        return [self._to_schema(s) for s in result.scalars().all()]

    async def get(
        self, station_id: UUID, tenant_id: UUID
    ) -> PreparationStationResponse:
        result = await self.db.execute(
            self._scoped(tenant_id).where(PreparationStation.id == station_id)
        )
        station = result.scalar_one_or_none()
        if not station:
            raise NotFoundError("Preparation station not found.")
        return self._to_schema(station)

    async def update(
        self, station_id: UUID, data: PreparationStationUpdate, tenant_id: UUID
    ) -> PreparationStationResponse:
        result = await self.db.execute(
            self._scoped(tenant_id).where(PreparationStation.id == station_id)
        )
        station = result.scalar_one_or_none()
        if not station:
            raise NotFoundError("Preparation station not found.")

        if data.name is not None:
            station.name = data.name
        if data.display_order is not None:
            station.display_order = data.display_order
        if data.is_active is not None:
            station.is_active = data.is_active

        await self.db.commit()
        await self.db.refresh(station)
        return self._to_schema(station)

    async def delete(self, station_id: UUID, tenant_id: UUID) -> None:
        from datetime import datetime, timezone

        result = await self.db.execute(
            self._scoped(tenant_id).where(PreparationStation.id == station_id)
        )
        station = result.scalar_one_or_none()
        if not station:
            raise NotFoundError("Preparation station not found.")

        station.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()
