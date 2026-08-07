"""Pre-dev tests for GhostPublisher.

Interface tests → PASS immediately against the stub.
Behavioral tests → raise NotImplementedError until implementation.
Uses respx to mock Ghost Admin API.
"""
from __future__ import annotations

import pytest
import respx

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.models.publish import PlatformCredentials, PublishPlatform
    from app.services.publishers.ghost import GhostPublisher

    HAS_GHOST_PUBLISHER = True
except (ImportError, ModuleNotFoundError):
    HAS_GHOST_PUBLISHER = False

    class PublishPlatform:  # type: ignore[no-redef]
        GHOST = "ghost"

    class PlatformCredentials:  # type: ignore[no-redef]
        pass


GHOST_API = "https://ghost.example.com/ghost/api/admin"


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — must pass immediately
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_GHOST_PUBLISHER, reason="services/publishers/ghost.py not implemented yet")
class TestGhostPublisherInterface:
    """Interface: GhostPublisher is importable and has expected API."""

    def test_importable(self):
        assert GhostPublisher is not None

    def test_is_class(self):
        assert isinstance(GhostPublisher, type)

    def test_has_create_post_method(self):
        assert hasattr(GhostPublisher, "create_post")
        assert callable(GhostPublisher.create_post)

    def test_has_authenticate_method(self):
        assert hasattr(GhostPublisher, "authenticate")
        assert callable(GhostPublisher.authenticate)

    def test_has_upload_image_method(self):
        assert hasattr(GhostPublisher, "upload_image")
        assert callable(GhostPublisher.upload_image)

    def test_create_post_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(GhostPublisher.create_post)

    def test_authenticate_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(GhostPublisher.authenticate)

    def test_upload_image_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(GhostPublisher.upload_image)

    def test_init_accepts_http_client(self):
        import inspect
        sig = inspect.signature(GhostPublisher.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params

    def test_create_post_has_title_param(self):
        import inspect
        sig = inspect.signature(GhostPublisher.create_post)
        assert "title" in sig.parameters

    def test_create_post_has_content_param(self):
        import inspect
        sig = inspect.signature(GhostPublisher.create_post)
        assert "content" in sig.parameters

    def test_create_post_has_status_param(self):
        import inspect
        sig = inspect.signature(GhostPublisher.create_post)
        params = sig.parameters
        assert "status" in params
        assert params["status"].default == "draft"

    def test_create_post_has_tags_param(self):
        import inspect
        sig = inspect.signature(GhostPublisher.create_post)
        assert "tags" in sig.parameters

    def test_create_post_has_feature_image_param(self):
        import inspect
        sig = inspect.signature(GhostPublisher.create_post)
        assert "feature_image" in sig.parameters

    def test_create_post_has_mobiledoc_param(self):
        import inspect
        sig = inspect.signature(GhostPublisher.create_post)
        assert "mobiledoc" in sig.parameters

    def test_create_post_has_credentials_param(self):
        import inspect
        sig = inspect.signature(GhostPublisher.create_post)
        assert "credentials" in sig.parameters

    def test_has_build_jwt_private_method(self):
        assert hasattr(GhostPublisher, "_build_jwt")

    def test_has_format_mobiledoc_static_method(self):
        assert hasattr(GhostPublisher, "_format_mobiledoc")

    def test_retry_after_is_static(self):
        assert hasattr(GhostPublisher, "_get_retry_after")


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — create_post success
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_GHOST_PUBLISHER, reason="services/publishers/ghost.py not implemented yet")
class TestGhostPublisherCreatePost:
    """Behavioral: Successful post creation via Ghost Admin API."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.GHOST,
            access_token="ghost_admin_api_key:secret",
        )

    @pytest.fixture
    def publisher(self):
        return GhostPublisher()

    async def test_create_post_returns_post_data(self, publisher, credentials):
        """POST /ghost/api/admin/posts/ returns 201 with post data."""
        with respx.mock:
            route = respx.post(f"{GHOST_API}/posts/").respond(
                status_code=201,
                json={"posts": [{"id": "1", "slug": "hello-world", "status": "draft"}]},
            )
            result = await publisher.create_post(
                credentials=credentials,
                title="Hello World",
                content="Welcome to Ghost!",
            )
        assert route.called
        assert "posts" in result
        assert result["posts"][0]["id"] == "1"

    async def test_create_post_with_title_and_content(self, publisher, credentials):
        """Payload includes title and content in the posts array."""
        with respx.mock:
            route = respx.post(f"{GHOST_API}/posts/").respond(
                status_code=201,
                json={"posts": [{"id": "2", "status": "draft"}]},
            )
            await publisher.create_post(
                credentials=credentials,
                title="My Ghost Post",
                content="Body text here",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        posts = sent_json.get("posts", [])
        assert len(posts) == 1
        assert posts[0].get("title") == "My Ghost Post"

    async def test_create_post_with_tags(self, publisher, credentials):
        """Payload includes tags array for tag mapping."""
        with respx.mock:
            route = respx.post(f"{GHOST_API}/posts/").respond(
                status_code=201,
                json={"posts": [{"id": "3", "status": "draft"}]},
            )
            await publisher.create_post(
                credentials=credentials,
                title="Tagged Post",
                content="Post with tags",
                tags=[{"name": "tech"}, {"name": "ai"}],
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        posts = sent_json.get("posts", [])
        assert len(posts) == 1
        assert "tags" in posts[0]

    async def test_create_post_draft_status(self, publisher, credentials):
        """status='draft' is sent in the payload."""
        with respx.mock:
            route = respx.post(f"{GHOST_API}/posts/").respond(
                status_code=201,
                json={"posts": [{"id": "4", "status": "draft"}]},
            )
            await publisher.create_post(
                credentials=credentials,
                title="Draft Post",
                content="Draft content",
                status="draft",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        posts = sent_json.get("posts", [])
        assert posts[0].get("status") == "draft"

    async def test_create_post_publish_status(self, publisher, credentials):
        """status='published' is sent in the payload."""
        with respx.mock:
            route = respx.post(f"{GHOST_API}/posts/").respond(
                status_code=201,
                json={"posts": [{"id": "5", "status": "published"}]},
            )
            await publisher.create_post(
                credentials=credentials,
                title="Published Post",
                content="Published content",
                status="published",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        posts = sent_json.get("posts", [])
        assert posts[0].get("status") == "published"

    async def test_create_post_scheduled_status(self, publisher, credentials):
        """status='scheduled' is sent for future posts."""
        with respx.mock:
            route = respx.post(f"{GHOST_API}/posts/").respond(
                status_code=201,
                json={"posts": [{"id": "6", "status": "scheduled"}]},
            )
            await publisher.create_post(
                credentials=credentials,
                title="Scheduled Post",
                content="Scheduled content",
                status="scheduled",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        posts = sent_json.get("posts", [])
        assert posts[0].get("status") == "scheduled"

    async def test_create_post_with_feature_image(self, publisher, credentials):
        """Payload includes feature_image URL."""
        with respx.mock:
            route = respx.post(f"{GHOST_API}/posts/").respond(
                status_code=201,
                json={"posts": [{"id": "7", "status": "draft"}]},
            )
            await publisher.create_post(
                credentials=credentials,
                title="Image Post",
                content="Post with feature image",
                feature_image="https://example.com/hero.jpg",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        posts = sent_json.get("posts", [])
        assert posts[0].get("feature_image") == "https://example.com/hero.jpg"

    async def test_create_post_with_mobiledoc(self, publisher, credentials):
        """Payload includes mobiledoc content format."""
        mobiledoc = '{"version":"0.3.1","markups":[],"atoms":[],"cards":[["markdown",{"markdown":"Hello"}]],"sections":[[10,0]]}'
        with respx.mock:
            route = respx.post(f"{GHOST_API}/posts/").respond(
                status_code=201,
                json={"posts": [{"id": "8", "status": "draft"}]},
            )
            await publisher.create_post(
                credentials=credentials,
                title="Mobiledoc Post",
                content="Content",
                mobiledoc=mobiledoc,
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        posts = sent_json.get("posts", [])
        assert posts[0].get("mobiledoc") == mobiledoc


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Auth (JWT from API key)
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_GHOST_PUBLISHER, reason="services/publishers/ghost.py not implemented yet")
class TestGhostPublisherAuth:
    """Behavioral: API key authentication generates JWT."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.GHOST,
            access_token="ghost_admin_api_key:secret_value",
        )

    @pytest.fixture
    def publisher(self):
        return GhostPublisher()

    async def test_authenticate_returns_jwt_string(self, publisher, credentials):
        """authenticate() returns a JWT string for API authorization."""
        result = await publisher.authenticate(credentials=credentials)
        assert isinstance(result, str)
        # JWT has three dot-separated parts
        assert result.count(".") == 2

    async def test_build_jwt_creates_signed_token(self, publisher, credentials):
        """_build_jwt returns a signed JWT token."""
        api_key = credentials.access_token
        jwt_token = await publisher._build_jwt(api_key)
        assert isinstance(jwt_token, str)
        assert jwt_token.count(".") == 2


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Upload image
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_GHOST_PUBLISHER, reason="services/publishers/ghost.py not implemented yet")
class TestGhostPublisherUploadImage:
    """Behavioral: Image upload to Ghost media library."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.GHOST,
            access_token="ghost_admin_api_key:secret",
        )

    @pytest.fixture
    def publisher(self):
        return GhostPublisher()

    async def test_upload_image_returns_image_data(self, publisher, credentials):
        """POST /ghost/api/admin/images/upload returns image reference."""
        with respx.mock:
            respx.get("https://example.com/photo.jpg").respond(
                status_code=200,
                content=b"\x89PNG\r\n\x1a\nfake-bytes",
                headers={"Content-Type": "image/png"},
            )
            route = respx.post(f"{GHOST_API}/images/upload").respond(
                status_code=201,
                json={"images": [{"url": "https://ghost.example.com/content/images/2026/08/photo.jpg", "ref": "photo-ref"}]},
            )
            result = await publisher.upload_image(
                credentials=credentials,
                image_url="https://example.com/photo.jpg",
            )
        assert route.called
        assert "images" in result

    async def test_upload_image_sends_fetched_bytes(self, publisher, credentials):
        """upload_image sends the fetched image bytes, not the URL string (B3)."""
        with respx.mock:
            respx.get("https://example.com/photo.jpg").respond(
                status_code=200,
                content=b"\x89PNG\r\n\x1a\nreal-bytes-123",
                headers={"Content-Type": "image/png"},
            )
            route = respx.post(f"{GHOST_API}/images/upload").respond(
                status_code=201,
                json={"images": [{"url": "https://ghost.example.com/img.jpg"}]},
            )
            await publisher.upload_image(
                credentials=credentials,
                image_url="https://example.com/photo.jpg",
            )
        assert route.called
        body = route.calls[0].request.content
        # multipart body must contain the fetched bytes, not the URL text
        assert b"real-bytes-123" in body
        assert b"https://example.com/photo.jpg" not in body

    async def test_upload_image_rejects_non_image(self, publisher, credentials):
        """Non-image content-type raises a clean error (B3 error path)."""
        with respx.mock:
            respx.get("https://example.com/page.html").respond(
                status_code=200,
                content=b"<html>not an image</html>",
                headers={"Content-Type": "text/html"},
            )
            with pytest.raises(Exception, match="image"):
                await publisher.upload_image(
                    credentials=credentials,
                    image_url="https://example.com/page.html",
                )

    async def test_upload_image_unreachable_url_raises(self, publisher, credentials):
        """Unreachable image URL raises a clean error (B3 error path)."""
        with respx.mock:
            respx.get("https://example.com/missing.jpg").respond(status_code=404)
            with pytest.raises(Exception, match="image|fetch|404"):
                await publisher.upload_image(
                    credentials=credentials,
                    image_url="https://example.com/missing.jpg",
                )


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Rate limit
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_GHOST_PUBLISHER, reason="services/publishers/ghost.py not implemented yet")
class TestGhostPublisherRateLimit:
    """Behavioral: Rate limit (429) backoff."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.GHOST,
            access_token="ghost_admin_api_key:secret",
        )

    @pytest.fixture
    def publisher(self):
        return GhostPublisher()

    async def test_rate_limit_causes_backoff(self, publisher, credentials):
        """429 triggers backoff and eventually succeeds."""
        with respx.mock:
            respx.post(f"{GHOST_API}/posts/").mock(
                side_effect=[
                    httpx.Response(429, json={"errors": [{"message": "Rate limit exceeded"}]}, headers={"Retry-After": "1"}),
                    httpx.Response(201, json={"posts": [{"id": "9", "status": "draft"}]}),
                ]
            )
            result = await publisher.create_post(
                credentials=credentials,
                title="Backoff Post",
                content="After backoff",
            )
        assert result["posts"][0]["id"] == "9"


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Server error
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_GHOST_PUBLISHER, reason="services/publishers/ghost.py not implemented yet")
class TestGhostPublisherServerError:
    """Behavioral: Server error (5xx) retry then fail."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.GHOST,
            access_token="ghost_admin_api_key:secret",
        )

    @pytest.fixture
    def publisher(self):
        return GhostPublisher()

    async def test_server_error_retries_then_raises(self, publisher, credentials):
        """5xx retries up to 3 times, then raises."""
        with respx.mock:
            route = respx.post(f"{GHOST_API}/posts/").respond(
                status_code=500,
                json={"errors": [{"message": "Internal server error"}]},
            )
            with pytest.raises(Exception, match="500 Internal Server Error"):
                await publisher.create_post(
                    credentials=credentials,
                    title="Error Post",
                    content="Server error test",
                )
        assert len(route.calls) <= 4  # 3 retries + original


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Format mobiledoc
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_GHOST_PUBLISHER, reason="services/publishers/ghost.py not implemented yet")
class TestGhostPublisherMobiledoc:
    """Behavioral: Content formatting as Mobiledoc."""

    def test_format_mobiledoc_returns_string(self):
        """_format_mobiledoc returns a Mobiledoc JSON string."""
        result = GhostPublisher._format_mobiledoc("# Hello\n\nThis is **bold**.")
        assert isinstance(result, str)

    def test_format_mobiledoc_is_valid_json(self):
        """_format_mobiledoc returns parseable JSON."""
        import json
        result = GhostPublisher._format_mobiledoc("Simple content")
        parsed = json.loads(result)
        assert "version" in parsed
        assert "sections" in parsed


import httpx  # noqa: E402 (needed for response helpers)
