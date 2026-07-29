"""Pre-dev tests for MediumPublisher (Phase 5).

Source of truth: analysis/analysis-brief.md §4.5 MediumPublisher.
Interface tests → xfail until services/publishers/medium.py is implemented.
Behavioral tests use respx to mock Medium API.
"""

from __future__ import annotations

import pytest
import respx

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.models.publish import PlatformCredentials, PublishPlatform
    from app.services.publishers.medium import MediumPublisher

    HAS_MEDIUM_PUBLISHER = True
except (ImportError, ModuleNotFoundError):
    HAS_MEDIUM_PUBLISHER = False

    class PublishPlatform:  # type: ignore[no-redef]
        MEDIUM = "medium"

    class PlatformCredentials:  # type: ignore[no-redef]
        pass


MEDIUM_API = "https://api.medium.com"


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_MEDIUM_PUBLISHER, reason="services/publishers/medium.py not implemented yet")
class TestMediumPublisherInterface:
    """Interface: MediumPublisher is importable and has expected API."""

    def test_importable(self):
        assert MediumPublisher is not None

    def test_is_class(self):
        assert isinstance(MediumPublisher, type)

    def test_has_create_article(self):
        assert hasattr(MediumPublisher, "create_article")
        assert callable(MediumPublisher.create_article)

    def test_create_article_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(MediumPublisher.create_article)

    def test_init_accepts_http_client(self):
        import inspect
        sig = inspect.signature(MediumPublisher.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Success
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_MEDIUM_PUBLISHER, reason="services/publishers/medium.py not implemented yet")
class TestMediumPublisherSuccess:
    """Behavioral: Successful article creation."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.MEDIUM,
            access_token="valid_medium_token",
            platform_user_id="user_abc123",
        )

    @pytest.fixture
    def publisher(self):
        return MediumPublisher()

    async def test_create_article_returns_201_with_url(self, credentials, publisher):
        """POST /v1/users/{id}/posts returns 201 with article URL."""
        with respx.mock:
            route = respx.post(f"{MEDIUM_API}/v1/users/{credentials.platform_user_id}/posts").respond(
                status_code=201,
                json={"data": {"id": "post_xyz", "url": "https://medium.com/@user/post_xyz"}},
            )
            result = await publisher.create_article(
                credentials=credentials,
                title="My Article",
                content="Article content here",
            )
        assert route.called
        assert result["data"]["url"] == "https://medium.com/@user/post_xyz"


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Markdown content format
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_MEDIUM_PUBLISHER, reason="services/publishers/medium.py not implemented yet")
class TestMediumPublisherMarkdown:
    """Behavioral: Payload includes contentFormat='markdown'."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.MEDIUM,
            access_token="valid_medium_token",
            platform_user_id="user_md",
        )

    @pytest.fixture
    def publisher(self):
        return MediumPublisher()

    async def test_content_format_is_markdown(self, credentials, publisher):
        """Payload has contentFormat set to 'markdown'."""
        with respx.mock:
            route = respx.post(f"{MEDIUM_API}/v1/users/{credentials.platform_user_id}/posts").respond(
                status_code=201,
                json={"data": {"id": "md_post", "url": "https://medium.com/@u/md_post"}},
            )
            await publisher.create_article(
                credentials=credentials,
                title="MD Article",
                content="# Markdown\n\nThis is *formatted*",
                content_format="markdown",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert sent_json.get("contentFormat") == "markdown"

    async def test_alternative_content_format(self, credentials, publisher):
        """accepts html as contentFormat as well."""
        with respx.mock:
            route = respx.post(f"{MEDIUM_API}/v1/users/{credentials.platform_user_id}/posts").respond(
                status_code=201,
                json={"data": {"id": "html_post", "url": "https://medium.com/@u/html_post"}},
            )
            await publisher.create_article(
                credentials=credentials,
                title="HTML Article",
                content="<p>HTML content</p>",
                content_format="html",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert sent_json.get("contentFormat") == "html"


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Draft vs published
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_MEDIUM_PUBLISHER, reason="services/publishers/medium.py not implemented yet")
class TestMediumPublisherPublishStatus:
    """Behavioral: publishStatus field controls draft vs published."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.MEDIUM,
            access_token="valid_medium_token",
            platform_user_id="user_status",
        )

    @pytest.fixture
    def publisher(self):
        return MediumPublisher()

    async def test_draft_status(self, credentials, publisher):
        """publishStatus='draft' is sent in the payload."""
        with respx.mock:
            route = respx.post(f"{MEDIUM_API}/v1/users/{credentials.platform_user_id}/posts").respond(
                status_code=201,
                json={"data": {"id": "draft_1", "url": "https://medium.com/@u/draft_1"}},
            )
            await publisher.create_article(
                credentials=credentials,
                title="Draft Article",
                content="Draft content",
                publish_status="draft",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert sent_json.get("publishStatus") == "draft"

    async def test_public_status(self, credentials, publisher):
        """publishStatus='public' is sent in the payload."""
        with respx.mock:
            route = respx.post(f"{MEDIUM_API}/v1/users/{credentials.platform_user_id}/posts").respond(
                status_code=201,
                json={"data": {"id": "pub_1", "url": "https://medium.com/@u/pub_1"}},
            )
            await publisher.create_article(
                credentials=credentials,
                title="Public Article",
                content="Public content",
                publish_status="public",
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert sent_json.get("publishStatus") == "public"


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Publication post
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_MEDIUM_PUBLISHER, reason="services/publishers/medium.py not implemented yet")
class TestMediumPublisherPublication:
    """Behavioral: Publication post routes to /v1/publications/{pubId}/posts."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.MEDIUM,
            access_token="valid_medium_token",
            platform_user_id="user_pub",
        )

    @pytest.fixture
    def publisher(self):
        return MediumPublisher()

    async def test_publication_post(self, credentials, publisher):
        """When publication_id is provided, POST to publications endpoint."""
        pub_id = "pub_98765"
        with respx.mock:
            route = respx.post(f"{MEDIUM_API}/v1/publications/{pub_id}/posts").respond(
                status_code=201,
                json={"data": {"id": "pub_post_1", "url": "https://medium.com/p/pub_post_1"}},
            )
            result = await publisher.create_article(
                credentials=credentials,
                title="Pub Article",
                content="Publication post content",
                publication_id=pub_id,
            )
        assert route.called
        assert result["data"]["id"] == "pub_post_1"

    async def test_publication_post_content(self, credentials, publisher):
        """Publication post payload includes title/content."""
        pub_id = "pub_444"
        with respx.mock:
            route = respx.post(f"{MEDIUM_API}/v1/publications/{pub_id}/posts").respond(
                status_code=201,
                json={"data": {"id": "pub_post_2", "url": "https://medium.com/p/pub_post_2"}},
            )
            await publisher.create_article(
                credentials=credentials,
                title="Pub Article 2",
                content="More publication content",
                publication_id=pub_id,
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert sent_json.get("title") == "Pub Article 2"
        assert "content" in sent_json
