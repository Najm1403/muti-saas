# api/platform/onboarding.py
#
# Platform tenant onboarding — single-transaction endpoint.
# Prefix: /api/platform/onboard

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import CurrentPlatformAdmin, get_current_platform_admin
from db.session import get_db
from schemas.onboarding import OnboardingCreate, OnboardingResponse
from services.onboarding_service import OnboardingService

router = APIRouter(prefix="/onboard", tags=["Platform · Onboarding"])


def _svc(db: AsyncSession = Depends(get_db)) -> OnboardingService:
    return OnboardingService(db)


@router.post(
    "",
    response_model=OnboardingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Onboard new tenant",
    description=(
        "Creates Tenant + Owner User + Admin Role + Business + "
        "Initial Branch + Subscription in a single atomic transaction. "
        "Nothing is written to the database unless all six steps succeed. "
        "Returns the IDs and display values for all created entities, "
        "including the owner's one-time temp password."
    ),
)
@router.post("/", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def onboard_tenant(
    data: OnboardingCreate,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: OnboardingService = Depends(_svc),
) -> OnboardingResponse:
    return await svc.onboard(data)
