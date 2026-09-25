# api/platform/employees.py
#
# Platform-company HR — employee records. Platform admin only.
# Delete (archive) requires super admin.
# Prefix: /api/platform/employees

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.platform.dependencies import (
    CurrentPlatformAdmin,
    get_current_platform_admin,
    require_super,
)
from db.session import get_db
from schemas.common import MessageResponse
from schemas.platform_employee import (
    PlatformDepartmentCreate,
    PlatformEmployeeCreate,
    PlatformEmployeeResponse,
    PlatformEmployeeUpdate,
)
from services.platform_hr_service import PlatformHRService

router = APIRouter(prefix="/employees", tags=["Platform · Employees"])


def _svc(db: AsyncSession = Depends(get_db)) -> PlatformHRService:
    return PlatformHRService(db)


@router.get("/departments", response_model=list[str], summary="Distinct department names")
async def list_departments(
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformHRService = Depends(_svc),
) -> list[str]:
    return await svc.departments()


@router.post("/departments", response_model=str, status_code=status.HTTP_201_CREATED, summary="Add a platform department")
async def create_department(
    data: PlatformDepartmentCreate,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformHRService = Depends(_svc),
) -> str:
    return await svc.create_department(data.name)


@router.get("", response_model=list[PlatformEmployeeResponse], summary="List platform employees")
@router.get("/", response_model=list[PlatformEmployeeResponse], include_in_schema=False)
async def list_employees(
    status_: str | None = Query(default=None, alias="status"),
    department: str | None = Query(default=None),
    q: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformHRService = Depends(_svc),
) -> list[PlatformEmployeeResponse]:
    return await svc.list_employees(
        status=status_, department=department, q=q, skip=skip, limit=limit
    )


@router.post(
    "",
    response_model=PlatformEmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a platform employee",
)
@router.post("/", response_model=PlatformEmployeeResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_employee(
    data: PlatformEmployeeCreate,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformHRService = Depends(_svc),
) -> PlatformEmployeeResponse:
    return await svc.create_employee(data)


@router.get("/{id}", response_model=PlatformEmployeeResponse, summary="Get a platform employee")
async def get_employee(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformHRService = Depends(_svc),
) -> PlatformEmployeeResponse:
    return await svc.get_employee(id)


@router.patch("/{id}", response_model=PlatformEmployeeResponse, summary="Update a platform employee")
async def update_employee(
    id: UUID,
    data: PlatformEmployeeUpdate,
    _: CurrentPlatformAdmin = Depends(get_current_platform_admin),
    svc: PlatformHRService = Depends(_svc),
) -> PlatformEmployeeResponse:
    return await svc.update_employee(id, data)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    summary="Archive a platform employee (super admin only)",
)
async def delete_employee(
    id: UUID,
    _: CurrentPlatformAdmin = Depends(require_super),
    svc: PlatformHRService = Depends(_svc),
) -> MessageResponse:
    await svc.delete_employee(id)
    return MessageResponse(message="Employee archived.")
