"""Pre-dev tests for PublishPlatform enum and publish dispatch routing.

Verifies:
- PublishPlatform enum includes WORDPRESS and GHOST values
- PublishService dispatch routes WORDPRESS → WordPressPublisher and GHOST → GhostPublisher
"""
from __future__ import annotations

import inspect

import pytest

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.models.publish import PublishPlatform
    HAS_MODELS = True
except (ImportError, ModuleNotFoundError):
    HAS_MODELS = False
    class PublishPlatform:  # type: ignore[no-redef]
        LINKEDIN = "linkedin"
        TWITTER = "twitter"
        MEDIUM = "medium"


try:
    from app.services.publish import PublishService
    from app.services.publishers.wordpress import WordPressPublisher
    from app.services.publishers.ghost import GhostPublisher
    HAS_PUBLISH = True
except (ImportError, ModuleNotFoundError):
    HAS_PUBLISH = False


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — PublishPlatform enum
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_MODELS, reason="models/publish.py not implemented yet")
class TestPublishPlatformEnum:
    """Interface: PublishPlatform enum contains all expected platform values."""

    def test_wordpress_value_exists(self):
        assert hasattr(PublishPlatform, "WORDPRESS")

    def test_ghost_value_exists(self):
        assert hasattr(PublishPlatform, "GHOST")

    def test_wordpress_string_value(self):
        assert PublishPlatform.WORDPRESS == "wordpress"

    def test_ghost_string_value(self):
        assert PublishPlatform.GHOST == "ghost"

    def test_linkedin_still_exists(self):
        assert hasattr(PublishPlatform, "LINKEDIN")
        assert PublishPlatform.LINKEDIN == "linkedin"

    def test_twitter_still_exists(self):
        assert hasattr(PublishPlatform, "TWITTER")
        assert PublishPlatform.TWITTER == "twitter"

    def test_medium_still_exists(self):
        assert hasattr(PublishPlatform, "MEDIUM")
        assert PublishPlatform.MEDIUM == "medium"

    def test_all_expected_members(self):
        """PublishPlatform has all 5 expected members."""
        expected = {"LINKEDIN", "TWITTER", "MEDIUM", "WORDPRESS", "GHOST"}
        actual = {m.name for m in PublishPlatform}
        assert expected == actual

    def test_wordpress_is_publishable(self):
        """WORDPRESS can be used as a PublishPlatform value."""
        platform = PublishPlatform("wordpress")
        assert platform == PublishPlatform.WORDPRESS

    def test_ghost_is_publishable(self):
        """GHOST can be used as a PublishPlatform value."""
        platform = PublishPlatform("ghost")
        assert platform == PublishPlatform.GHOST


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — PublishService accepts WordPress/Ghost publishers
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH, reason="services/publish.py not implemented yet")
class TestPublishServiceConstructor:
    """Interface: PublishService __init__ accepts wordpress and ghost kwargs."""

    def test_init_accepts_wordpress_kwarg(self):
        sig = inspect.signature(PublishService.__init__)
        assert "wordpress" in sig.parameters or any(
            "wordpress" in p.name.lower() for p in sig.parameters.values()
        )

    def test_init_accepts_ghost_kwarg(self):
        sig = inspect.signature(PublishService.__init__)
        assert "ghost" in sig.parameters or any(
            "ghost" in p.name.lower() for p in sig.parameters.values()
        )


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Dispatch routing
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH, reason="services/publish.py not implemented yet")
class TestPublishDispatchWordPress:
    """Behavioral: WORDPRESS platform routes to WordPressPublisher."""

    @pytest.fixture
    def credentials(self):
        from app.models.publish import PlatformCredentials
        return PlatformCredentials(
            platform=PublishPlatform.WORDPRESS,
            access_token="wp_token",
        )

    async def test_wordpress_dispatch_creates_post(self, credentials):
        """WORDPRESS request routes to WordPressPublisher.create_post."""
        import respx

        service = PublishService()
        from app.models.publish import PublishRequest, PublishResponse

        request = PublishRequest(
            platform=PublishPlatform.WORDPRESS,
            content="WordPress content",
            title="WP Title",
        )
        with respx.mock:
            respx.post("https://example.wordpress.com/wp-json/wp/v2/posts").respond(
                status_code=201,
                json={"id": 100, "status": "draft"},
            )
            response = await service.publish(request, credentials)
        assert isinstance(response, PublishResponse)
        assert response.platform == PublishPlatform.WORDPRESS


@pytest.mark.xfail(not HAS_PUBLISH, reason="services/publish.py not implemented yet")
class TestPublishDispatchGhost:
    """Behavioral: GHOST platform routes to GhostPublisher."""

    @pytest.fixture
    def credentials(self):
        from app.models.publish import PlatformCredentials
        return PlatformCredentials(
            platform=PublishPlatform.GHOST,
            access_token="ghost_api_key:secret",
        )

    async def test_ghost_dispatch_creates_post(self, credentials):
        """GHOST request routes to GhostPublisher.create_post."""
        import respx

        service = PublishService()
        from app.models.publish import PublishRequest, PublishResponse

        request = PublishRequest(
            platform=PublishPlatform.GHOST,
            content="Ghost content",
            title="Ghost Title",
        )
        with respx.mock:
            respx.post("https://ghost.example.com/ghost/api/admin/posts/").respond(
                status_code=201,
                json={"posts": [{"id": "200", "status": "draft"}]},
            )
            response = await service.publish(request, credentials)
        assert isinstance(response, PublishResponse)
        assert response.platform == PublishPlatform.GHOST


@pytest.mark.xfail(not HAS_PUBLISH, reason="services/publish.py not implemented yet")
class TestPublishExtractPostId:
    """Behavioral: _extract_post_id handles WORDPRESS and GHOST."""

    def test_extract_wordpress_post_id(self):
        result = PublishService._extract_post_id(
            PublishPlatform.WORDPRESS, {"id": 42, "status": "draft"}
        )
        assert result == 42 or result == "42"

    def test_extract_ghost_post_id(self):
        result = PublishService._extract_post_id(
            PublishPlatform.GHOST, {"posts": [{"id": "55"}]}
        )
        assert result == "55"
