"""Pre-dev tests for InstagramPublisher (Instagram Graph API — Meta v19.0).

Source of truth: analysis-brief.md §4.x InstagramPublisher + task t_b7c1abd9.
Interface tests → PASS immediately against the stub (contract).
Behavioral tests → FAIL with NotImplementedError until dev implements
(src/app/services/publishers/instagram.py, task t_93c9ee41).

Instagram Graph API publishing flow (container-based):
  1. Single image: POST /{ig-user-id}/media → POST /{ig-user-id}/media_publish
  2. Carousel: POST /{ig-user-id}/media per item → POST carousel container
     (children=...) → POST /{ig-user-id}/media_publish
  3. Reel: POST /{ig-user-id}/media with media_type=REELS → poll container
     status until FINISHED → POST /{ig-user-id}/media_publish
  4. Token refresh: Graph API /oauth/access_token (fb_exchange_token) then retry

Mock strategy: respx (httpx-native routing), matching the sibling suites
(test_publish_linkedin.py / medium / twitter). NEVER MagicMock.
"""

from __future__ import annotations

import logging

import pytest
import respx

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.models.publish import PlatformCredentials, PublishPlatform
    from app.services.publishers.instagram import InstagramPublisher

    HAS_INSTAGRAM_PUBLISHER = True
except (ImportError, ModuleNotFoundError):
    HAS_INSTAGRAM_PUBLISHER = False

    class PublishPlatform:  # type: ignore[no-redef]
        INSTAGRAM = "instagram"

    class PlatformCredentials:  # type: ignore[no-redef]
        pass


GRAPH_API = "https://graph.facebook.com/v19.0"
IG_USER_ID = "17841400123456789"

SKIP_REASON = "services/publishers/instagram.py not implemented yet"
SKIP_MARK = pytest.mark.skipif(not HAS_INSTAGRAM_PUBLISHER, reason=SKIP_REASON)


def _container_ok(container_id: str) -> respx.MockResponse:
    """Real Graph API container-creation response shape: {"id": "..."}."""
    return respx.MockResponse(status_code=200, json={"id": container_id})


def _media_publish_ok(media_id: str) -> respx.MockResponse:
    """Real Graph API media_publish response shape: {"id": "..."}."""
    return respx.MockResponse(status_code=200, json={"id": media_id})


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — must PASS immediately against the stub
# ════════════════════════════════════════════════════════════════════════════════


