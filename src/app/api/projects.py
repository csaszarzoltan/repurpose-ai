"""User-centered project workspace and privacy-safe telemetry endpoints."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from app.dependencies import get_optional_user
from app.models.project import ProjectCreate, ProjectResponse, ProjectUpdate, TelemetryEvent
from app.services.project_store import ProjectStore

if TYPE_CHECKING:
    from app.models.auth import UserResponse

router = APIRouter(prefix="/api/v1", tags=["workspace"])


def _owner(user: UserResponse | None, workspace_id: str | None) -> str:
    if user:
        return user.user_id
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "production":
        raise HTTPException(status_code=401, detail="Authentication is required")
    return workspace_id or "local-workspace"


def _store() -> ProjectStore:
    return ProjectStore()


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    payload: ProjectCreate,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> ProjectResponse:
    owner = _owner(user, x_workspace_id)
    project = _store().create(owner, payload)
    event = TelemetryEvent(
        event_name="project_created", properties={"format_count": len(payload.target_formats)}
    )
    _store().record_event(owner, event)
    return project


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    include_archived: bool = False,
    q: str | None = None,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> list[ProjectResponse]:
    return _store().list(_owner(user, x_workspace_id), include_archived, q)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> ProjectResponse:
    try:
        return _store().get(_owner(user, x_workspace_id), project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> ProjectResponse:
    owner = _owner(user, x_workspace_id)
    try:
        project = _store().update(owner, project_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    event = TelemetryEvent(
        event_name="project_updated", properties={"changed_fields": len(payload.model_fields_set)}
    )
    _store().record_event(owner, event)
    return project


@router.delete("/projects/{project_id}", status_code=204)
async def archive_project(
    project_id: str,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> Response:
    owner = _owner(user, x_workspace_id)
    try:
        _store().archive(owner, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    _store().record_event(owner, TelemetryEvent(event_name="project_archived"))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/telemetry/events", status_code=202)
async def record_telemetry(
    event: TelemetryEvent,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> dict[str, str]:
    _store().record_event(_owner(user, x_workspace_id), event)
    return {"status": "accepted"}
