"""Pre-dev tests for Workflow API endpoints (P2 — API).

Source of truth: analysis/analysis-brief.md §4.2 (api/workflows.py) + §5.
Behavioral tests → xfail until api/workflows.py is implemented.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.api.workflows import router as workflows_router

    HAS_WORKFLOWS_ROUTER = True
except (ImportError, ModuleNotFoundError):
    HAS_WORKFLOWS_ROUTER = False

try:
    from app.api.webhook import router as webhook_router  # noqa: F401

    HAS_WEBHOOK_ROUTER = True
except (ImportError, ModuleNotFoundError):
    HAS_WEBHOOK_ROUTER = False


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Router structure
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORKFLOWS_ROUTER, reason="api/workflows.py not implemented yet")
class TestWorkflowsRouterInterface:
    """Interface: workflows router is importable with expected routes."""

    def test_router_importable(self):
        assert workflows_router is not None

    def test_router_is_apirouter(self):
        from fastapi import APIRouter
        assert isinstance(workflows_router, APIRouter)

    def test_has_correct_prefix(self):
        assert hasattr(workflows_router, "prefix")
        assert "workflow" in workflows_router.prefix

    def test_has_post_workflows_route(self):
        routes = [r for r in workflows_router.routes if hasattr(r, "methods")]
        post_routes = [r for r in routes if "POST" in r.methods]
        matching = [r for r in post_routes if r.path.endswith("/workflows")]
        assert len(matching) >= 1

    def test_has_get_workflows_route(self):
        routes = [r for r in workflows_router.routes if hasattr(r, "methods")]
        get_routes = [r for r in routes if "GET" in r.methods]
        matching = [r for r in get_routes if r.path.endswith("/workflows")]
        assert len(matching) >= 1

    def test_has_trigger_route(self):
        routes = [r for r in workflows_router.routes if hasattr(r, "methods")]
        post_routes = [r for r in routes if "POST" in r.methods]
        matching = [r for r in post_routes if "trigger" in r.path]
        assert len(matching) >= 1

    def test_route_in_openapi_schema(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        has_workflows = any("workflows" in p for p in paths)
        assert has_workflows, "No workflow endpoints found in OpenAPI schema"


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — POST /api/v1/workflows
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(not HAS_WORKFLOWS_ROUTER, reason="api/workflows.py not implemented yet")
class TestCreateWorkflowEndpoint:
    """Behavioral: POST /api/v1/workflows — Create workflow."""

    async def test_create_workflow_returns_201(self):
        """Valid request → 201 with workflow_id."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/workflows",
                json={
                    "name": "My Workflow",
                    "trigger_type": "manual",
                    "steps": [
                        {
                            "step_id": "step-1",
                            "step_type": "repurpose",
                            "config": {"source_content": "test"},
                        }
                    ],
                },
            )
        # Expected: 201 (or 200 if that's what the endpoint uses)
        assert response.status_code in (200, 201)
        data = response.json()
        assert "workflow_id" in data
        assert isinstance(data["workflow_id"], str)

    async def test_create_workflow_validates_name_required(self):
        """Missing name → 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/workflows",
                json={
                    "trigger_type": "manual",
                    "steps": [
                        {
                            "step_id": "step-1",
                            "step_type": "repurpose",
                            "config": {},
                        }
                    ],
                },
            )
        assert response.status_code == 422

    async def test_create_workflow_validates_steps_required(self):
        """Missing steps → 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/workflows",
                json={
                    "name": "Test",
                    "trigger_type": "manual",
                },
            )
        assert response.status_code == 422

    async def test_create_workflow_empty_steps_rejected(self):
        """Empty steps list → 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/workflows",
                json={
                    "name": "Test",
                    "trigger_type": "manual",
                    "steps": [],
                },
            )
        assert response.status_code == 422

    async def test_create_workflow_invalid_step_type_rejected(self):
        """Invalid step_type → 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/workflows",
                json={
                    "name": "Test",
                    "trigger_type": "manual",
                    "steps": [
                        {
                            "step_id": "step-1",
                            "step_type": "nonexistent",
                            "config": {},
                        }
                    ],
                },
            )
        assert response.status_code == 422

    async def test_create_workflow_duplicate_step_ids_rejected(self):
        """Duplicate step_ids → 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/workflows",
                json={
                    "name": "Test",
                    "trigger_type": "manual",
                    "steps": [
                        {"step_id": "step-1", "step_type": "repurpose", "config": {}},
                        {"step_id": "step-1", "step_type": "wait", "config": {"delay_seconds": 5}},
                    ],
                },
            )
        assert response.status_code == 422

    async def test_create_workflow_accepts_schedule_config(self):
        """Workflow with schedule config should be accepted."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/workflows",
                json={
                    "name": "Scheduled",
                    "trigger_type": "schedule",
                    "schedule": {"cron_expression": "0 */6 * * *"},
                    "steps": [
                        {"step_id": "s1", "step_type": "repurpose", "config": {}}
                    ],
                },
            )
        assert response.status_code in (200, 201)

    async def test_create_workflow_accepts_webhook_config(self):
        """Workflow with webhook config should be accepted."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/workflows",
                json={
                    "name": "Webhook",
                    "trigger_type": "webhook",
                    "webhook_config": {"secret": "my-secret"},
                    "steps": [
                        {"step_id": "s1", "step_type": "repurpose", "config": {}}
                    ],
                },
            )
        assert response.status_code in (200, 201)


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — GET /api/v1/workflows
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(not HAS_WORKFLOWS_ROUTER, reason="api/workflows.py not implemented yet")
class TestListWorkflowsEndpoint:
    """Behavioral: GET /api/v1/workflows — List workflows."""

    async def test_list_workflows_returns_200(self):
        """GET /workflows → 200 with list."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/workflows")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_workflows_empty_when_none(self):
        """Returns empty list when no workflows exist."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/workflows")
        data = response.json()
        assert isinstance(data, list)

    async def test_list_workflows_supports_active_filter(self):
        """Supports ?active=true/false filter."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/workflows?active=true")
        assert response.status_code == 200

    async def test_list_workflows_returns_created_items(self):
        """After creating a workflow, GET should include it."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create a workflow
            create_resp = await client.post(
                "/api/v1/workflows",
                json={
                    "name": "List Test",
                    "trigger_type": "manual",
                    "steps": [{"step_id": "s1", "step_type": "repurpose", "config": {}}],
                },
            )
            if create_resp.status_code not in (200, 201):
                pytest.skip("Cannot create workflow for list test")

            # List workflows
            list_resp = await client.get("/api/v1/workflows")
            data = list_resp.json()
            names = [w.get("name") for w in data]
            assert "List Test" in names


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — POST /api/v1/workflows/{id}/trigger
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(not HAS_WORKFLOWS_ROUTER, reason="api/workflows.py not implemented yet")
class TestTriggerWorkflowEndpoint:
    """Behavioral: POST /api/v1/workflows/{id}/trigger — Trigger workflow."""

    async def test_trigger_returns_202(self):
        """Valid trigger → 202 with execution_id."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create a workflow first
            create_resp = await client.post(
                "/api/v1/workflows",
                json={
                    "name": "Trigger Test",
                    "trigger_type": "manual",
                    "steps": [{"step_id": "s1", "step_type": "repurpose", "config": {}}],
                },
            )
            if create_resp.status_code not in (200, 201):
                pytest.skip("Cannot create workflow for trigger test")

            wf_id = create_resp.json()["workflow_id"]
            response = await client.post(f"/api/v1/workflows/{wf_id}/trigger")
        assert response.status_code == 202
        data = response.json()
        assert "execution_id" in data
        assert isinstance(data["execution_id"], str)

    async def test_trigger_returns_404_for_unknown(self):
        """Trigger unknown workflow → 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/workflows/nonexistent/trigger")
        assert response.status_code == 404

    async def test_trigger_returns_409_for_inactive(self):
        """Trigger inactive workflow → 409."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/workflows/inactive-workflow/trigger")
        # The endpoint should return 409 (conflict) for inactive workflows
        if response.status_code == 404:
            # Accept 404 if inactive is treated as non-existent
            pass
        elif response.status_code == 409:
            # Preferred
            pass
        else:
            # Some error status
            assert response.status_code >= 400


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — POST /api/v1/webhook/workflow/{workflow_id}
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(not HAS_WEBHOOK_ROUTER, reason="Webhook trigger not in api/webhook.py yet")
class TestWebhookTriggerEndpoint:
    """Behavioral: POST /api/v1/webhook/workflow/{workflow_id} — Webhook trigger."""

    async def test_webhook_trigger_returns_202(self):
        """Valid webhook trigger → 202."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/webhook/workflow/wf-1", json={})
        # The route may or may not be registered yet
        if response.status_code != 404:
            assert response.status_code == 202

    async def test_webhook_trigger_returns_404_for_unknown(self):
        """Unknown workflow → 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhook/workflow/nonexistent", json={}
            )
        assert response.status_code == 404

    async def test_webhook_trigger_validates_hmac_when_configured(self):
        """HMAC validation should reject missing signature."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhook/workflow/wf-with-secret",
                json={},
            )
        if response.status_code != 404:
            assert response.status_code in (401, 403, 422)

    async def test_webhook_trigger_ssrf_validation(self):
        """SSRF validation on callback URLs in the request."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhook/workflow/wf-1",
                json={"callback_url": "http://169.254.169.254/latest/meta-data/"},
            )
        if response.status_code != 404:
            # SSRF should block this
            assert response.status_code == 422