@SKIP_MARK
class TestInstagramPublisherInterface:
    """Interface: InstagramPublisher is importable and has expected API."""

    def test_importable(self):
        assert InstagramPublisher is not None

    def test_is_class(self):
        assert isinstance(InstagramPublisher, type)

    def test_has_publish_method(self):
        assert hasattr(InstagramPublisher, "publish")
        assert callable(InstagramPublisher.publish)

    def test_publish_is_async(self):
        import inspect

        assert inspect.iscoroutinefunction(InstagramPublisher.publish)

    def test_has_refresh_token_method(self):
        assert hasattr(InstagramPublisher, "refresh_token")
        assert callable(InstagramPublisher.refresh_token)

    def test_refresh_token_is_async(self):
        import inspect

        assert inspect.iscoroutinefunction(InstagramPublisher.refresh_token)

    def test_has_build_container_method(self):
        assert hasattr(InstagramPublisher, "build_container")
        assert callable(InstagramPublisher.build_container)

    def test_build_container_is_async(self):
        import inspect

        assert inspect.iscoroutinefunction(InstagramPublisher.build_container)

    def test_has_publish_container_method(self):
        assert hasattr(InstagramPublisher, "publish_container")
        assert callable(InstagramPublisher.publish_container)

    def test_publish_container_is_async(self):
        import inspect

        assert inspect.iscoroutinefunction(InstagramPublisher.publish_container)

    def test_init_accepts_http_client(self):
        import inspect

        sig = inspect.signature(InstagramPublisher.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params
        # The stub must accept an injectable httpx.AsyncClient so tests can
        # substitute a mocked transport — matches sibling publisher patterns.
        assert any(
            name in ("http_client", "client", "http") for name in params[1:]
        ), f"expected injectable http client param, got {params}"

    def test_integrates_with_publish_platform_instagram(self):
        """Instagram publisher works with PublishPlatform.INSTAGRAM enum."""
        assert hasattr(PublishPlatform, "INSTAGRAM")
        assert PublishPlatform.INSTAGRAM == "instagram"


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — RED phase (NotImplementedError until dev implements)
# ════════════════════════════════════════════════════════════════════════════════

# Every behavioral test below currently fails with NotImplementedError because
# the stub methods raise it. Once the developer implements the publisher
# (task t_93c9ee41), these tests turn GREEN and verify the real Graph API flow.


@SKIP_MARK
class TestInstagramPublisherSingleImageBehavioral:
    """Behavioral: single image post — container then publish."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.INSTAGRAM,
            access_token="valid_ig_token_abc123",
            platform_user_id=IG_USER_ID,
        )

    @pytest.fixture
    def publisher(self):
        return InstagramPublisher()

    async def test_single_image_creates_container_then_publishes(self, publisher, credentials):
        """POST /{ig-user-id}/media then POST /{ig-user-id}/media_publish."""
        with respx.mock:
            container_route = respx.post(f"{GRAPH_API}/{IG_USER_ID}/media").respond(
                status_code=200,
                json={"id": "17841405678901234"},
            )
            publish_route = respx.post(f"{GRAPH_API}/{IG_USER_ID}/media_publish").respond(
                status_code=200,
                json={"id": "17841405678905678"},
            )

            result = await publisher.publish(
                credentials=credentials,
                image_url="https://example.com/photo.jpg",
                caption="Hello Instagram!",
            )

        assert container_route.called
        assert publish_route.called
        assert result["id"] == "17841405678905678"

    async def test_single_image_container_payload_has_image_url(self, publisher, credentials):
        """Container creation payload includes image_url field."""
        with respx.mock:
            container_route = respx.post(f"{GRAPH_API}/{IG_USER_ID}/media").respond(
                status_code=200,
                json={"id": "container_123"},
            )
            respx.post(f"{GRAPH_API}/{IG_USER_ID}/media_publish").respond(
                status_code=200,
                json={"id": "post_123"},
            )

            await publisher.publish(
                credentials=credentials,
                image_url="https://example.com/beach.png",
                caption="Beach day",
            )

        assert container_route.called
        sent_json = container_route.calls[0].request.json()
        assert "image_url" in sent_json
        assert sent_json["image_url"] == "https://example.com/beach.png"

    async def test_single_image_container_payload_has_caption(self, publisher, credentials):
        """Container creation payload includes caption field."""
        with respx.mock:
            container_route = respx.post(f"{GRAPH_API}/{IG_USER_ID}/media").respond(
                status_code=200,
                json={"id": "container_456"},
            )
            respx.post(f"{GRAPH_API}/{IG_USER_ID}/media_publish").respond(
                status_code=200,
                json={"id": "post_456"},
            )

            await publisher.publish(
                credentials=credentials,
                image_url="https://example.com/sunset.jpg",
                caption="Beautiful sunset #photography",
            )

        sent_json = container_route.calls[0].request.json()
        assert "caption" in sent_json
        assert "Beautiful sunset" in sent_json["caption"]

    async def test_publish_payload_has_creation_id(self, publisher, credentials):
        """media_publish payload includes creation_id from container response."""
        with respx.mock:
            respx.post(f"{GRAPH_API}/{IG_USER_ID}/media").respond(
                status_code=200,
                json={"id": "container_789"},
            )
            publish_route = respx.post(f"{GRAPH_API}/{IG_USER_ID}/media_publish").respond(
                status_code=200,
                json={"id": "post_789"},
            )

            await publisher.publish(
                credentials=credentials,
                image_url="https://example.com/img.jpg",
                caption="Test post",
            )

        sent_json = publish_route.calls[0].request.json()
        assert "creation_id" in sent_json
        assert sent_json["creation_id"] == "container_789"


@SKIP_MARK
class TestInstagramPublisherCarouselBehavioral:
    """Behavioral: carousel post — per-item containers, carousel container, publish."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.INSTAGRAM,
            access_token="valid_ig_token_carousel",
            platform_user_id=IG_USER_ID,
        )

    @pytest.fixture
    def publisher(self):
        return InstagramPublisher()

    def _media_route(self, media_route):
        """Dispatch /media responses by JSON body (single mocked route).

        respx matches routes by URL+method, and every /media POST to the same
        ig-user-id looks identical on the wire except for its JSON payload, so
        one route with a body-dispatching side_effect represents the whole
        multi-container flow. Container responses use real Graph API shapes.
        """

        def handler(request):
            import json

            body = json.loads(request.content)
            if body.get("media_type") == "CAROUSEL":
                return respx.MockResponse(status_code=200, json={"id": "carousel_container"})
            if "children" in body:
                return respx.MockResponse(status_code=200, json={"id": "carousel_item"})
            return respx.MockResponse(status_code=200, json={"id": "single_item"})

        media_route.mock(side_effect=handler)

    async def test_carousel_creates_item_containers_then_carousel_container(self, publisher, credentials):
        """Item containers created first, then carousel container, then publish."""
        with respx.mock:
            media_route = respx.post(f"{GRAPH_API}/{IG_USER_ID}/media")
            self._media_route(media_route)
            publish_route = respx.post(f"{GRAPH_API}/{IG_USER_ID}/media_publish").respond(
                status_code=200,
                json={"id": "carousel_post_123"},
            )

            result = await publisher.publish(
                credentials=credentials,
                media_type="CAROUSEL",
                children=[
                    {"image_url": "https://example.com/img1.jpg"},
                    {"image_url": "https://example.com/img2.jpg"},
                ],
                caption="Check out this carousel!",
            )

        assert publish_route.called
        # Exactly 3 container creations: 2 per-item containers + 1 carousel container
        assert media_route.call_count == 3
        assert result["id"] == "carousel_post_123"

    async def test_carousel_container_payload_has_media_type_and_children(self, publisher, credentials):
        """Carousel container payload has media_type=CAROUSEL and children list."""
        with respx.mock:
            media_route = respx.post(f"{GRAPH_API}/{IG_USER_ID}/media")
            self._media_route(media_route)
            respx.post(f"{GRAPH_API}/{IG_USER_ID}/media_publish").respond(
                status_code=200,
                json={"id": "pub_123"},
            )

            await publisher.publish(
                credentials=credentials,
                media_type="CAROUSEL",
                children=[
                    {"image_url": "https://example.com/a.jpg"},
                    {"image_url": "https://example.com/b.jpg"},
                ],
                caption="Carousel",
            )

        # The final call is the carousel container creation (children + CAROUSEL).
        import json

        payloads = [json.loads(c.request.content) for c in media_route.calls]
        carousel_payload = payloads[-1]
        assert carousel_payload.get("media_type") == "CAROUSEL"
        assert "children" in carousel_payload


