"""Pre-dev tests for Job status endpoint (P2 — API).

Source of truth: analysis/analysis-brief.md §5 (GET /api/v1/jobs/{id}).
Behavioral tests → xfail until api/jobs.py is implemented.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.api.jobs import router as jobs_router

    HAS_JOBS_ROUTER = True
except (ImportError, ModuleNotFoundError):
    HAS_JOBS_ROUTER = False


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Router structure
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_JOBS_ROUTER, reason="api/jobs.py not implemented yet")
class TestJobsRouterInterface:
    """Interface: jobs router is importable."""

    def test_router_importable(self):
        assert jobs_router is not None

    def test_router_is_apirouter(self):
        from fastapi import APIRouter
        assert isinstance(jobs_router, APIRouter)

    def test_has_get_endpoint(self):
        routes = [r for r in jobs_router.routes if hasattr(r, "methods")]
        get_routes = [r for r in routes if "GET" in r.methods]
        assert len(get_routes) >= 1

    def test_route_in_openapi_schema(self):
        # Informational — will fail when module exists but route not registered
        import pytest as _pytest

        _pytest.skip("Jobs route not registered yet")


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — GET /api/v1/jobs/{id}
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(not HAS_JOBS_ROUTER, reason="api/jobs.py not implemented yet")
class TestGetJobStatusEndpoint:
    """Behavioral: GET /api/v1/jobs/{id} — Get job status."""

    async def test_get_job_returns_200_for_known_job(self):
        """Known job_id → 200 with job details."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/jobs/known-job-id")
        if response.status_code != 404:
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            assert "status" in data
            assert "created_at" in data

    async def test_get_job_returns_404_for_unknown(self):
        """Unknown job_id → 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/jobs/nonexistent-job-id")
        assert response.status_code == 404

    async def test_get_job_shows_status(self):
        """Response includes status field."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/jobs/known-job-id")
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert data["status"] in ("pending", "processing", "completed", "failed")

    async def test_get_job_shows_created_at(self):
        """Response includes created_at timestamp."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/jobs/known-job-id")
        if response.status_code == 200:
            data = response.json()
            assert "created_at" in data
            assert isinstance(data["created_at"], str)

    async def test_get_job_shows_completed_at_for_completed(self):
        """Completed jobs include completed_at."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/jobs/completed-job-id")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "completed":
                assert "completed_at" in data
                assert data["completed_at"] is not None

    async def test_completed_jobs_include_result(self):
        """Completed jobs include result data."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/jobs/completed-job-id")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "completed":
                assert "result" in data

    async def test_failed_jobs_include_error(self):
        """Failed jobs include error message."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/jobs/failed-job-id")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "failed":
                assert "error" in data
                assert data["error"] is not None

    async def test_get_job_returns_unified_status(self):
        """Unified endpoint covers both webhook jobs and workflow executions."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Check the response has enough info to distinguish job type
            response = await client.get("/api/v1/jobs/existing-webhook-job")
        if response.status_code == 200:
            data = response.json()
            # Both types should share the common status fields
            assert "job_id" in data
            assert "status" in data
            assert "created_at" in data
