"""Pre-dev tests for publish dispatch function (services/publish.py).

Verifies that the PublishService._publish_to_platform method correctly routes
WORDPRESS and GHOST platform values to their respective publisher implementations.
"""
from __future__ import annotations

import inspect

import pytest

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.models.publish import PlatformCredentials, PublishPlatform, PublishRequest
    from app.services.publish import PublishService
    from app.services.publishers.wordpress import WordPressPublisher
    from app.services.publishers.ghost import GhostPublisher
    HAS_DISPATCH = True
except (ImportError, ModuleNotFoundError):
    HAS_DISPATCH = False


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Dispatch method exists
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_DISPATCH, reason="services/publish.py not implemented yet")
class TestDispatchInterface:
    """Interface: PublishService._publish_to_platform exists and is async."""

    def test_has_publish_to_platform(self):
        assert hasattr(PublishService, "_publish_to_platform")

    def test_publish_to_platform_is_async(self):
        assert inspect.iscoroutinefunction(PublishService._publish_to_platform)

    def test_has_extract_post_id(self):
        assert hasattr(PublishService, "_extract_post_id")

    def test_extract_post_id_is_static(self):
        import inspect
        assert isinstance(
            inspect.getattr_static(PublishService, "_extract_post_id"),
            staticmethod,
        )


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Dispatch routes correctly
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_DISPATCH, reason="services/publish.py not implemented yet")
class TestDispatchWordpressRoute:
    """Behavioral: WORDPRESS request creates WordPressPublisher if needed."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.WORDPRESS,
            access_token="wp_test_token",
        )

    async def test_wordpress_dispatches_to_wordpress_publisher(self, credentials):
        """_publish_to_platform calls WordPressPublisher for WORDPRESS."""
        import respx

        service = PublishService()
        request = PublishRequest(
            platform=PublishPlatform.WORDPRESS,
            content="WP dispatch test",
            title="Dispatch WP",
        )
        with respx.mock:
            respx.post("https://example.wordpress.com/wp-json/wp/v2/posts").respond(
                status_code=201,
                json={"id": 300, "status": "draft"},
            )
            result = await service._publish_to_platform(request, credentials)
        assert result["id"] == 300

    async def test_wordpress_publish_instantiates_publisher(self, credentials):
        """PublishService auto-creates WordPressPublisher when not injected."""
        service = PublishService()
        assert service._wordpress is None or isinstance(service._wordpress, WordPressPublisher)


@pytest.mark.xfail(not HAS_DISPATCH, reason="services/publish.py not implemented yet")
class TestDispatchGhostRoute:
    """Behavioral: GHOST request creates GhostPublisher if needed."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.GHOST,
            access_token="ghost_api_key:secret",
        )

    async def test_ghost_dispatches_to_ghost_publisher(self, credentials):
        """_publish_to_platform calls GhostPublisher for GHOST."""
        import respx

        service = PublishService()
        request = PublishRequest(
            platform=PublishPlatform.GHOST,
            content="Ghost dispatch test",
            title="Dispatch Ghost",
        )
        with respx.mock:
            respx.post("https://ghost.example.com/ghost/api/admin/posts/").respond(
                status_code=201,
                json={"posts": [{"id": "400", "status": "draft"}]},
            )
            result = await service._publish_to_platform(request, credentials)
        assert "posts" in result
        assert result["posts"][0]["id"] == "400"

    async def test_ghost_publish_instantiates_publisher(self, credentials):
        """PublishService auto-creates GhostPublisher when not injected."""
        service = PublishService()
        assert service._ghost is None or isinstance(service._ghost, GhostPublisher)


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Extract post ID
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_DISPATCH, reason="services/publish.py not implemented yet")
class TestExtractPostId:
    """Behavioral: _extract_post_id handles new platform types."""

    def test_wordpress_id_extraction(self):
        result = PublishService._extract_post_id(
            PublishPlatform.WORDPRESS, {"id": 42, "link": "https://example.com/?p=42"}
        )
        assert result == 42

    def test_ghost_id_extraction(self):
        result = PublishService._extract_post_id(
            PublishPlatform.GHOST, {"posts": [{"id": "99"}]}
        )
        assert result == "99"

    def test_unknown_platform_returns_none(self):
        """Unknown platform returns None for post ID."""
        # This tests that the function gracefully handles unexpected platforms
        result = PublishService._extract_post_id(
            "unknown_platform", {"id": "x"}
        )
        assert result is None
