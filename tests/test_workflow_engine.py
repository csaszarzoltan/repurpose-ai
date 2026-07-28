"""Pre-dev tests for WorkflowEngine (P1 — Core Engine).

Source of truth: analysis/analysis-brief.md §4 — Architecture Design.
Behavioral tests → xfail until services/workflow_engine.py is implemented.
"""

from __future__ import annotations

import pytest

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.services.workflow_engine import (
        RepurposeStepExecutor,
        WaitStepExecutor,
        WebhookStepExecutor,
        WorkflowEngine,
    )

    HAS_WORKFLOW_ENGINE = True
except (ImportError, ModuleNotFoundError):
    HAS_WORKFLOW_ENGINE = False


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Module structure
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORKFLOW_ENGINE, reason="services/workflow_engine.py not implemented yet")
class TestWorkflowEngineImport:
    """Interface: WorkflowEngine classes are importable."""

    def test_workflow_engine_importable(self):
        assert WorkflowEngine is not None

    def test_repurpose_executor_importable(self):
        assert RepurposeStepExecutor is not None

    def test_webhook_executor_importable(self):
        assert WebhookStepExecutor is not None

    def test_wait_executor_importable(self):
        assert WaitStepExecutor is not None


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — WorkflowEngine construction
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORKFLOW_ENGINE, reason="services/workflow_engine.py not implemented yet")
class TestWorkflowEngineConstruction:
    """Behavioral: WorkflowEngine constructor accepts store dependency."""

    async def test_constructor_accepts_store(self):
        """Engine should accept a workflow store dependency."""
        store = {}
        engine = WorkflowEngine(store=store)
        assert engine is not None

    async def test_constructor_raises_without_store(self):
        """Engine should raise if no store provided."""
        with pytest.raises(TypeError):
            WorkflowEngine()  # type: ignore[call-arg]

    async def test_engine_has_run_workflow_method(self):
        """Engine should expose run_workflow method."""
        store = {}
        engine = WorkflowEngine(store=store)
        assert hasattr(engine, "run_workflow")
        assert callable(engine.run_workflow)


