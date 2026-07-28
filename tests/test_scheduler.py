"""Pre-dev tests for WorkflowScheduler (P3 — Scheduling Engine).

Source of truth: analysis/analysis-brief.md §4.6 (scheduler.py),
§5 (Phase 3 tasks).
Behavioral tests → xfail until services/scheduler.py is implemented.
"""

from __future__ import annotations

import pytest

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.services.scheduler import WorkflowScheduler

    HAS_SCHEDULER = True
except (ImportError, ModuleNotFoundError):
    HAS_SCHEDULER = False


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_SCHEDULER, reason="services/scheduler.py not implemented yet")
class TestWorkflowSchedulerInterface:
    """Interface: WorkflowScheduler class is importable."""

    def test_importable(self):
        assert WorkflowScheduler is not None

    def test_is_class(self):
        assert isinstance(WorkflowScheduler, type)

    def test_has_start_method(self):
        assert hasattr(WorkflowScheduler, "start")
        assert callable(WorkflowScheduler.start)

    def test_has_stop_method(self):
        assert hasattr(WorkflowScheduler, "stop")
        assert callable(WorkflowScheduler.stop)


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Scheduler lifecycle
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_SCHEDULER, reason="services/scheduler.py not implemented yet")
class TestWorkflowSchedulerLifecycle:
    """Behavioral: Scheduler start/stop lifecycle."""

    async def test_scheduler_starts_on_create(self):
        """Scheduler should start automatically when created with auto_start=True."""
        scheduler = WorkflowScheduler(store={}, poll_interval=3600)
        assert scheduler is not None
        assert scheduler.running is True

    async def test_scheduler_stops_gracefully(self):
        """Scheduler.stop() should stop the scheduler cleanly."""
        scheduler = WorkflowScheduler(store={}, poll_interval=3600)
        await scheduler.stop()
        assert scheduler.running is False

    async def test_scheduler_stop_is_idempotent(self):
        """Calling stop twice should not raise."""
        scheduler = WorkflowScheduler(store={}, poll_interval=3600)
        await scheduler.stop()
        await scheduler.stop()  # Second stop should be a no-op
        assert scheduler.running is False

    async def test_scheduler_accepts_poll_interval(self):
        """Poll interval should be configurable."""
        scheduler = WorkflowScheduler(store={}, poll_interval=60)
        assert scheduler.poll_interval == 60

    async def test_scheduler_default_poll_interval(self):
        """Default poll interval should be 60 seconds."""
        scheduler = WorkflowScheduler(store={})
        assert scheduler.poll_interval == 60


@pytest.mark.xfail(not HAS_SCHEDULER, reason="services/scheduler.py not implemented yet")
class TestWorkflowSchedulerExecution:
    """Behavioral: Scheduler detects due workflows and triggers execution."""

    async def test_detects_due_workflows(self):
        """Scheduler should detect workflows that are due to run."""
        store = {
            "workflows": {
                "wf-1": _make_scheduled_workflow(),
            },
        }
        scheduler = WorkflowScheduler(store=store, poll_interval=60)
        due = await scheduler.check_due_workflows()
        assert len(due) >= 1
        assert "wf-1" in [w["workflow_id"] for w in due] or "wf-1" in due

    async def test_creates_execution_for_due_workflow(self):
        """For each due workflow, scheduler should create a WorkflowExecution."""
        store = {
            "workflows": {
                "wf-1": _make_scheduled_workflow(),
            },
            "executions": {},
        }
        scheduler = WorkflowScheduler(store=store, poll_interval=60)
        await scheduler.tick()
        assert "executions" in store
        # At least one execution should exist
        assert len(store["executions"]) >= 1

    async def test_skips_inactive_workflows(self):
        """Inactive workflows should not be triggered by scheduler."""
        store = {
            "workflows": {
                "wf-inactive": _make_scheduled_workflow(is_active=False),
            },
            "executions": {},
        }
        scheduler = WorkflowScheduler(store=store, poll_interval=60)
        due = await scheduler.check_due_workflows()
        assert len(due) == 0

    async def test_skips_workflows_with_future_schedule(self):
        """Workflows with future start_at should be skipped."""
        from datetime import datetime, timedelta

        store = {
            "workflows": {
                "wf-future": _make_scheduled_workflow(
                    start_at=datetime.utcnow() + timedelta(days=365),
                ),
            },
        }
        scheduler = WorkflowScheduler(store=store, poll_interval=60)
        due = await scheduler.check_due_workflows()
        # Should not be detected as due
        assert len(due) == 0

    async def test_skips_manual_triggers(self):
        """Workflows with trigger_type=manual should be skipped by scheduler."""
        store = {
            "workflows": {
                "wf-manual": _make_scheduled_workflow(trigger_type="manual"),
            },
        }
        scheduler = WorkflowScheduler(store=store, poll_interval=60)
        due = await scheduler.check_due_workflows()
        assert len(due) == 0

    async def test_cron_expression_evaluated(self):
        """Workflows with cron expressions should be evaluated correctly."""
        store = {
            "workflows": {
                "wf-cron": _make_workflow_with_cron("*/5 * * * *"),
            },
        }
        scheduler = WorkflowScheduler(store=store, poll_interval=60)
        # Should not crash when evaluating
        due = await scheduler.check_due_workflows()
        assert isinstance(due, list)


# ════════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════════


def _make_scheduled_workflow(
    is_active: bool = True,
    trigger_type: str = "schedule",
    start_at=None,
) -> dict:
    """Create a minimal scheduled workflow dict for test setup."""
    from datetime import datetime

    return {
        "workflow_id": "wf-1",
        "name": "Scheduled Workflow",
        "trigger_type": trigger_type,
        "schedule": {
            "cron_expression": None,
            "interval_minutes": 60,
            "start_at": start_at,
        },
        "webhook_config": None,
        "steps": [
            {"step_id": "s1", "step_type": "repurpose", "config": {}},
        ],
        "is_active": is_active,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": None,
    }


def _make_workflow_with_cron(cron_expr: str) -> dict:
    """Create a scheduled workflow with a cron expression."""
    from datetime import datetime

    return {
        "workflow_id": "wf-cron",
        "name": "Cron Workflow",
        "trigger_type": "schedule",
        "schedule": {
            "cron_expression": cron_expr,
            "interval_minutes": None,
            "start_at": None,
        },
        "webhook_config": None,
        "steps": [
            {"step_id": "s1", "step_type": "repurpose", "config": {}},
        ],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": None,
    }
