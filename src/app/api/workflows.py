"""Workflow management API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.models.workflow import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowStepType,
    WorkflowTriggerType,
)
from app.services.workflow_engine import WorkflowEngine
from app.services.workflow_store import WORKFLOWS_DB, create_workflow

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


def _make_engine() -> WorkflowEngine:
    """Create a WorkflowEngine backed by the shared in-memory store."""
    return WorkflowEngine(store={"workflows": WORKFLOWS_DB})


def _validate_steps(steps: list[dict]) -> list[WorkflowStep]:
    """Validate and deduplicate step definitions."""
    seen_ids: set[str] = set()
    parsed_steps: list[WorkflowStep] = []
    for step_data in steps:
        # Validate step_type
        step_type_str = step_data.get("step_type", "")
        try:
            step_type = WorkflowStepType(step_type_str)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid step_type: '{step_type_str}'",
            ) from None

        step = WorkflowStep(
            step_id=step_data["step_id"],
            step_type=step_type,
            config=step_data.get("config", {}),
        )

        # Duplicate step_id check
        if step.step_id in seen_ids:
            raise HTTPException(
                status_code=422,
                detail=f"Duplicate step_id: '{step.step_id}'",
            )
        seen_ids.add(step.step_id)
        parsed_steps.append(step)

    return parsed_steps


@router.post("", status_code=201)
async def create_workflow_endpoint(body: dict) -> dict:
    """Create a new workflow definition."""
    name = body.get("name")
    if not name:
        raise HTTPException(status_code=422, detail="name is required")

    steps_data = body.get("steps")
    if not steps_data:
        raise HTTPException(status_code=422, detail="steps is required")
    if not isinstance(steps_data, list) or len(steps_data) == 0:
        raise HTTPException(status_code=422, detail="steps must be a non-empty list")

    trigger_type_str = body.get("trigger_type", "manual")
    try:
        trigger_type = WorkflowTriggerType(trigger_type_str)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid trigger_type: '{trigger_type_str}'") from None

    parsed_steps = _validate_steps(steps_data)

    now = datetime.utcnow()
    workflow_id = str(uuid.uuid4())

    # Build optional schedule / webhook config
    schedule = None
    if body.get("schedule"):
        from app.models.workflow import ScheduleConfig
        schedule = ScheduleConfig(**body["schedule"])

    webhook_config = None
    if body.get("webhook_config"):
        from app.models.workflow import WebhookTriggerConfig
        webhook_config = WebhookTriggerConfig(**body["webhook_config"])

    wf = WorkflowDefinition(
        workflow_id=workflow_id,
        name=name,
        description=body.get("description"),
        trigger_type=trigger_type,
        schedule=schedule,
        webhook_config=webhook_config,
        steps=parsed_steps,
        is_active=body.get("is_active", True),
        created_at=now,
        updated_at=now,
        created_by=body.get("created_by"),
    )

    create_workflow(wf)
    return {"workflow_id": workflow_id}


@router.get("")
async def list_workflows_endpoint(active: str | None = None) -> list:
    """List all workflow definitions."""
    from app.services.workflow_store import list_workflows

    active_filter = None
    if active is not None:
        active_filter = active.lower() == "true"

    return [
        wf.model_dump() for wf in list_workflows(active_only=active_filter)
    ]


@router.post("/{workflow_id}/trigger", status_code=202)
async def trigger_workflow(workflow_id: str) -> dict:
    """Manually trigger a workflow by id."""
    from app.services.workflow_store import get_workflow

    wf = get_workflow(workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if not wf.is_active:
        raise HTTPException(status_code=409, detail="Workflow is inactive")

    engine = _make_engine()
    execution = await engine.run_workflow(workflow_id)

    return {"execution_id": execution.execution_id}
