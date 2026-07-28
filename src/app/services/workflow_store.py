"""In-memory workflow store — alpha stage, no database.

Stores workflow definitions and executions in module-level dicts.
"""

from __future__ import annotations

from app.models.workflow import WorkflowDefinition, WorkflowExecution

# ── In-memory stores ───────────────────────────────────────────────────────────

WORKFLOWS_DB: dict[str, WorkflowDefinition] = {}
WORKFLOW_EXECUTIONS_DB: dict[str, WorkflowExecution] = {}


# ── CRUD helpers — WorkflowDefinition ──────────────────────────────────────────


def create_workflow(workflow: WorkflowDefinition) -> WorkflowDefinition:
    """Store a new workflow definition."""
    WORKFLOWS_DB[workflow.workflow_id] = workflow
    return workflow


def get_workflow(workflow_id: str) -> WorkflowDefinition | None:
    """Retrieve a workflow definition by id."""
    return WORKFLOWS_DB.get(workflow_id)


def list_workflows(active_only: bool | None = None) -> list[WorkflowDefinition]:
    """List all workflow definitions, optionally filtering by active status."""
    workflows = list(WORKFLOWS_DB.values())
    if active_only is not None:
        workflows = [w for w in workflows if w.is_active == active_only]
    return workflows


# ── CRUD helpers — WorkflowExecution ───────────────────────────────────────────


def create_execution(execution: WorkflowExecution) -> WorkflowExecution:
    """Store a new workflow execution record."""
    WORKFLOW_EXECUTIONS_DB[execution.execution_id] = execution
    return execution


def get_execution(execution_id: str) -> WorkflowExecution | None:
    """Retrieve a workflow execution by id."""
    return WORKFLOW_EXECUTIONS_DB.get(execution_id)


def list_executions(
    workflow_id: str | None = None,
) -> list[WorkflowExecution]:
    """List executions, optionally filtered by workflow_id."""
    executions = list(WORKFLOW_EXECUTIONS_DB.values())
    if workflow_id is not None:
        executions = [e for e in executions if e.workflow_id == workflow_id]
    return executions


def update_execution(execution: WorkflowExecution) -> None:
    """Update an existing execution record in-place."""
    WORKFLOW_EXECUTIONS_DB[execution.execution_id] = execution
