from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from schemas.common import APIBaseSchema


class BranchBrief(APIBaseSchema):
    id: UUID
    name: str
    branch_code: str


class BranchAssignmentResponse(APIBaseSchema):
    all_branches: bool
    branches: list[BranchBrief]


class BranchAssignmentUpdate(BaseModel):
    all_branches: bool
    branch_ids: list[UUID] = []