@SKIP_MARK
class TestInstagramPublisherReelBehavioral:
    """Behavioral: reel post — container with REELS media_type, status poll, publish."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.INSTAGRAM,
            access_token="valid_ig_token_reel",
            platform_user_id=IG_USER_ID,
        )

    @pytest.fixture
    def publisher(self):
        return InstagramPublisher()

    async def test_reel_container_has_reels_media_type(self, publisher, credentials):
        """Reel container creation sends media_type=REELS and video_url."""
        with respx.mock:
            container_route = respx.post(f"{GRAPH_API}/{IG_USER_ID}/media").respond(
                status_code=200,
                json={"id": "reel_container"},
            )
            # Status check — FINISHED (container GET endpoint)
            respx.get(f"{GRAPH_API}/reel_container").respond(
                status_code=200,
                json={"id": "reel_container", "status_code": "FINISHED"},
            )
            respx.post(f"{GRAPH_API}/{IG_USER_ID}/media_publish").respond(
                status_code=200,
                json={"id": "reel_post_123"},
            )

            await publisher.publish(
                credentials=credentials,
                media_type="REELS",
                video_url="https://example.com/video.mp4",
                caption="New reel!",
            )

        sent_json = container_route.calls[0].request.json()
        assert sent_json.get("media_type") == "REELS"
        assert "video_url" in sent_json

    async def test_reel_polls_status_before_publishing(self, publisher, credentials):
        """Reel container status is polled (IN_PROGRESS → FINISHED) before media_publish."""
        with respx.mock:
            respx.post(f"{GRAPH_API}/{IG_USER_ID}/media").respond(
                status_code=200,
                json={"id": "reel_status_container"},
            )
            # First poll — still processing
            respx.get(f"{GRAPH_API}/reel_status_container").respond(
                status_code=200,
                json={"id": "reel_status_container", "status_code": "IN_PROGRESS"},
            )
            # Second poll — finished
            respx.get(f"{GRAPH_API}/reel_status_container").respond(
                status_code=200,
                json={"id": "reel_status_container", "status_code": "FINISHED"},
            )
            publish_route = respx.post(f"{GRAPH_API}/{IG_USER_ID}/media_publish").respond(
                status_code=200,
                json={"id": "reel_published"},
            )

            result = await publisher.publish(
                credentials=credentials,
                media_type="REELS",
                video_url="https://example.com/reel.mp4",
                caption="Check this out",
            )

        assert publish_route.called
        assert result["id"] == "reel_published"


@SKIP_MARK
class TestInstagramPublisherTokenRefreshBehavioral:
    """Behavioral: expired token triggers refresh via Graph API, then retries."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.INSTAGRAM,
            access_token="expired_token_xyz",
            refresh_token="refresh_token_abc",
            platform_user_id=IG_USER_ID,
        )

    @pytest.fixture
    def publisher(self):
        return InstagramPublisher()

    async def test_expired_token_refreshes_and_retries(self, publisher, credentials):
        """Graph API OAuthException (code 190) → refresh via /oauth/access_token → retry."""
        refresh_called = False

        def _refresh_handler(request):
            nonlocal refresh_called
            refresh_called = True
            return respx.MockResponse(
                status_code=200,
                json={"access_token": "fresh_token_123", "expires_in": 3600},
            )

        with respx.mock:
            # First attempt — token expired (Graph API error code 190); retry succeeds
            media_route = respx.post(f"{GRAPH_API}/{IG_USER_ID}/media").mock(
                side_effect=[
                    respx.MockResponse(
                        status_code=200,
                        json={
                            "error": {
                                "message": "Invalid OAuth access token.",
                                "type": "OAuthException",
                                "code": 190,
                            }
                        },
                    ),
                    respx.MockResponse(status_code=200, json={"id": "container_after_refresh"}),
                ]
            )
            # Token refresh endpoint (Facebook Graph API OAuth)
            respx.post(f"{GRAPH_API}/oauth/access_token").mock(side_effect=_refresh_handler)
            # Publish
            respx.post(f"{GRAPH_API}/{IG_USER_ID}/media_publish").respond(
                status_code=200,
                json={"id": "post_after_refresh"},
            )

            result = await publisher.publish(
                credentials=credentials,
                image_url="https://example.com/img.jpg",
                caption="After token refresh",
            )

        assert refresh_called, "Token refresh should have been called"
        assert media_route.call_count == 2, "Original request should have been retried"
        assert result["id"] == "post_after_refresh"

    async def test_refresh_token_hits_graph_oauth_endpoint(self, publisher, credentials):
        """refresh_token() calls the Graph API /oauth/access_token endpoint."""
        with respx.mock:
            token_route = respx.post(f"{GRAPH_API}/oauth/access_token").respond(
                status_code=200,
                json={"access_token": "brand_new_token", "expires_in": 5184000},
            )
            new_token = await publisher.refresh_token(credentials)

        assert token_route.called
        assert new_token == "brand_new_token"


