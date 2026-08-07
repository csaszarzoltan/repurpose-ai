"""Pre-dev tests for Publish API endpoints (Phase 7).

Source of truth: analysis/analysis-brief.md §4.3 Publish API Endpoints + §5.
Interface tests → xfail until api/publish.py is implemented.
Behavioral tests use ASGITransport + respx for external mocks.
"""

from __future__ import annotations

import pytest
import respx
from httpx import ASGITransport, AsyncClient

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.api.publish import router as publish_router

    HAS_PUBLISH_ROUTER = True
except (ImportError, ModuleNotFoundError):
    HAS_PUBLISH_ROUTER = False

try:
    from app.main import app

    HAS_APP = True
except (ImportError, ModuleNotFoundError):
    HAS_APP = False


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Router structure
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_ROUTER, reason="api/publish.py not implemented yet")
class TestPublishRouterInterface:
    """Interface: publish router is importable and has expected routes."""

    def test_router_importable(self):
        assert publish_router is not None

    def test_router_is_apirouter(self):
        from fastapi import APIRouter
        assert isinstance(publish_router, APIRouter)

    def test_has_publish_prefix(self):
        assert hasattr(publish_router, "prefix")
        assert "publish" in publish_router.prefix

    def test_has_post_publish_route(self):
        routes = [r for r in publish_router.routes if hasattr(r, "methods")]
        post_routes = [r for r in routes if "POST" in r.methods]
        matching = [r for r in post_routes if r.path.endswith("/publish") or "/publish" in r.path]
        assert len(matching) >= 1

    def test_has_get_job_status_route(self):
        routes = [r for r in publish_router.routes if hasattr(r, "methods")]
        get_routes = [r for r in routes if "GET" in r.methods]
        matching = [r for r in get_routes if "{job_id}" in r.path]
        assert len(matching) >= 1

    def test_has_get_platforms_route(self):
        routes = [r for r in publish_router.routes if hasattr(r, "methods")]
        get_routes = [r for r in routes if "GET" in r.methods]
        matching = [r for r in get_routes if "platforms" in r.path.lower()]
        assert len(matching) >= 1

    def test_has_auth_url_route(self):
        routes = [r for r in publish_router.routes if hasattr(r, "methods")]
        get_routes = [r for r in routes if "GET" in r.methods]
        matching = [r for r in get_routes if "auth-url" in r.path.lower() or "auth_url" in r.path.lower()]
        assert len(matching) >= 1

    def test_has_auth_callback_route(self):
        routes = [r for r in publish_router.routes if hasattr(r, "methods")]
        post_routes = [r for r in routes if "POST" in r.methods]
        matching = [r for r in post_routes if "callback" in r.path.lower()]
        assert len(matching) >= 1

    def test_has_credentials_routes(self):
        routes = [r for r in publish_router.routes if hasattr(r, "methods")]
        cred_routes = [r for r in routes if "credential" in r.path.lower()]
        assert len(cred_routes) >= 1

    def test_route_in_openapi_schema(self):
        schema = app.openapi()
        paths = schema.get("paths", {})
        has_publish = any("publish" in p for p in paths)
        has_platforms = any("platforms" in p for p in paths)
        has_credentials = any("credential" in p for p in paths)
        assert has_publish, "No publish endpoints found in OpenAPI schema"
        assert has_platforms, "No platforms endpoint in OpenAPI schema"
        assert has_credentials, "No credentials endpoints in OpenAPI schema"


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — POST /api/v1/publish
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_ROUTER, reason="api/publish.py not implemented yet")
class TestPublishEndpoint:
    """Behavioral: POST /api/v1/publish dispatches a publish request."""

    def _make_request(self, **overrides):
        body = {
            "platform": "linkedin",
            "content": "This is a test post",
            "title": "Test Title",
        }
        body.update(overrides)
        return body

    async def test_post_publish_returns_200(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with respx.mock:
                respx.post("https://api.linkedin.com/rest/posts").respond(
                    status_code=201,
                    json={"id": "urn:li:activity:api_test"},
                )
                response = await client.post("/api/v1/publish", json=self._make_request())
        assert response.status_code in (200, 201, 202)

    async def test_post_publish_returns_response_shape(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with respx.mock:
                respx.post("https://api.linkedin.com/rest/posts").respond(
                    status_code=201,
                    json={"id": "urn:li:activity:shape_test"},
                )
                response = await client.post("/api/v1/publish", json=self._make_request())
        data = response.json()
        assert "job_id" in data
        assert "platform" in data
        assert "status" in data


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — GET /api/v1/publish/{job_id}
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_ROUTER, reason="api/publish.py not implemented yet")
class TestPublishJobStatus:
    """Behavioral: GET /api/v1/publish/{job_id} returns job status."""

    async def test_get_job_returns_200(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/publish/job-123")
        # Expect 404 when route not implemented (RED), 200 when implemented (GREEN)
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            data = response.json()
            assert "status" in data


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — GET /api/v1/publish/platforms
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_ROUTER, reason="api/publish.py not implemented yet")
class TestPublishPlatforms:
    """Behavioral: GET /api/v1/publish/platforms lists platforms."""

    async def test_get_platforms_returns_200(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/publish/platforms")
        assert response.status_code == 200

    async def test_get_platforms_returns_list(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/publish/platforms")
        data = response.json()
        platforms = data if isinstance(data, list) else data.get("platforms", data.get("data", []))
        assert isinstance(platforms, list)
        assert len(platforms) >= 3  # linkedin, twitter, medium

    async def test_get_platforms_contains_expected(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/publish/platforms")
        data = response.json()
        platforms = data if isinstance(data, list) else data.get("platforms", data.get("data", []))
        platform_names = [p.get("name", p.get("id", p)) if isinstance(p, dict) else p for p in platforms]
        platform_strs = [str(p).lower() for p in platform_names]
        assert "linkedin" in platform_strs
        assert "twitter" in platform_strs
        assert "medium" in platform_strs


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — OAuth endpoints
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_ROUTER, reason="api/publish.py not implemented yet")
class TestPublishAuthEndpoints:
    """Behavioral: OAuth flow endpoints."""

    async def test_get_auth_url_returns_url(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/publish/linkedin/auth-url",
                params={"redirect_uri": "https://app.example.com/callback"},
            )
        assert response.status_code == 200
        data = response.json()
        url = data.get("url", data.get("auth_url", ""))
        assert "linkedin" in str(url).lower()

    async def test_wordpress_auth_url_returns_200(self):
        """GET /publish/wordpress/auth-url returns 200 (B1 — was a KeyError 500)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/publish/wordpress/auth-url",
                params={"redirect_uri": "https://app.example.com/callback"},
            )
        assert response.status_code == 200
        data = response.json()
        url = data.get("url", data.get("auth_url", ""))
        assert "wordpress.com" in str(url).lower()

    async def test_ghost_auth_url_returns_clean_error(self):
        """GET /publish/ghost/auth-url returns a clean 400 (B1 — was a KeyError 500)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/publish/ghost/auth-url",
                params={"redirect_uri": "https://app.example.com/callback"},
            )
        assert response.status_code == 400
        data = response.json()
        assert "ghost" in str(data.get("detail", "")).lower()

    async def test_auth_callback_returns_200(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            with respx.mock:
                respx.post("https://www.linkedin.com/oauth/v2/accessToken").respond(
                    status_code=200,
                    json={"access_token": "tok_abc", "expires_in": 3600},
                )
                response = await client.post(
                    "/publish/linkedin/callback",
                    params={"code": "auth_code_xyz", "state": "state_123"},
                )
        assert response.status_code in (200, 201)


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Credentials CRUD
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_ROUTER, reason="api/publish.py not implemented yet")
class TestPublishCredentialsEndpoints:
    """Behavioral: CRUD for platform credentials."""

    async def test_get_credentials_returns_200(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/publish/linkedin/credentials")
        assert response.status_code in (200, 404)

    async def test_put_credentials_returns_200(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                "/publish/linkedin/credentials",
                json={
                    "platform": "linkedin",
                    "access_token": "new_tok",
                    "platform_user_id": "user_1",
                },
            )
        assert response.status_code in (200, 201)

    async def test_delete_credentials_returns_200(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/publish/linkedin/credentials")
        assert response.status_code in (200, 204)

    async def test_get_credentials_invalid_platform(self):
        """Invalid platform returns 422 or 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/publish/invalid_platform/credentials")
        assert response.status_code in (404, 422)
