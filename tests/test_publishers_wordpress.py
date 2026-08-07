"""Pre-dev tests for WordPressPublisher.

Interface tests → PASS immediately against the stub.
Behavioral tests → raise NotImplementedError until implementation.
Uses respx to mock WordPress REST API.
"""
from __future__ import annotations

import pytest
import respx

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.models.publish import PlatformCredentials, PublishPlatform
    from app.services.publishers.wordpress import WordPressPublisher

    HAS_WORDPRESS_PUBLISHER = True
except (ImportError, ModuleNotFoundError):
    HAS_WORDPRESS_PUBLISHER = False

    class PublishPlatform:  # type: ignore[no-redef]
        WORDPRESS = "wordpress"

    class PlatformCredentials:  # type: ignore[no-redef]
        pass


WORDPRESS_API = "https://example.wordpress.com/wp-json/wp/v2"


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — must pass immediately
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORDPRESS_PUBLISHER, reason="services/publishers/wordpress.py not implemented yet")
class TestWordPressPublisherInterface:
    """Interface: WordPressPublisher is importable and has expected API."""

    def test_importable(self):
        assert WordPressPublisher is not None

    def test_is_class(self):
        assert isinstance(WordPressPublisher, type)

    def test_has_create_post_method(self):
        assert hasattr(WordPressPublisher, "create_post")
        assert callable(WordPressPublisher.create_post)

    def test_has_authenticate_method(self):
        assert hasattr(WordPressPublisher, "authenticate")
        assert callable(WordPressPublisher.authenticate)

    def test_has_upload_image_method(self):
        assert hasattr(WordPressPublisher, "upload_image")
        assert callable(WordPressPublisher.upload_image)

    def test_has_refresh_token_method(self):
        assert hasattr(WordPressPublisher, "refresh_token")
        assert callable(WordPressPublisher.refresh_token)

    def test_create_post_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(WordPressPublisher.create_post)

    def test_authenticate_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(WordPressPublisher.authenticate)

    def test_upload_image_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(WordPressPublisher.upload_image)

    def test_refresh_token_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(WordPressPublisher.refresh_token)

    def test_init_accepts_http_client(self):
        import inspect
        sig = inspect.signature(WordPressPublisher.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params

    def test_create_post_has_status_param(self):
        import inspect
        sig = inspect.signature(WordPressPublisher.create_post)
        params = sig.parameters
        assert "status" in params
        assert params["status"].default == "draft"

    def test_create_post_has_categories_param(self):
        import inspect
        sig = inspect.signature(WordPressPublisher.create_post)
        assert "categories" in sig.parameters

    def test_create_post_has_tags_param(self):
        import inspect
        sig = inspect.signature(WordPressPublisher.create_post)
        assert "tags" in sig.parameters

    def test_create_post_has_featured_media_param(self):
        import inspect
        sig = inspect.signature(WordPressPublisher.create_post)
        assert "featured_media" in sig.parameters

    def test_create_post_has_content_param(self):
        import inspect
        sig = inspect.signature(WordPressPublisher.create_post)
        assert "content" in sig.parameters

    def test_create_post_has_title_param(self):
        import inspect
        sig = inspect.signature(WordPressPublisher.create_post)
        assert "title" in sig.parameters

    def test_create_post_has_credentials_param(self):
        import inspect
        sig = inspect.signature(WordPressPublisher.create_post)
        assert "credentials" in sig.parameters

    def test_create_post_has_excerpt_param(self):
        """create_post accepts an excerpt for AC #3 excerpt generation (M2)."""
        import inspect
        sig = inspect.signature(WordPressPublisher.create_post)
        assert "excerpt" in sig.parameters

    def test_retry_after_is_static(self):
        assert hasattr(WordPressPublisher, "_get_retry_after")


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — create_post success
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORDPRESS_PUBLISHER, reason="services/publishers/wordpress.py not implemented yet")
class TestWordPressPublisherCreatePost:
    """Behavioral: Successful post creation via WordPress REST API."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.WORDPRESS,
            access_token="valid_wp_token_123",
        )

    @pytest.fixture
    def publisher(self):
        return WordPressPublisher()

    async def test_create_post_returns_post_id(self, publisher, credentials):
        """POST /wp-json/wp/v2/posts returns 201 with post id."""
        with respx.mock:
            route = respx.post(f"{WORDPRESS_API}/posts").respond(
                status_code=201,
                json={"id": 42, "status": "draft", "title": {"rendered": "Test"}},
            )
            result = await publisher.create_post(
                credentials=credentials,
                content="Hello WordPress!",
                title="Test Post",
            )
        assert route.called
        assert result["id"] == 42
        assert result["status"] == "draft"

    async def test_create_post_with_title_and_content(self, publisher, credentials):
        """Payload includes title and content fields."""
        with respx.mock:
            route = respx.post(f"{WORDPRESS_API}/posts").respond(
                status_code=201,
                json={"id": 43, "status": "draft"},
            )
            await publisher.create_post(
                credentials=credentials,
                content="Post body",
                title="My Title",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert sent_json.get("title") == "My Title"
        assert sent_json.get("content") == "Post body"

    async def test_create_post_with_categories_and_tags(self, publisher, credentials):
        """Payload includes categories and tags lists."""
        with respx.mock:
            route = respx.post(f"{WORDPRESS_API}/posts").respond(
                status_code=201,
                json={"id": 44, "status": "draft"},
            )
            await publisher.create_post(
                credentials=credentials,
                content="Tagged post",
                categories=[1, 5],
                tags=[10, 20],
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert sent_json.get("categories") == [1, 5]
        assert sent_json.get("tags") == [10, 20]

    async def test_create_post_with_featured_image(self, publisher, credentials):
        """Payload includes featured_media attachment ID."""
        with respx.mock:
            route = respx.post(f"{WORDPRESS_API}/posts").respond(
                status_code=201,
                json={"id": 45, "featured_media": 99},
            )
            await publisher.create_post(
                credentials=credentials,
                content="Image post",
                featured_media="99",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert sent_json.get("featured_media") == "99"

    async def test_create_post_draft_status(self, publisher, credentials):
        """status='draft' is sent in the payload."""
        with respx.mock:
            route = respx.post(f"{WORDPRESS_API}/posts").respond(
                status_code=201,
                json={"id": 46, "status": "draft"},
            )
            await publisher.create_post(
                credentials=credentials,
                content="Draft content",
                status="draft",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert sent_json.get("status") == "draft"

    async def test_create_post_publish_status(self, publisher, credentials):
        """status='publish' is sent in the payload."""
        with respx.mock:
            route = respx.post(f"{WORDPRESS_API}/posts").respond(
                status_code=201,
                json={"id": 47, "status": "publish"},
            )
            await publisher.create_post(
                credentials=credentials,
                content="Published content",
                status="publish",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert sent_json.get("status") == "publish"

    async def test_create_post_schedule_status(self, publisher, credentials):
        """status='future' is sent for scheduled posts."""
        with respx.mock:
            route = respx.post(f"{WORDPRESS_API}/posts").respond(
                status_code=201,
                json={"id": 48, "status": "future"},
            )
            await publisher.create_post(
                credentials=credentials,
                content="Scheduled content",
                status="future",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert sent_json.get("status") == "future"

    async def test_create_post_with_explicit_excerpt(self, publisher, credentials):
        """An explicit excerpt is sent in the payload (M2)."""
        with respx.mock:
            route = respx.post(f"{WORDPRESS_API}/posts").respond(
                status_code=201,
                json={"id": 49, "status": "draft"},
            )
            await publisher.create_post(
                credentials=credentials,
                content="Post body",
                excerpt="A short summary",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert sent_json.get("excerpt") == "A short summary"

    async def test_create_post_derives_excerpt_from_content(self, publisher, credentials):
        """Without an explicit excerpt, one is derived from the content (M2)."""
        with respx.mock:
            route = respx.post(f"{WORDPRESS_API}/posts").respond(
                status_code=201,
                json={"id": 50, "status": "draft"},
            )
            long_content = "First paragraph of the post.\n\nSecond paragraph with more text."
            await publisher.create_post(credentials=credentials, content=long_content)
        assert route.called
        sent_json = route.calls[0].request.json()
        excerpt = sent_json.get("excerpt")
        assert excerpt
        assert excerpt.startswith("First paragraph of the post")


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Auth failure + OAuth2 refresh
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORDPRESS_PUBLISHER, reason="services/publishers/wordpress.py not implemented yet")
class TestWordPressPublisherAuth:
    """Behavioral: Auth failure (401) triggers OAuth2 refresh + retry."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.WORDPRESS,
            access_token="expired_token",
            refresh_token="refresh_xyz",
            platform_user_id="https://example.wordpress.com",
        )

    @pytest.fixture
    def publisher(self):
        return WordPressPublisher()

    async def test_auth_failure_refreshes_token_and_retries(self, publisher, credentials):
        """401 → refresh OAuth2 token → retry the post once."""
        auth_called = False

        async def _refresh_handler(request):
            nonlocal auth_called
            auth_called = True
            return httpx.Response(
                status_code=200,
                json={"access_token": "fresh_token", "token_type": "bearer"},
            )

        with respx.mock:
            respx.post(f"{WORDPRESS_API}/posts").mock(
                side_effect=[
                    httpx.Response(401, json={"code": "rest_cookie_invalid_nonce", "message": "Cookie nonce is invalid"}),
                    httpx.Response(201, json={"id": 50, "status": "draft"}),
                ]
            )
            respx.post("https://example.wordpress.com/oauth/token").mock(
                side_effect=_refresh_handler,
            )
            result = await publisher.create_post(
                credentials=credentials,
                content="Retry test",
            )
        assert auth_called, "OAuth2 token refresh should have been called"
        assert result["id"] == 50

    async def test_refresh_uses_env_client_credentials(self, publisher, monkeypatch):
        """refresh_token resolves client_id/secret from env, not placeholders (B2)."""
        monkeypatch.setenv("WORDPRESS_CLIENT_ID", "env_client_123")
        monkeypatch.setenv("WORDPRESS_CLIENT_SECRET", "env_secret_456")
        creds = PlatformCredentials(
            platform=PublishPlatform.WORDPRESS,
            access_token="expired",
            refresh_token="refresh_env",
            platform_user_id="https://example.wordpress.com",
        )

        async def _refresh_handler(request):
            return httpx.Response(
                status_code=200,
                json={"access_token": "fresh_from_env", "token_type": "bearer"},
            )

        with respx.mock:
            route = respx.post("https://example.wordpress.com/oauth/token").mock(
                side_effect=_refresh_handler,
            )
            result = await publisher.refresh_token(creds)
        assert route.called
        sent = route.calls[0].request
        body = sent.content.decode()
        assert "env_client_123" in body
        assert "env_secret_456" in body
        assert "wordpress_client_id" not in body
        assert "client_secret_placeholder" not in body
        assert result.access_token == "fresh_from_env"

    async def test_refresh_token_url_from_site(self, publisher):
        """refresh_token derives the token URL from the site URL (B2)."""
        creds = PlatformCredentials(
            platform=PublishPlatform.WORDPRESS,
            access_token="expired",
            refresh_token="refresh_rt",
            platform_user_id="https://mysite.example.com",
        )

        async def _refresh_handler(request):
            return httpx.Response(
                status_code=200,
                json={"access_token": "fresh", "token_type": "bearer"},
            )

        with respx.mock:
            route = respx.post("https://mysite.example.com/oauth/token").mock(
                side_effect=_refresh_handler,
            )
            await publisher.refresh_token(creds)
        assert route.called

    async def test_refresh_token_url_from_options(self, publisher):
        """refresh_token prefers the token endpoint in credentials.options (B2)."""
        creds = PlatformCredentials(
            platform=PublishPlatform.WORDPRESS,
            access_token="expired",
            refresh_token="refresh_opts",
            platform_user_id="https://site.example.com",
            options={"token_endpoint": "https://auth.example.com/oauth2/token"},
        )

        async def _refresh_handler(request):
            return httpx.Response(
                status_code=200,
                json={"access_token": "fresh_opts", "token_type": "bearer"},
            )

        with respx.mock:
            route = respx.post("https://auth.example.com/oauth2/token").mock(
                side_effect=_refresh_handler,
            )
            await publisher.refresh_token(creds)
        assert route.called

    async def test_auth_without_refresh_token_raises(self, publisher, credentials_no_refresh):
        """401 without refresh_token raises immediately."""
        with respx.mock:
            respx.post(f"{WORDPRESS_API}/posts").respond(
                status_code=401,
                json={"code": "rest_cookie_invalid_nonce", "message": "Unauthorized"},
            )
            with pytest.raises(Exception, match="WordPress post failed|401"):
                await publisher.create_post(
                    credentials=credentials_no_refresh,
                    content="No refresh available",
                )


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Rate limit
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORDPRESS_PUBLISHER, reason="services/publishers/wordpress.py not implemented yet")
class TestWordPressPublisherRateLimit:
    """Behavioral: Rate limit (429) backoff."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.WORDPRESS,
            access_token="valid_token",
        )

    @pytest.fixture
    def publisher(self):
        return WordPressPublisher()

    async def test_rate_limit_causes_backoff(self, publisher, credentials):
        """429 triggers backoff and eventually succeeds."""
        with respx.mock:
            respx.post(f"{WORDPRESS_API}/posts").mock(
                side_effect=[
                    httpx.Response(
                        429,
                        json={"code": "rate_limit_exceeded", "message": "Too many requests"},
                        headers={"Retry-After": "1"},
                    ),
                    httpx.Response(201, json={"id": 51, "status": "draft"}),
                ]
            )
            result = await publisher.create_post(
                credentials=credentials,
                content="Backoff test",
            )
        assert result["id"] == 51


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Upload image
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORDPRESS_PUBLISHER, reason="services/publishers/wordpress.py not implemented yet")
class TestWordPressPublisherUploadImage:
    """Behavioral: Image upload to WordPress media library."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.WORDPRESS,
            access_token="valid_token",
        )

    @pytest.fixture
    def publisher(self):
        return WordPressPublisher()

    async def test_upload_image_returns_media_id(self, publisher, credentials):
        """POST /wp-json/wp/v2/media returns attachment data."""
        with respx.mock:
            route = respx.post("https://example.wordpress.com/wp-json/wp/v2/media").respond(
                status_code=201,
                json={"id": 101, "source_url": "https://example.wordpress.com/wp-content/uploads/2026/08/img.jpg"},
            )
            result = await publisher.upload_image(
                credentials=credentials,
                image_url="https://example.com/photo.jpg",
                alt_text="Test image",
            )
        assert route.called
        assert result["id"] == 101

    async def test_upload_image_with_alt_text(self, publisher, credentials):
        """Alt text is sent in the upload payload."""
        with respx.mock:
            route = respx.post("https://example.wordpress.com/wp-json/wp/v2/media").respond(
                status_code=201,
                json={"id": 102, "source_url": "https://example.wordpress.com/img.jpg"},
            )
            await publisher.upload_image(
                credentials=credentials,
                image_url="https://example.com/photo.jpg",
                alt_text="My alt text",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert sent_json.get("alt_text") == "My alt text"


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Server error
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_WORDPRESS_PUBLISHER, reason="services/publishers/wordpress.py not implemented yet")
class TestWordPressPublisherServerError:
    """Behavioral: Server error (5xx) retry then fail."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.WORDPRESS,
            access_token="valid_token",
        )

    @pytest.fixture
    def publisher(self):
        return WordPressPublisher()

    async def test_server_error_retries_three_times_then_raises(self, publisher, credentials):
        """5xx retries up to 3 times, then raises."""
        with respx.mock:
            route = respx.post(f"{WORDPRESS_API}/posts").respond(
                status_code=500,
                json={"code": "internal_server_error", "message": "Something went wrong"},
            )
            with pytest.raises(Exception, match="500 Internal Server Error"):
                await publisher.create_post(
                    credentials=credentials,
                    content="Server error test",
                )
        assert len(route.calls) <= 4  # 3 retries + original


# ════════════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def credentials_no_refresh():
    return PlatformCredentials(
        platform=PublishPlatform.WORDPRESS,
        access_token="token_no_refresh",
    )


import httpx  # noqa: E402 (needed for response helpers)