@SKIP_MARK
class TestInstagramPublisherErrorMappingBehavioral:
    """Behavioral: Graph API errors are mapped to appropriate exceptions."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.INSTAGRAM,
            access_token="valid_token",
            platform_user_id=IG_USER_ID,
        )

    @pytest.fixture
    def publisher(self):
        return InstagramPublisher()

    async def test_rate_limit_error_raises(self, publisher, credentials):
        """HTTP 429 / Graph API code 4 (rate limit) maps to rate-limit exception."""
        with respx.mock:
            respx.post(f"{GRAPH_API}/{IG_USER_ID}/media").respond(
                status_code=429,
                json={
                    "error": {
                        "message": "Rate limit reached",
                        "type": "OAuthException",
                        "code": 4,
                    }
                },
            )

            with pytest.raises(Exception) as exc_info:
                await publisher.publish(
                    credentials=credentials,
                    image_url="https://example.com/img.jpg",
                    caption="Rate limited",
                )
            assert "rate" in str(exc_info.value).lower() or "limit" in str(exc_info.value).lower()

    async def test_permission_scope_error_raises(self, publisher, credentials):
        """Permission scope error (code 200 / subcode 1888029) maps to permission exception."""
        with respx.mock:
            respx.post(f"{GRAPH_API}/{IG_USER_ID}/media").respond(
                status_code=400,
                json={
                    "error": {
                        "message": "Invalid scope",
                        "type": "OAuthException",
                        "code": 200,
                        "error_subcode": 1888029,
                    }
                },
            )

            with pytest.raises(Exception) as exc_info:
                await publisher.publish(
                    credentials=credentials,
                    image_url="https://example.com/img.jpg",
                    caption="Permission error",
                )
            assert "permission" in str(exc_info.value).lower() or "scope" in str(exc_info.value).lower()

    async def test_app_review_required_error_raises(self, publisher, credentials):
        """App review required (code 10) maps to app-review exception."""
        with respx.mock:
            respx.post(f"{GRAPH_API}/{IG_USER_ID}/media").respond(
                status_code=400,
                json={
                    "error": {
                        "message": "Application does not have permission for this action",
                        "type": "OAuthException",
                        "code": 10,
                    }
                },
            )

            with pytest.raises(Exception) as exc_info:
                await publisher.publish(
                    credentials=credentials,
                    image_url="https://example.com/img.jpg",
                    caption="App review needed",
                )
            assert "review" in str(exc_info.value).lower() or "permission" in str(exc_info.value).lower()


@SKIP_MARK
class TestInstagramPublisherTokenSecurityBehavioral:
    """Behavioral: OAuth tokens are never leaked to log output."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.INSTAGRAM,
            access_token="super_secret_ig_token_98765",
            platform_user_id=IG_USER_ID,
        )

    @pytest.fixture
    def publisher(self):
        return InstagramPublisher()

    async def test_token_not_in_log_output(self, publisher, credentials, caplog):
        """Access token must never appear in any logger output."""
        with caplog.at_level(logging.DEBUG), respx.mock:
            respx.post(f"{GRAPH_API}/{IG_USER_ID}/media").respond(
                status_code=200,
                json={"id": "container_security"},
            )
            respx.post(f"{GRAPH_API}/{IG_USER_ID}/media_publish").respond(
                status_code=200,
                json={"id": "post_security"},
            )

            await publisher.publish(
                    credentials=credentials,
                    image_url="https://example.com/secure.jpg",
                    caption="Security test",
                )

        for record in caplog.records:
            assert "super_secret_ig_token_98765" not in record.message, (
                f"Token leaked in log: {record.message}"
            )
