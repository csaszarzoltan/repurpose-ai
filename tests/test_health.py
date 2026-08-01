"""Tests for health check endpoint — expanded coverage."""

from httpx import ASGITransport, AsyncClient

from app.main import app, create_app

# ── Interface Tests (must pass immediately) ──────────────────


class TestAppFactory:
    """Interface: app factory and health endpoint exist."""

    def test_create_app_returns_fastapi(self):
        application = create_app()
        from fastapi import FastAPI
        assert isinstance(application, FastAPI)

    def test_app_has_title(self):
        application = create_app()
        assert application.title == "RepurposeAI"

    def test_app_has_version(self):
        application = create_app()
        assert application.version == "0.8.0"

    def test_app_has_docs_url(self):
        application = create_app()
        assert application.docs_url == "/docs"

    def test_app_has_redoc_url(self):
        application = create_app()
        assert application.redoc_url == "/redoc"

    def test_module_level_app_exists(self):
        from fastapi import FastAPI

        from app.main import app as module_app
        assert isinstance(module_app, FastAPI)


class TestHealthEndpointInterface:
    """Interface: /health endpoint is registered."""

    def test_health_route_exists(self):
        application = create_app()
        schema = application.openapi()
        paths = schema.get("paths", {})
        assert "/health" in paths


# ── Behavioral Tests (must fail until implementation) ────────


class TestHealthEndpointBehavior:
    """Behavioral: /health endpoint returns correct response."""

    async def test_health_returns_200(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_returns_ok_status(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    async def test_health_returns_json(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")
        assert response.headers["content-type"] == "application/json"

    async def test_health_is_get_only(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/health")
        assert response.status_code == 405

    async def test_health_no_auth_required(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_response_has_status_key(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")
        data = response.json()
        assert "status" in data
        assert isinstance(data["status"], str)


class TestCORSBehavior:
    """Behavioral: CORS middleware is configured."""

    async def test_cors_allows_origin(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.options(
                "/health",
                headers={
                    "Origin": "http://example.com",
                    "Access-Control-Request-Method": "GET",
                },
            )
        assert response.status_code in (200, 405)

    async def test_cors_headers_present(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/health",
                headers={"Origin": "http://example.com"},
            )
        assert "access-control-allow-origin" in response.headers
