"""Workflow scheduler — polls for due workflows and triggers execution."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime

from app.models.workflow import WorkflowDefinition, WorkflowExecution, WorkflowTriggerType
from app.services.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


class WorkflowScheduler:
    """Periodically polls the workflow store for due scheduled workflows.

    Attributes:
        running: Whether the scheduler loop is active.
        poll_interval: Seconds between polls (default 60).
    """

    def __init__(
        self,
        store: dict,
        poll_interval: int = 60,
        auto_start: bool = True,
    ) -> None:
        self.store = store
        self.poll_interval = poll_interval
        self._task: asyncio.Task | None = None
        self.running = False

        if auto_start:
            self.start()

    def start(self) -> None:
        """Start the scheduler loop."""
        if not self.running:
            self.running = True
            # In async context, create a background task
            with contextlib.suppress(RuntimeError):
                self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the scheduler cleanly (idempotent)."""
        if not self.running:
            return
        self.running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def check_due_workflows(self) -> list[dict]:
        """Return a list of workflow dicts that are due to run."""
        workflows = self.store.get("workflows", {})
        due: list[dict] = []
        now = datetime.utcnow()

        for _wf_id, wf in workflows.items():
            # Only scheduled workflows
            if not isinstance(wf, (WorkflowDefinition, dict)):
                continue

            trigger_type = _get_trigger_type(wf)
            if trigger_type != WorkflowTriggerType.SCHEDULE:
                continue

            # Must be active
            is_active = wf.is_active if isinstance(wf, WorkflowDefinition) else wf.get("is_active", True)
            if not is_active:
                continue

            schedule = wf.schedule if isinstance(wf, WorkflowDefinition) else wf.get("schedule")
            if schedule is None:
                continue

            # Check start_at
            start_at = None
            interval_minutes = None
            if isinstance(schedule, dict):
                start_at = schedule.get("start_at")
                interval_minutes = schedule.get("interval_minutes")
            else:
                start_at = getattr(schedule, "start_at", None)
                interval_minutes = getattr(schedule, "interval_minutes", None)

            if start_at is not None and start_at > now:
                continue

            # If there's an interval, it's due (no last-run tracking in alpha store)
            if interval_minutes is not None and interval_minutes > 0:
                due.append(_wf_to_dict(wf))
                continue

            # Cron — also due (simple alpha handling)
            cron_expr = None
            if isinstance(schedule, dict):
                cron_expr = schedule.get("cron_expression")
            else:
                cron_expr = getattr(schedule, "cron_expression", None)

            if cron_expr:
                due.append(_wf_to_dict(wf))

        return due

    async def tick(self) -> None:
        """Single poll cycle: detect due workflows and create executions."""
        due = await self.check_due_workflows()
        for wf in due:
            wf_id = wf["workflow_id"] if isinstance(wf, dict) else wf
            execution = await self._create_execution(wf_id)
            logger.info("Scheduler created execution %s for workflow %s", execution.execution_id, wf_id)

    async def _create_execution(self, workflow_id: str) -> WorkflowExecution:
        """Create a new execution for a due workflow via the engine."""
        engine = WorkflowEngine(store=self.store)
        execution = await engine.run_workflow(workflow_id)
        return execution

    async def _run(self) -> None:
        """Main scheduler loop."""
        while self.running:
            try:
                await self.tick()
            except Exception as exc:
                logger.exception("Scheduler tick failed: %s", exc)
            await asyncio.sleep(self.poll_interval)


def _get_trigger_type(wf: WorkflowDefinition | dict) -> WorkflowTriggerType:
    """Get the trigger type from a workflow definition (model or dict)."""
    if isinstance(wf, WorkflowDefinition):
        return wf.trigger_type
    trigger_str = wf.get("trigger_type", "manual")
    try:
        return WorkflowTriggerType(trigger_str)
    except ValueError:
        return WorkflowTriggerType.MANUAL


def _wf_to_dict(wf: WorkflowDefinition | dict) -> dict:
    """Convert a workflow definition (model or dict) to a plain dict."""
    if isinstance(wf, WorkflowDefinition):
        return {
            "workflow_id": wf.workflow_id,
            "name": wf.name,
            "description": wf.description,
            "trigger_type": wf.trigger_type.value if hasattr(wf.trigger_type, "value") else wf.trigger_type,
            "is_active": wf.is_active,
            "schedule": wf.schedule.model_dump() if wf.schedule and hasattr(wf.schedule, "model_dump") else wf.schedule,
        }
    return wf
