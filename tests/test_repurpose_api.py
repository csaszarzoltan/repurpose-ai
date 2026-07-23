"""Tests for repurpose API endpoint."""

from httpx import ASGITransport, AsyncClient

from app.api.repurpose import router as repurpose_router
from app.main import app

# ── Interface Tests (must pass immediately) ──────────────────


class TestRepurposeRouterImport:
    """Interface: repurpose router is importable and has expected routes."""

    def test_importable(self):
        assert repurpose_router is not None

    def test_has_post_endpoint(self):
        """Router should have a POST /repurpose route."""
        routes = [r for r in repurpose_router.routes if hasattr(r, "methods")]
        post_routes = [r for r in routes if "POST" in r.methods]
        assert len(post_routes) >= 1

    def test_router_has_prefix(self):
        assert hasattr(repurpose_router, "prefix")
        assert "v1" in repurpose_router.prefix


# ── Behavioral Tests (must fail until implementation) ────────


class TestRepurposeEndpointBehavior:
    """Behavioral: POST /api/v1/repurpose endpoint."""

    def _make_request(self, **overrides):
        """Helper to build a valid repurpose request body."""
        body = {
            "content": {
                "title": "AI in Healthcare",
                "body": "AI is transforming diagnostics.",
                "source_format": "blog_post",
                "tags": ["ai"],
            },
            "target_formats": ["twitter_thread"],
            "brand_voice": "professional",
        }
        body.update(overrides)
        return body

    async def test_post_repurpose_returns_200(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose", json=self._make_request()
            )
        assert response.status_code == 200

    async def test_post_repurpose_returns_repurpose_response(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose", json=self._make_request()
            )
        data = response.json()
        assert "original_id" in data
        assert "repurposed" in data
        assert "warnings" in data
        assert "created_at" in data

    async def test_post_repurpose_populates_repurposed(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose", json=self._make_request()
            )
        data = response.json()
        assert isinstance(data["repurposed"], dict)
        assert len(data["repurposed"]) > 0

    async def test_post_repurpose_multiple_formats(self):
        body = self._make_request()
        body["target_formats"] = ["twitter_thread", "linkedin_post", "newsletter"]
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/repurpose", json=body)
        data = response.json()
        assert len(data["repurposed"]) == 3

    async def test_post_repurpose_with_brand_voice(self):
        body = self._make_request()
        body["brand_voice"] = "casual"
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/repurpose", json=body)
        assert response.status_code == 200

    async def test_post_repurpose_with_custom_instructions(self):
        body = self._make_request()
        body["custom_instructions"] = "Make it under 280 characters"
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/repurpose", json=body)
        assert response.status_code == 200

    async def test_post_repurpose_missing_content_returns_422(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json={"target_formats": ["twitter_thread"]},
            )
        assert response.status_code == 422

    async def test_post_repurpose_missing_target_formats_returns_422(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json={
                    "content": {
                        "title": "T",
                        "body": "B",
                        "source_format": "blog_post",
                    }
                },
            )
        assert response.status_code == 422

    async def test_post_repurpose_empty_body_returns_422(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/repurpose", json={})
        assert response.status_code == 422
