"""Workflow models for the Workflow Automation feature (v0.5.0)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

# ── Enums ──────────────────────────────────────────────────────────────────────


class WorkflowTriggerType(StrEnum):
    """How a workflow is triggered."""

    MANUAL = "manual"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"


class WorkflowStepType(StrEnum):
    """Types of steps a workflow can execute."""

    REPURPOSE = "repurpose"
    WEBHOOK = "webhook"
    WAIT = "wait"


# ── Config Models ──────────────────────────────────────────────────────────────


class RetryConfig(BaseModel):
    """Retry policy for a workflow step."""

    max_attempts: int = 3
    delay_seconds: int = 30


class ScheduleConfig(BaseModel):
    """Schedule configuration for a workflow."""

    cron_expression: str | None = None
    interval_minutes: int | None = None
    start_at: datetime | None = None


class WebhookTriggerConfig(BaseModel):
    """Webhook trigger configuration."""

    secret: str | None = None


# ── Core Workflow Models ───────────────────────────────────────────────────────


class WorkflowStep(BaseModel):
    """A single step in a workflow pipeline."""

    step_id: str
    step_type: WorkflowStepType
    config: dict = Field(default_factory=dict)
    retry_config: RetryConfig | None = None


class WorkflowDefinition(BaseModel):
    """A complete workflow definition."""

    workflow_id: str
    name: str
    description: str | None = None
    trigger_type: WorkflowTriggerType
    schedule: ScheduleConfig | None = None
    webhook_config: WebhookTriggerConfig | None = None
    steps: list[WorkflowStep]
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None


class StepResult(BaseModel):
    """Result of executing a single workflow step."""

    step_id: str
    status: str
    attempt: int = 1
    started_at: datetime
    completed_at: datetime | None = None
    output: dict | None = None
    error: str | None = None


class WorkflowExecution(BaseModel):
    """Runtime record of a workflow execution."""

    execution_id: str
    workflow_id: str
    status: str
    current_step: int = 0
    step_results: list[StepResult] = Field(default_factory=list)
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None


# ── Batch Models ───────────────────────────────────────────────────────────────


class BatchJobItem(BaseModel):
    """A single job within a batch repurpose request."""

    content: dict
    target_formats: list[str]


class BatchRepurposeRequest(BaseModel):
    """Request to repurpose multiple content items in batch."""

    jobs: list[BatchJobItem] = Field(min_length=1, max_length=50)
    concurrency: int = 5


class BatchRepurposeResponse(BaseModel):
    """Response from a batch repurpose operation."""

    batch_id: str
    total: int
    completed: int
    failed: int
    results: list
    errors: list = Field(default_factory=list)


# ── PipelineTemplate (optional / nice-to-have) ────────────────────────────────


class PipelineTemplate(BaseModel):
    """Reusable pipeline template (defined in spec, may be deferred)."""

    template_id: str
    name: str
    description: str | None = None
    steps: list[WorkflowStep]
    default_schedule: ScheduleConfig | None = None