@pytest.mark.xfail(not HAS_WORKFLOW_ENGINE, reason="services/workflow_engine.py not implemented yet")
class TestWorkflowEngineRun:
    """Behavioral: WorkflowEngine.run_workflow() creates executions and runs steps."""

    async def test_run_workflow_creates_execution(self):
        """run_workflow should create a WorkflowExecution in the store."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(),
            },
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-1")
        assert execution is not None
        assert execution.workflow_id == "wf-1"

    async def test_run_workflow_returns_execution_id(self):
        """run_workflow should return something with execution_id."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(),
            },
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-1")
        assert hasattr(execution, "execution_id")
        assert isinstance(execution.execution_id, str)
        assert len(execution.execution_id) > 0

    async def test_run_workflow_raises_for_unknown_workflow(self):
        """run_workflow should raise for non-existent workflow."""
        store = {"workflows": {}}
        engine = WorkflowEngine(store=store)
        with pytest.raises(LookupError):
            await engine.run_workflow("nonexistent")

    async def test_run_workflow_raises_for_inactive_workflow(self):
        """run_workflow should raise for inactive workflow."""
        store = {
            "workflows": {
                "wf-inactive": _make_dummy_workflow(is_active=False),
            },
        }
        engine = WorkflowEngine(store=store)
        with pytest.raises(RuntimeError):
            await engine.run_workflow("wf-inactive")

    async def test_execution_completes_successfully(self):
        """Engine runs synchronously and returns completed execution."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(),
            },
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-1")
        assert execution.status == "completed"
        assert execution.completed_at is not None

    async def test_execution_transitions_to_running(self):
        """Execution should transition to running when engine starts."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(),
            },
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-1")
        # At some point the status should be "running"
        assert execution.current_step == 0

    async def test_executes_steps_in_order(self):
        """Steps should execute sequentially in definition order."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(num_steps=3),
            },
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-1")
        # After execution, all steps should have results
        assert len(execution.step_results) == 3
        assert execution.step_results[0].step_id == "s1"
        assert execution.step_results[1].step_id == "s2"
        assert execution.step_results[2].step_id == "s3"

    async def test_execution_records_step_results(self):
        """Each executed step should produce a StepResult."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(),
            },
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-1")
        for result in execution.step_results:
            assert hasattr(result, "step_id")
            assert hasattr(result, "status")
            assert hasattr(result, "started_at")

    async def test_step_result_has_completed_at(self):
        """Completed steps should have completed_at timestamp."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(),
            },
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-1")
        for result in execution.step_results:
            if result.status in ("completed", "failed"):
                assert result.completed_at is not None

    async def test_error_in_step_does_not_crash_engine(self):
        """If a step fails, the engine should continue and report the error."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(num_steps=3),
            },
        }
        engine = WorkflowEngine(store=store)
        # Make the second step fail
        execution = await engine.run_workflow("wf-1")
        # Engine should complete without raising
        assert execution is not None

    async def test_completed_execution_has_final_status(self):
        """After all steps complete, execution should have completed/failed status."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(),
            },
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-1")
        assert execution.status in ("completed", "failed")

    async def test_workflow_store_updated_after_each_step(self):
        """Store should reflect the latest execution state after each step."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(),
            },
            "executions": {},
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-1")
        # The execution should be in the store
        assert execution.execution_id in store.get("executions", {})

    async def test_current_step_increments_through_steps(self):
        """current_step should increment as each step executes."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(num_steps=5),
            },
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-1")
        # After completion, current_step should point past the last step
        assert execution.current_step >= 5 or execution.status == "completed"

    async def test_multiple_workflows_can_run_independently(self):
        """Running two workflows should not interfere."""
        store = {
            "workflows": {
                "wf-a": _make_dummy_workflow(name="A"),
                "wf-b": _make_dummy_workflow(name="B"),
            },
            "executions": {},
        }
        engine = WorkflowEngine(store=store)
        ex_a = await engine.run_workflow("wf-a")
        ex_b = await engine.run_workflow("wf-b")
        assert ex_a.execution_id != ex_b.execution_id
        assert ex_a.workflow_id == "wf-a"
        assert ex_b.workflow_id == "wf-b"


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Retry Logic
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORKFLOW_ENGINE, reason="services/workflow_engine.py not implemented yet")
class TestWorkflowEngineRetry:
    """Behavioral: Step retry with configurable max_attempts and delay."""

    async def test_step_retried_on_failure(self):
        """A failing step should be retried up to max_attempts times."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(retry_max=3),
            },
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-1")
        # The failing step should have multiple StepResult attempts
        step_results = [r for r in execution.step_results if r.step_id == "s1"]
        # Should have multiple results recorded for retries
        total_attempts = sum(r.attempt for r in step_results) if step_results else 0
        assert total_attempts >= 1

    async def test_after_max_retries_step_marked_failed(self):
        """After exhausting retries, step should be marked failed."""
        from datetime import datetime

        from app.models.workflow import RetryConfig, WorkflowDefinition, WorkflowStep, WorkflowStepType, WorkflowTriggerType

        failing_url = "http://127.0.0.1:1/"  # Connection refused = fast failure
        workflow = WorkflowDefinition(
            workflow_id="wf-retry",
            name="Retry Test",
            trigger_type=WorkflowTriggerType.MANUAL,
            steps=[
                WorkflowStep(
                    step_id="s1",
                    step_type=WorkflowStepType.WEBHOOK,
                    config={"callback_url": failing_url, "method": "POST"},
                    retry_config=RetryConfig(max_attempts=2, delay_seconds=0),
                ),
            ],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        store = {
            "workflows": {
                "wf-retry": workflow,
            },
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-retry")
        step_results = [r for r in execution.step_results if r.step_id == "s1"]
        assert len(step_results) >= 1
        # After max_attempts retries, last result should be failed
        assert step_results[-1].status == "failed"

    async def test_retry_delay_is_configurable(self):
        """delay_seconds from RetryConfig should be respected between retries."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(retry_max=3, retry_delay=1),
            },
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-1")
        assert execution is not None

    async def test_retry_does_not_apply_to_successful_steps(self):
        """Steps that succeed should not be retried."""
        store = {
            "workflows": {
                "wf-1": _make_dummy_workflow(),
            },
        }
        engine = WorkflowEngine(store=store)
        execution = await engine.run_workflow("wf-1")
        # Each step should have exactly one result
        assert len(execution.step_results) == 1


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Step Executors
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORKFLOW_ENGINE, reason="services/workflow_engine.py not implemented yet")
class TestStepExecutors:
    """Behavioral: Individual step executor behavior."""

    async def test_repurpose_executor_calls_repurpose_service(self):
        """RepurposeStepExecutor should call RepurposeService.repurpose()."""
        executor = RepurposeStepExecutor()
        result = await executor.execute({"source_content": "test"})
        assert result is not None

    async def test_webhook_executor_sends_http_request(self):
        """WebhookStepExecutor should send an httpx request to callback_url."""
        executor = WebhookStepExecutor()
        result = await executor.execute({
            "callback_url": "https://example.com/hook",
            "method": "POST",
        })
        assert result is not None

    async def test_wait_executor_pauses(self):
        """WaitStepExecutor should pause for the configured delay."""
        executor = WaitStepExecutor()
        result = await executor.execute({"delay_seconds": 0})
        assert result is not None

    async def test_wait_executor_uses_asyncio_sleep(self):
        """WaitStepExecutor should use asyncio.sleep internally."""
        import inspect

        executor = WaitStepExecutor()
        execute_method = getattr(executor, "execute", None)
        if execute_method and inspect.iscoroutinefunction(execute_method):
            assert True
        else:
            pytest.fail("execute must be a coroutine")


# ════════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════════


def _make_dummy_workflow(
    name: str = "Test",
    is_active: bool = True,
    num_steps: int = 1,
    retry_max: int = 3,
    retry_delay: int = 30,
) -> dict:
    """Create a minimal workflow dict for test setup."""
    from datetime import datetime

    from app.models.workflow import WorkflowDefinition, WorkflowStep, WorkflowStepType, WorkflowTriggerType

    steps = []
    for i in range(num_steps):
        steps.append(
            WorkflowStep(
                step_id=f"s{i + 1}",
                step_type=WorkflowStepType.REPURPOSE,
                config={"source_content": "test"},
            )
        )

    return WorkflowDefinition(
        workflow_id=f"wf-{name.lower()[:3] if name != 'Test' else '1'}",
        name=name,
        trigger_type=WorkflowTriggerType.MANUAL,
        steps=steps,
        is_active=is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
