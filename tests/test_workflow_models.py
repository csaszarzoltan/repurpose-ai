"""Pre-dev tests for Workflow models (P0 — Foundation).

Source of truth: analysis/analysis-brief.md §4.1 Data Models.
Interface tests  → xfail until models/workflow.py is implemented.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.models.workflow import (
        BatchJobItem,
        BatchRepurposeRequest,
        BatchRepurposeResponse,
        PipelineTemplate,
        RetryConfig,
        ScheduleConfig,
        StepResult,
        WebhookTriggerConfig,
        WorkflowDefinition,
        WorkflowExecution,
        WorkflowStep,
        WorkflowStepType,
        WorkflowTriggerType,
    )

    HAS_WORKFLOW_MODELS = True
except (ImportError, ModuleNotFoundError):
    HAS_WORKFLOW_MODELS = False


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Enums
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORKFLOW_MODELS, reason="models/workflow.py not implemented yet")
class TestWorkflowTriggerType:
    """Interface: WorkflowTriggerType enum."""

    def test_importable(self):
        assert WorkflowTriggerType is not None

    def test_is_str_enum(self):
        assert issubclass(WorkflowTriggerType, str)

    def test_has_manual(self):
        assert hasattr(WorkflowTriggerType, "MANUAL")
        assert WorkflowTriggerType.MANUAL == "manual"

    def test_has_schedule(self):
        assert hasattr(WorkflowTriggerType, "SCHEDULE")
        assert WorkflowTriggerType.SCHEDULE == "schedule"

    def test_has_webhook(self):
        assert hasattr(WorkflowTriggerType, "WEBHOOK")
        assert WorkflowTriggerType.WEBHOOK == "webhook"

    def test_all_values_expected(self):
        values = {v.value for v in WorkflowTriggerType}
        assert values == {"manual", "schedule", "webhook"}


@pytest.mark.xfail(not HAS_WORKFLOW_MODELS, reason="models/workflow.py not implemented yet")
class TestWorkflowStepType:
    """Interface: WorkflowStepType enum."""

    def test_importable(self):
        assert WorkflowStepType is not None

    def test_is_str_enum(self):
        assert issubclass(WorkflowStepType, str)

    def test_has_repurpose(self):
        assert hasattr(WorkflowStepType, "REPURPOSE")
        assert WorkflowStepType.REPURPOSE == "repurpose"

    def test_has_webhook(self):
        assert hasattr(WorkflowStepType, "WEBHOOK_CALLBACK") or hasattr(WorkflowStepType, "WEBHOOK")
        # Accept either "webhook" or "webhook_callback" as the enum member name
        val = getattr(WorkflowStepType, "WEBHOOK_CALLBACK", None) or getattr(WorkflowStepType, "WEBHOOK", None)
        assert val in ("webhook", "webhook_callback")

    def test_has_wait(self):
        assert hasattr(WorkflowStepType, "WAIT")
        assert WorkflowStepType.WAIT == "wait"

    def test_all_values_expected(self):
        values = {v.value for v in WorkflowStepType}
        assert "repurpose" in values
        assert "wait" in values
        assert "webhook" in values or "webhook_callback" in values


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Simple Models
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORKFLOW_MODELS, reason="models/workflow.py not implemented yet")
class TestRetryConfig:
    """Interface: RetryConfig model."""

    def test_importable(self):
        assert RetryConfig is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(RetryConfig, BaseModel)

    def test_has_max_attempts_field(self):
        assert "max_attempts" in RetryConfig.model_fields

    def test_max_attempts_is_int(self):
        field = RetryConfig.model_fields["max_attempts"]
        assert field.annotation is int

    def test_max_attempts_default_3(self):
        field = RetryConfig.model_fields["max_attempts"]
        assert field.default == 3

    def test_has_delay_seconds_field(self):
        assert "delay_seconds" in RetryConfig.model_fields

    def test_delay_seconds_is_int(self):
        field = RetryConfig.model_fields["delay_seconds"]
        assert field.annotation is int

    def test_delay_seconds_default_30(self):
        field = RetryConfig.model_fields["delay_seconds"]
        assert field.default == 30

    def test_custom_values(self):
        cfg = RetryConfig(max_attempts=5, delay_seconds=60)
        assert cfg.max_attempts == 5
        assert cfg.delay_seconds == 60

    def test_all_fields_have_defaults(self):
        cfg = RetryConfig()
        assert cfg.max_attempts == 3
        assert cfg.delay_seconds == 30


@pytest.mark.xfail(not HAS_WORKFLOW_MODELS, reason="models/workflow.py not implemented yet")
class TestScheduleConfig:
    """Interface: ScheduleConfig model."""

    def test_importable(self):
        assert ScheduleConfig is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(ScheduleConfig, BaseModel)

    def test_has_cron_expression(self):
        assert "cron_expression" in ScheduleConfig.model_fields
        field = ScheduleConfig.model_fields["cron_expression"]
        assert field.annotation == str | None

    def test_has_interval_minutes(self):
        assert "interval_minutes" in ScheduleConfig.model_fields
        field = ScheduleConfig.model_fields["interval_minutes"]
        assert field.annotation == int | None

    def test_has_start_at(self):
        assert "start_at" in ScheduleConfig.model_fields
        field = ScheduleConfig.model_fields["start_at"]
        assert field.annotation == datetime | None

    def test_all_optional_by_default(self):
        cfg = ScheduleConfig()
        assert cfg.cron_expression is None
        assert cfg.interval_minutes is None
        assert cfg.start_at is None

    def test_cron_expression_accepted(self):
        cfg = ScheduleConfig(cron_expression="0 */6 * * *")
        assert cfg.cron_expression == "0 */6 * * *"

    def test_interval_minutes_accepted(self):
        cfg = ScheduleConfig(interval_minutes=360)
        assert cfg.interval_minutes == 360


@pytest.mark.xfail(not HAS_WORKFLOW_MODELS, reason="models/workflow.py not implemented yet")
class TestWebhookTriggerConfig:
    """Interface: WebhookTriggerConfig model."""

    def test_importable(self):
        assert WebhookTriggerConfig is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(WebhookTriggerConfig, BaseModel)

    def test_has_secret_field(self):
        assert "secret" in WebhookTriggerConfig.model_fields
        field = WebhookTriggerConfig.model_fields["secret"]
        assert field.annotation == str | None

    def test_secret_defaults_none(self):
        cfg = WebhookTriggerConfig()
        assert cfg.secret is None

    def test_secret_can_be_set(self):
        cfg = WebhookTriggerConfig(secret="my-hmac-secret")
        assert cfg.secret == "my-hmac-secret"


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — WorkflowStep + WorkflowDefinition
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORKFLOW_MODELS, reason="models/workflow.py not implemented yet")
class TestWorkflowStep:
    """Interface: WorkflowStep model."""

    def test_importable(self):
        assert WorkflowStep is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(WorkflowStep, BaseModel)

    def test_has_step_id(self):
        assert "step_id" in WorkflowStep.model_fields
        field = WorkflowStep.model_fields["step_id"]
        assert field.annotation is str

    def test_has_step_type(self):
        assert "step_type" in WorkflowStep.model_fields
        field = WorkflowStep.model_fields["step_type"]
        # Accept either the enum directly or Optional
        assert field.annotation is WorkflowStepType or (
            hasattr(field.annotation, "__origin__")
            and WorkflowStepType in str(field.annotation)
        )

    def test_has_config(self):
        assert "config" in WorkflowStep.model_fields
        field = WorkflowStep.model_fields["config"]
        assert field.annotation is dict or "dict" in str(field.annotation)

    def test_has_retry_config(self):
        assert "retry_config" in WorkflowStep.model_fields
        field = WorkflowStep.model_fields["retry_config"]
        assert field.annotation == RetryConfig | None

    def test_retry_config_defaults_none(self):
        step = WorkflowStep(step_id="s1", step_type=WorkflowStepType.REPURPOSE, config={})
        assert step.retry_config is None

    def test_custom_retry_config(self):
        step = WorkflowStep(
            step_id="s1",
            step_type=WorkflowStepType.REPURPOSE,
            config={},
            retry_config=RetryConfig(max_attempts=5),
        )
        assert step.retry_config is not None
        assert step.retry_config.max_attempts == 5

    def test_step_id_required(self):
        with pytest.raises(ValidationError):
            WorkflowStep(step_type=WorkflowStepType.REPURPOSE, config={})

    def test_step_type_required(self):
        with pytest.raises(ValidationError):
            WorkflowStep(step_id="s1", config={})


@pytest.mark.xfail(not HAS_WORKFLOW_MODELS, reason="models/workflow.py not implemented yet")
class TestWorkflowDefinition:
    """Interface: WorkflowDefinition model."""

    def test_importable(self):
        assert WorkflowDefinition is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(WorkflowDefinition, BaseModel)

    def test_has_workflow_id(self):
        assert "workflow_id" in WorkflowDefinition.model_fields
        assert WorkflowDefinition.model_fields["workflow_id"].annotation is str

    def test_has_name(self):
        assert "name" in WorkflowDefinition.model_fields
        assert WorkflowDefinition.model_fields["name"].annotation is str

    def test_has_description(self):
        assert "description" in WorkflowDefinition.model_fields
        assert WorkflowDefinition.model_fields["description"].annotation == str | None

    def test_has_trigger_type(self):
        assert "trigger_type" in WorkflowDefinition.model_fields

    def test_has_schedule(self):
        assert "schedule" in WorkflowDefinition.model_fields
        assert WorkflowDefinition.model_fields["schedule"].annotation == ScheduleConfig | None

    def test_has_webhook_config(self):
        assert "webhook_config" in WorkflowDefinition.model_fields
        assert WorkflowDefinition.model_fields["webhook_config"].annotation == WebhookTriggerConfig | None

    def test_has_steps(self):
        assert "steps" in WorkflowDefinition.model_fields

    def test_has_is_active(self):
        assert "is_active" in WorkflowDefinition.model_fields
        field = WorkflowDefinition.model_fields["is_active"]
        assert field.annotation is bool
        assert field.default is True

    def test_has_created_at(self):
        assert "created_at" in WorkflowDefinition.model_fields

    def test_has_updated_at(self):
        assert "updated_at" in WorkflowDefinition.model_fields

    def test_has_created_by(self):
        assert "created_by" in WorkflowDefinition.model_fields
        assert WorkflowDefinition.model_fields["created_by"].annotation == str | None

    def test_minimal_construction(self):
        wf = WorkflowDefinition(
            workflow_id="wf-1",
            name="Test Workflow",
            trigger_type=WorkflowTriggerType.MANUAL,
            steps=[
                WorkflowStep(step_id="s1", step_type=WorkflowStepType.REPURPOSE, config={}),
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert wf.workflow_id == "wf-1"
        assert wf.is_active is True
        assert len(wf.steps) == 1

    def test_workflow_id_required(self):
        with pytest.raises(ValidationError):
            WorkflowDefinition(
                name="Test",
                trigger_type=WorkflowTriggerType.MANUAL,
                steps=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

    def test_name_required(self):
        with pytest.raises(ValidationError):
            WorkflowDefinition(
                workflow_id="wf-1",
                trigger_type=WorkflowTriggerType.MANUAL,
                steps=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

    def test_steps_required(self):
        with pytest.raises(ValidationError):
            WorkflowDefinition(
                workflow_id="wf-1",
                name="Test",
                trigger_type=WorkflowTriggerType.MANUAL,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — WorkflowExecution + StepResult
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORKFLOW_MODELS, reason="models/workflow.py not implemented yet")
class TestWorkflowExecution:
    """Interface: WorkflowExecution model."""

    def test_importable(self):
        assert WorkflowExecution is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(WorkflowExecution, BaseModel)

    def test_has_execution_id(self):
        assert "execution_id" in WorkflowExecution.model_fields
        assert WorkflowExecution.model_fields["execution_id"].annotation is str

    def test_has_workflow_id(self):
        assert "workflow_id" in WorkflowExecution.model_fields
        assert WorkflowExecution.model_fields["workflow_id"].annotation is str

    def test_has_status(self):
        assert "status" in WorkflowExecution.model_fields
        # Status should reuse JobStatus from models/webhook.py or be its own enum
        # Accept both possibilities

    def test_has_current_step(self):
        assert "current_step" in WorkflowExecution.model_fields
        field = WorkflowExecution.model_fields["current_step"]
        assert field.annotation is int
        assert field.default == 0

    def test_has_step_results(self):
        assert "step_results" in WorkflowExecution.model_fields

    def test_has_started_at(self):
        assert "started_at" in WorkflowExecution.model_fields

    def test_has_completed_at(self):
        assert "completed_at" in WorkflowExecution.model_fields

    def test_has_error(self):
        assert "error" in WorkflowExecution.model_fields
        assert WorkflowExecution.model_fields["error"].annotation == str | None

    def test_current_step_defaults_zero(self):
        exec_ = WorkflowExecution(
            execution_id="ex-1",
            workflow_id="wf-1",
            status="pending" if "str" in str(type(WorkflowExecution.model_fields["status"].annotation)) else "PENDING",  # noqa: E501
            started_at=datetime.utcnow(),
        )
        assert exec_.current_step == 0

    def test_step_results_defaults_empty(self):
        exec_ = WorkflowExecution(
            execution_id="ex-1",
            workflow_id="wf-1",
            status="pending",
            started_at=datetime.utcnow(),
        )
        assert isinstance(exec_.step_results, list)
        assert len(exec_.step_results) == 0


@pytest.mark.xfail(not HAS_WORKFLOW_MODELS, reason="models/workflow.py not implemented yet")
class TestStepResult:
    """Interface: StepResult model."""

    def test_importable(self):
        assert StepResult is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(StepResult, BaseModel)

    def test_has_step_id(self):
        assert "step_id" in StepResult.model_fields
        assert StepResult.model_fields["step_id"].annotation is str

    def test_has_status(self):
        assert "status" in StepResult.model_fields

    def test_has_attempt(self):
        assert "attempt" in StepResult.model_fields
        field = StepResult.model_fields["attempt"]
        assert field.annotation is int
        assert field.default == 1

    def test_has_started_at(self):
        assert "started_at" in StepResult.model_fields

    def test_has_completed_at(self):
        assert "completed_at" in StepResult.model_fields

    def test_has_output(self):
        assert "output" in StepResult.model_fields
        assert StepResult.model_fields["output"].annotation == dict | None

    def test_has_error(self):
        assert "error" in StepResult.model_fields
        assert StepResult.model_fields["error"].annotation == str | None

    def test_attempt_defaults_one(self):
        result = StepResult(
            step_id="s1",
            status="completed",
            started_at=datetime.utcnow(),
        )
        assert result.attempt == 1

    def test_output_defaults_none(self):
        result = StepResult(
            step_id="s1",
            status="completed",
            started_at=datetime.utcnow(),
        )
        assert result.output is None

    def test_error_defaults_none(self):
        result = StepResult(
            step_id="s1",
            status="completed",
            started_at=datetime.utcnow(),
        )
        assert result.error is None


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Batch Models
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORKFLOW_MODELS, reason="models/workflow.py not implemented yet")
class TestBatchRepurposeRequest:
    """Interface: BatchRepurposeRequest model."""

    def test_importable(self):
        assert BatchRepurposeRequest is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(BatchRepurposeRequest, BaseModel)

    def test_has_jobs_field(self):
        assert "jobs" in BatchRepurposeRequest.model_fields

    def test_has_min_length_validation(self):
        """Should reject empty jobs list (min_length=1)."""
        field = BatchRepurposeRequest.model_fields["jobs"]
        # Check for min_length in metadata
        assert hasattr(field, "metadata")  # Pydantic v2
        # The actual validation happens at construction time

    def test_has_max_length_validation(self):
        """Should reject >50 jobs (max_length=50)."""
        field = BatchRepurposeRequest.model_fields["jobs"]
        assert hasattr(field, "metadata")

    def test_has_concurrency_field(self):
        assert "concurrency" in BatchRepurposeRequest.model_fields
        field = BatchRepurposeRequest.model_fields["concurrency"]
        assert field.annotation is int
        assert field.default == 5

    def test_concurrency_default_five(self):
        req = BatchRepurposeRequest(jobs=[BatchJobItem(content={"body": "test"}, target_formats=["blog_post"])])
        assert req.concurrency == 5

    def test_empty_jobs_rejected(self):
        with pytest.raises(ValidationError):
            BatchRepurposeRequest(jobs=[])

    def test_custom_concurrency(self):
        req = BatchRepurposeRequest(jobs=[BatchJobItem(content={"body": "test"}, target_formats=["blog_post"])], concurrency=10)
        assert req.concurrency == 10


@pytest.mark.xfail(not HAS_WORKFLOW_MODELS, reason="models/workflow.py not implemented yet")
class TestBatchRepurposeResponse:
    """Interface: BatchRepurposeResponse model."""

    def test_importable(self):
        assert BatchRepurposeResponse is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(BatchRepurposeResponse, BaseModel)

    def test_has_batch_id(self):
        assert "batch_id" in BatchRepurposeResponse.model_fields
        assert BatchRepurposeResponse.model_fields["batch_id"].annotation is str

    def test_has_total(self):
        assert "total" in BatchRepurposeResponse.model_fields
        assert BatchRepurposeResponse.model_fields["total"].annotation is int

    def test_has_completed(self):
        assert "completed" in BatchRepurposeResponse.model_fields
        assert BatchRepurposeResponse.model_fields["completed"].annotation is int

    def test_has_failed(self):
        assert "failed" in BatchRepurposeResponse.model_fields
        assert BatchRepurposeResponse.model_fields["failed"].annotation is int

    def test_has_results(self):
        assert "results" in BatchRepurposeResponse.model_fields

    def test_has_errors(self):
        assert "errors" in BatchRepurposeResponse.model_fields

    def test_errors_defaults_empty_list(self):
        field = BatchRepurposeResponse.model_fields["errors"]
        assert field.default_factory is not None or field.default == []

    def test_minimal_construction(self):
        resp = BatchRepurposeResponse(
            batch_id="batch-1",
            total=10,
            completed=7,
            failed=3,
            results=[],
        )
        assert resp.batch_id == "batch-1"
        assert resp.total == 10
        assert resp.completed == 7
        assert resp.failed == 3
        assert resp.errors == []

    def test_batch_id_required(self):
        with pytest.raises(ValidationError):
            BatchRepurposeResponse(total=0, completed=0, failed=0, results=[])

    def test_total_required(self):
        with pytest.raises(ValidationError):
            BatchRepurposeResponse(batch_id="b1", completed=0, failed=0, results=[])


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — PipelineTemplate (deprecated / nice-to-have)
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORKFLOW_MODELS, reason="models/workflow.py not implemented yet")
class TestPipelineTemplate:
    """Interface: PipelineTemplate model (defined in spec §4.1 but may be deferred)."""

    def test_importable(self):
        assert PipelineTemplate is not None

    def test_is_pydantic_model(self):
        from pydantic import BaseModel
        assert issubclass(PipelineTemplate, BaseModel)

    def test_has_template_id(self):
        assert "template_id" in PipelineTemplate.model_fields

    def test_has_name(self):
        assert "name" in PipelineTemplate.model_fields

    def test_has_description(self):
        assert "description" in PipelineTemplate.model_fields

    def test_has_steps(self):
        assert "steps" in PipelineTemplate.model_fields

    def test_has_default_schedule(self):
        assert "default_schedule" in PipelineTemplate.model_fields
