"""Tests for formats API endpoints."""

from httpx import ASGITransport, AsyncClient
import pytest

from app.main import app
from app.models.content import ContentFormat, FormatInfo
from app.api.formats import router as formats_router


# ── Interface Tests (must pass immediately) ──────────────────


class TestFormatsRouterImport:
    """Interface: formats router is importable and has expected routes."""

    def test_importable(self):
        assert formats_router is not None

    def test_has_get_list_endpoint(self):
        """Router should have a GET /formats route."""
        routes = [r for r in formats_router.routes if hasattr(r, "methods")]
        get_routes = [r for r in routes if "GET" in r.methods]
        assert len(get_routes) >= 1

    def test_has_get_detail_endpoint(self):
        """Router should have a GET /formats/{format_id} route."""
        routes = [r for r in formats_router.routes if hasattr(r, "path")]
        detail_routes = [r for r in routes if "{format_id}" in getattr(r, "path", "")]
        assert len(detail_routes) >= 1

    def test_router_has_prefix(self):
        assert hasattr(formats_router, "prefix")
        assert "v1" in formats_router.prefix


# ── Behavioral Tests (must fail until implementation) ────────


class TestFormatsListBehavior:
    """Behavioral: GET /api/v1/formats returns all formats."""

    async def test_list_formats_returns_200(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/formats")
        assert response.status_code == 200

    async def test_list_formats_returns_list(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/formats")
        data = response.json()
        assert isinstance(data, list)

    async def test_list_formats_has_all_formats(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/formats")
        data = response.json()
        format_ids = [f["format_id"] for f in data]
        for fmt in ContentFormat:
            assert fmt.value in format_ids

    async def test_list_formats_has_required_fields(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/formats")
        data = response.json()
        for item in data:
            assert "format_id" in item
            assert "name" in item
            assert "description" in item
            assert "max_length" in item
            assert "supports_images" in item
            assert "supports_links" in item


class TestFormatsDetailBehavior:
    """Behavioral: GET /api/v1/formats/{format_id} returns one format."""

    async def test_get_format_returns_200(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/formats/blog_post")
        assert response.status_code == 200

    async def test_get_format_returns_correct_format(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/formats/twitter_thread")
        data = response.json()
        assert data["format_id"] == "twitter_thread"
        assert data["name"] == "Twitter Thread"

    async def test_get_format_not_found(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/formats/nonexistent")
        assert response.status_code == 404

    async def test_get_format_has_max_length(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/formats/blog_post")
        data = response.json()
        assert isinstance(data["max_length"], int)
        assert data["max_length"] > 0

    async def test_get_format_supports_images_field(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/formats/linkedin_post")
        data = response.json()
        assert isinstance(data["supports_images"], bool)
