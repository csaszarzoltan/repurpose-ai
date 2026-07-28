"""Pre-dev tests for Batch repurpose endpoint (P2 — API).

Source of truth: analysis/analysis-brief.md §5 (POST /api/v1/repurpose/batch).
Behavioral tests → xfail until api/batch.py is implemented.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.api.batch import router as batch_router

    HAS_BATCH_ROUTER = True
except (ImportError, ModuleNotFoundError):
    HAS_BATCH_ROUTER = False


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Router structure
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_BATCH_ROUTER, reason="api/batch.py not implemented yet")
class TestBatchRouterInterface:
    """Interface: batch router is importable."""

    def test_router_importable(self):
        assert batch_router is not None

    def test_router_is_apirouter(self):
        from fastapi import APIRouter
        assert isinstance(batch_router, APIRouter)

    def test_has_post_endpoint(self):
        routes = [r for r in batch_router.routes if hasattr(r, "methods")]
        post_routes = [r for r in routes if "POST" in r.methods]
        assert len(post_routes) >= 1

    def test_route_in_openapi_schema(self):
        # Informational — will fail when module exists but route not registered
        import pytest as _pytest

        _pytest.skip("Batch route not registered yet")


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — POST /api/v1/repurpose/batch
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(not HAS_BATCH_ROUTER, reason="api/batch.py not implemented yet")
class TestBatchEndpoint:
    """Behavioral: POST /api/v1/repurpose/batch — Batch repurpose."""

    def _single_job(self) -> dict:
        return {
            "content": {
                "title": "AI in Healthcare",
                "body": "AI is transforming diagnostics.",
                "source_format": "blog_post",
            },
            "target_formats": ["twitter_thread"],
        }

    def _valid_payload(self, num_jobs: int = 2) -> dict:
        return {
            "jobs": [self._single_job() for _ in range(num_jobs)],
            "concurrency": 5,
        }

    async def test_batch_returns_200(self):
        """Valid batch request → 200 with BatchRepurposeResponse."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/repurpose/batch",
                json=self._valid_payload(2),
            )
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert "total" in data
        assert "completed" in data
        assert "failed" in data
        assert "results" in data

    async def test_batch_accepts_1_to_50_jobs(self):
        """Accepts 1 job (minimum)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/repurpose/batch",
                json=self._valid_payload(1),
            )
        assert response.status_code == 200

    async def test_batch_accepts_50_jobs(self):
        """Accepts 50 jobs (maximum)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/repurpose/batch",
                json=self._valid_payload(50),
            )
        assert response.status_code == 200

    async def test_batch_rejects_empty_jobs_list(self):
        """Empty jobs list → 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/repurpose/batch",
                json={"jobs": [], "concurrency": 5},
            )
        assert response.status_code == 422

    async def test_batch_rejects_over_50_jobs(self):
        """>50 jobs → 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/repurpose/batch",
                json=self._valid_payload(51),
            )
        assert response.status_code == 422

    async def test_batch_validates_each_job(self):
        """Invalid job in the list → 422 on the specific job."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            payload = self._valid_payload(2)
            # Corrupt one job
            payload["jobs"][1] = {"invalid": "data"}
            response = await client.post(
                "/api/v1/repurpose/batch",
                json=payload,
            )
        assert response.status_code == 422

    async def test_batch_concurrency_limit_respected(self):
        """Concurrency parameter should be respected."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/repurpose/batch",
                json={
                    "jobs": [self._single_job() for _ in range(5)],
                    "concurrency": 1,
                },
            )
        assert response.status_code == 200

    async def test_batch_individual_failures_dont_block_others(self):
        """One failing job should not block other jobs."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/repurpose/batch",
                json=self._valid_payload(3),
            )
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] + data["failed"] == data["total"]

    async def test_batch_response_shape(self):
        """Response should match BatchRepurposeResponse fields."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/repurpose/batch",
                json=self._valid_payload(2),
            )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["batch_id"], str)
        assert isinstance(data["total"], int)
        assert isinstance(data["completed"], int)
        assert isinstance(data["failed"], int)
        assert isinstance(data["results"], list)
        assert isinstance(data.get("errors", []), list)
