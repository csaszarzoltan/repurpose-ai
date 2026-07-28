"""Workflow engine — sequential step runner with retry support."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime

import httpx

from app.models.content import BrandVoice, ContentFormat, ContentItem
from app.models.workflow import (
    RetryConfig,
    StepResult,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
    WorkflowStepType,
)
from app.services.repurpose import RepurposeService
from app.services.ssrf import SSRFChecker

logger = logging.getLogger(__name__)


# ── Step Executors ─────────────────────────────────────────────────────────────


class RepurposeStepExecutor:
    """Executes a repurpose workflow step via RepurposeService."""

    async def execute(self, config: dict) -> dict:
        """Run the repurpose step.

        config may contain source_content, target_formats, brand_voice, etc.
        Returns a result dict.
        """
        try:
            svc = RepurposeService()
            target_formats = config.get("target_formats")
            if target_formats is None:
                target_formats = [config.get("source_format", "blog_post")]

            body_content = ContentItem(
                title=config.get("source_title", ""),
                body=config.get("source_content", ""),
                source_format=ContentFormat.BLOG_POST,
            )

            parsed_formats = []
            for t in target_formats:
                if isinstance(t, str) and ContentFormat.__members__.get(t.upper().replace("-", "_"), None):
                    parsed_formats.append(ContentFormat(t))
                else:
                    parsed_formats.append(ContentFormat.BLOG_POST)

            response = await svc.repurpose(
                content=body_content,
                target_formats=parsed_formats,
                brand_voice=BrandVoice(config.get("brand_voice", "professional")),
                custom_instructions=config.get("custom_instructions"),
            )
            return {"status": "completed", "data": response.model_dump() if hasattr(response, "model_dump") else str(response)}
        except Exception as exc:
            logger.warning("RepurposeStepExecutor failed: %s", exc)
            return {"status": "failed", "error": str(exc)}


class WebhookStepExecutor:
    """Executes a webhook call workflow step."""

    async def execute(self, config: dict) -> dict:
        """Send an HTTP request to the configured callback URL."""
        callback_url = config.get("callback_url", "")
        method = config.get("method", "POST").upper()
        payload = config.get("payload", {})
        headers = config.get("headers", {})

        # SSRF validation
        checker = SSRFChecker()
        if not checker.validate_url(callback_url):
            logger.warning("WebhookStepExecutor: SSRF-blocked callback URL %s", callback_url)
            return {"status": "failed", "error": "SSRF-blocked callback URL"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    resp = await client.get(callback_url, headers=headers)
                elif method == "PUT":
                    resp = await client.put(callback_url, json=payload, headers=headers)
                else:
                    resp = await client.post(callback_url, json=payload, headers=headers)
                resp.raise_for_status()
                return {"status": "completed", "status_code": resp.status_code}
        except Exception as exc:
            logger.warning("WebhookStepExecutor failed: %s", exc)
            return {"status": "failed", "error": str(exc)}


class WaitStepExecutor:
    """Executes a wait/delay workflow step."""

    async def execute(self, config: dict) -> dict:
        """Sleep for the configured delay."""
        delay = config.get("delay_seconds", 0)
        await asyncio.sleep(delay)
        return {"status": "completed", "delay_seconds": delay}


# ── Engine ─────────────────────────────────────────────────────────────────────


class WorkflowEngine:
    """Sequential workflow step runner.

    Accepts a store dict with keys:
      - "workflows": dict[str, WorkflowDefinition]
      - "executions": dict[str, WorkflowExecution]  (optional, created if absent)
    """

    def __init__(self, store: dict) -> None:
        self.store = store

    async def run_workflow(self, workflow_id: str) -> WorkflowExecution:
        """Execute a workflow by id, creating an execution and running all steps."""
        workflows = self.store.get("workflows", {})
        workflow = workflows.get(workflow_id)
        if workflow is None:
            raise LookupError(f"Workflow '{workflow_id}' not found")

        # Handle both WorkflowDefinition and dict
        is_active = workflow.is_active if isinstance(workflow, WorkflowDefinition) else workflow.get("is_active", True)
        if not is_active:
            raise RuntimeError(f"Workflow '{workflow_id}' is inactive")

        # Get steps — handle both model and dict
        if isinstance(workflow, WorkflowDefinition):
            steps = workflow.steps
        else:
            from app.models.workflow import WorkflowStep, WorkflowStepType

            raw_steps = workflow.get("steps", [])
            steps = []
            for s in raw_steps:
                if isinstance(s, WorkflowStep):
                    steps.append(s)
                elif isinstance(s, dict):
                    step_type_str = s.get("step_type", "repurpose")
                    try:
                        step_type = WorkflowStepType(step_type_str)
                    except ValueError:
                        step_type = WorkflowStepType.REPURPOSE
                    steps.append(
                        WorkflowStep(
                            step_id=s.get("step_id", "unknown"),
                            step_type=step_type,
                            config=s.get("config", {}),
                        )
                    )
                else:
                    steps = []

        now = datetime.utcnow()
        execution = WorkflowExecution(
            execution_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            status="pending",
            current_step=0,
            step_results=[],
            started_at=now,
        )

        # Store execution
        executions = self.store.setdefault("executions", {})
        executions[execution.execution_id] = execution

        # Transition to running
        execution.status = "running"
        executions[execution.execution_id] = execution

        # Run each step sequentially
        for step_idx, step in enumerate(steps):
            execution.current_step = step_idx
            _update_store(executions, execution)

            retry_config = step.retry_config or RetryConfig(max_attempts=1, delay_seconds=0)
            max_attempts = retry_config.max_attempts
            delay = retry_config.delay_seconds

            step_succeeded = False
            for attempt in range(1, max_attempts + 1):
                step_start = datetime.utcnow()
                result_data = await self._execute_step(step)
                step_end = datetime.utcnow()

                step_result = StepResult(
                    step_id=step.step_id,
                    status="completed" if result_data.get("status") == "completed" else "failed",
                    attempt=attempt,
                    started_at=step_start,
                    completed_at=step_end,
                    output=result_data if result_data.get("status") == "completed" else None,
                    error=result_data.get("error") if result_data.get("status") != "completed" else None,
                )
                execution.step_results.append(step_result)
                _update_store(executions, execution)

                if step_result.status == "completed":
                    step_succeeded = True
                    break

                if attempt < max_attempts and delay > 0:
                    await asyncio.sleep(delay)

            if not step_succeeded:
                # Step failed after all retries — mark execution but continue
                execution.error = (
                    f"Step '{step.step_id}' failed after {max_attempts} attempt(s)"
                )
                _update_store(executions, execution)

        # Mark execution complete
        if any(r.status == "failed" for r in execution.step_results):
            execution.status = "failed"
        else:
            execution.status = "completed"
        execution.completed_at = datetime.utcnow()
        _update_store(executions, execution)

        return execution

    async def _execute_step(self, step: WorkflowStep) -> dict:
        """Dispatch a step to the appropriate executor and return the result."""
        if step.step_type == WorkflowStepType.REPURPOSE:
            executor = RepurposeStepExecutor()
        elif step.step_type == WorkflowStepType.WEBHOOK:
            executor = WebhookStepExecutor()
        elif step.step_type == WorkflowStepType.WAIT:
            executor = WaitStepExecutor()
        else:
            return {"status": "failed", "error": f"Unknown step type: {step.step_type}"}

        try:
            return await executor.execute(step.config)
        except Exception as exc:
            logger.exception("Step '%s' executor raised: %s", step.step_id, exc)
            return {"status": "failed", "error": str(exc)}
def _update_store(
    executions: dict[str, WorkflowExecution],
    execution: WorkflowExecution,
) -> None:
    """Update the in-memory execution store."""
    executions[execution.execution_id] = execution


def _content_from_config(config: dict) -> str:
    """Extract source content from step config."""
    return config.get("source_content", config.get("content", ""))
