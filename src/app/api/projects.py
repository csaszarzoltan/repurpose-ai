"""User-centered project workspace and privacy-safe telemetry endpoints."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status

from app.dependencies import get_optional_user
from app.models.content import ContentItem
from app.models.project import (
    GenerationResponse,
    ProjectCreate,
    ProjectDuplicate,
    ProjectResponse,
    ProjectUpdate,
    TelemetryEvent,
    VariantResponse,
    VariantUpdate,
    WorkspaceSummary,
)
from app.services.generation_factory import build_generation_service
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


@router.get("/workspace/summary", response_model=WorkspaceSummary)
async def workspace_summary(
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> WorkspaceSummary:
    return _store().workspace_summary(_owner(user, x_workspace_id))


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


@router.post("/projects/{project_id}/duplicate", response_model=ProjectResponse, status_code=201)
async def duplicate_project(
    project_id: str,
    payload: ProjectDuplicate,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> ProjectResponse:
    owner = _owner(user, x_workspace_id)
    try:
        project = _store().duplicate(owner, project_id, payload.title)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    _store().record_event(
        owner, TelemetryEvent(event_name="project_created", properties={"source": "duplicate"})
    )
    return project


@router.post("/projects/{project_id}/restore", response_model=ProjectResponse)
async def restore_archived_project(
    project_id: str,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> ProjectResponse:
    owner = _owner(user, x_workspace_id)
    try:
        project = _store().restore_project(owner, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None
    _store().record_event(
        owner, TelemetryEvent(event_name="project_updated", properties={"action": "restore"})
    )
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


@router.post("/projects/{project_id}/generate", response_model=GenerationResponse, status_code=201)
async def generate_project_variants(
    project_id: str,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> GenerationResponse:
    owner = _owner(user, x_workspace_id)
    store = _store()
    try:
        project = store.get(owner, project_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None

    content = ContentItem(
        id=project.id,
        title=project.title,
        body=project.body,
        source_format=project.source_format,
    )
    service, generation_mode = build_generation_service(user=user)
    result = await service.repurpose(
        content=content,
        target_formats=project.target_formats,
        brand_voice=project.brand_voice,
        custom_instructions=project.custom_instructions,
    )
    warning = None
    if generation_mode == "template_fallback":
        warning = (
            "Generated drafts use template fallback because no configured LLM provider "
            "is available in this workspace. Review every draft before publishing."
        )
    elif result.warnings:
        generation_mode = "llm_fallback"
        warning = " ".join(result.warnings)
    variants = [
        store.create_variant(
            owner_id=owner,
            project_id=project.id,
            format_id=format_id.value,
            content=generated,
            generation_mode=generation_mode,
        )
        for format_id, generated in result.repurposed.items()
    ]
    store.record_event(
        owner,
        TelemetryEvent(
            event_name="generation_started",
            properties={"format_count": len(variants), "generation_mode": generation_mode},
        ),
    )
    return GenerationResponse(
        project_id=project.id,
        generation_mode=generation_mode,
        warning=warning,
        variants=variants,
    )


@router.get("/projects/{project_id}/variants", response_model=list[VariantResponse])
async def list_project_variants(
    project_id: str,
    include_history: bool = False,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> list[VariantResponse]:
    try:
        return _store().list_variants(
            _owner(user, x_workspace_id), project_id, include_history=include_history
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found") from None


@router.post(
    "/projects/{project_id}/variants/{variant_id}/restore",
    response_model=VariantResponse,
    status_code=201,
)
async def restore_project_variant(
    project_id: str,
    variant_id: str,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> VariantResponse:
    try:
        return _store().restore_variant(
            _owner(user, x_workspace_id), project_id, variant_id
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Variant not found") from None


@router.patch(
    "/projects/{project_id}/variants/{variant_id}", response_model=VariantResponse
)
async def revise_project_variant(
    project_id: str,
    variant_id: str,
    payload: VariantUpdate,
    user: UserResponse | None = Depends(get_optional_user),
    x_workspace_id: str | None = Header(default=None),
) -> VariantResponse:
    try:
        return _store().revise_variant(
            owner_id=_owner(user, x_workspace_id),
            project_id=project_id,
            variant_id=variant_id,
            content=payload.content,
            status=payload.status,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Variant not found") from None
