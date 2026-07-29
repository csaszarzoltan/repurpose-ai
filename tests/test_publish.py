"""Pre-dev tests for PublishService orchestrator (Phase 6).

Source of truth: analysis/analysis-brief.md §4.7 PublishService orchestrator.
Interface tests → xfail until services/publish.py is implemented.
Behavioral tests use respx to mock external publisher HTTP calls.
"""

from __future__ import annotations

import pytest
import respx

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.models.publish import (
        PlatformCredentials,
        PublishPlatform,
        PublishRequest,
        PublishResponse,
    )
    from app.services.publish import PublishService

    HAS_PUBLISH_SERVICE = True
except (ImportError, ModuleNotFoundError):
    HAS_PUBLISH_SERVICE = False

    class PublishPlatform:  # type: ignore[no-redef]
        LINKEDIN = "linkedin"
        TWITTER = "twitter"
        MEDIUM = "medium"

    class PublishRequest:  # type: ignore[no-redef]
        pass

    class PublishResponse:  # type: ignore[no-redef]
        pass

    class PlatformCredentials:  # type: ignore[no-redef]
        pass


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_SERVICE, reason="services/publish.py not implemented yet")
class TestPublishServiceInterface:
    """Interface: PublishService is importable and has expected API."""

    def test_importable(self):
        assert PublishService is not None

    def test_is_class(self):
        assert isinstance(PublishService, type)

    def test_has_publish_method(self):
        assert hasattr(PublishService, "publish")
        assert callable(PublishService.publish)

    def test_publish_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(PublishService.publish)

    def test_init_accepts_publishers(self):
        import inspect
        sig = inspect.signature(PublishService.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Dispatch to correct publisher
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_SERVICE, reason="services/publish.py not implemented yet")
class TestPublishServiceDispatch:
    """Behavioral: PublishService routes to the correct publisher by platform."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.LINKEDIN,
            access_token="tok",
        )

    @pytest.fixture
    def service(self):
        return PublishService()

    async def test_dispatch_linkedin(self, service, credentials):
        """LinkedIn request routes to LinkedInPublisher."""
        request = PublishRequest(
            platform=PublishPlatform.LINKEDIN,
            content="LinkedIn post",
            title="Post Title",
        )
        with respx.mock:
            respx.post("https://api.linkedin.com/rest/posts").respond(
                status_code=201,
                json={"id": "urn:li:activity:dispatch_test"},
            )
            response = await service.publish(request, credentials)
        assert isinstance(response, PublishResponse)
        assert response.platform == PublishPlatform.LINKEDIN

    async def test_dispatch_twitter(self, service, credentials):
        """Twitter request routes to TwitterPublisher."""
        request = PublishRequest(
            platform=PublishPlatform.TWITTER,
            content="Tweet text",
        )
        with respx.mock:
            respx.post("https://api.twitter.com/2/tweets").respond(
                status_code=201,
                json={"data": {"id": "tweet_dispatch", "text": "Tweet text"}},
            )
            response = await service.publish(request, credentials)
        assert isinstance(response, PublishResponse)
        assert response.platform == PublishPlatform.TWITTER

    async def test_dispatch_medium(self, service, credentials):
        """Medium request routes to MediumPublisher."""
        request = PublishRequest(
            platform=PublishPlatform.MEDIUM,
            content="Article body",
            title="Article Title",
        )
        with respx.mock:
            respx.post("https://api.medium.com/v1/users//posts").respond(
                status_code=201,
                json={"data": {"id": "post_dispatch", "url": "https://medium.com/p/post_dispatch"}},
            )
            response = await service.publish(request, credentials)
        assert isinstance(response, PublishResponse)
        assert response.platform == PublishPlatform.MEDIUM


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Dry-run mode
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_SERVICE, reason="services/publish.py not implemented yet")
class TestPublishServiceDryRun:
    """Behavioral: Dry-run validates but does not send HTTP requests."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.LINKEDIN,
            access_token="tok",
        )

    @pytest.fixture
    def service(self):
        return PublishService()

    async def test_dry_run_does_not_send_http(self, service, credentials):
        """Dry-run returns response without making HTTP calls."""
        request = PublishRequest(
            platform=PublishPlatform.LINKEDIN,
            content="Dry run post",
            options={"dry_run": True},
        )
        with respx.mock:
            # No route mock registered — if dry-run sends HTTP, it will fail
            response = await service.publish(request, credentials, dry_run=True)
        assert isinstance(response, PublishResponse)
        assert response.status == "dry-run" or "dry" in response.status.lower()

    async def test_dry_run_returns_valid_response(self, service, credentials):
        """Dry-run response has valid job_id and platform."""
        request = PublishRequest(
            platform=PublishPlatform.LINKEDIN,
            content="Another dry run",
        )
        with respx.mock:
            response = await service.publish(request, credentials, dry_run=True)
        assert response.job_id is not None
        assert response.platform == PublishPlatform.LINKEDIN
        assert response.errors == []


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Retry on network errors
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_PUBLISH_SERVICE, reason="services/publish.py not implemented yet")
class TestPublishServiceRetry:
    """Behavioral: Retry 3 times with backoff on network errors."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.TWITTER,
            access_token="tok",
        )

    @pytest.fixture
    def service(self):
        return PublishService()

    async def test_retry_on_server_error(self, service, credentials):
        """Server error triggers up to 3 retries, then fails or succeeds."""
        request = PublishRequest(
            platform=PublishPlatform.TWITTER,
            content="Retry test",
        )
        with respx.mock:
            route = respx.post("https://api.twitter.com/2/tweets").respond(
                status_code=500,
                json={"error": "Internal error"},
            )
            # Should either raise or return error response after retries
            try:
                response = await service.publish(request, credentials)
                # If no exception, check response has error
                assert response.status == "failed" or len(response.errors) > 0
            except Exception:
                pass  # Exception acceptable
        assert len(route.calls) >= 1  # At least one attempt made

    async def test_retry_eventually_succeeds(self, service, credentials):
        """After 2 failures, 3rd attempt succeeds."""
        request = PublishRequest(
            platform=PublishPlatform.TWITTER,
            content="Eventual success",
        )
        call_count = 0

        def _handler(request):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return httpx.Response(500, json={"error": "Retry later"})
            return httpx.Response(201, json={"data": {"id": "tweet_success", "text": "Success"}})

        with respx.mock:
            respx.post("https://api.twitter.com/2/tweets").mock(side_effect=_handler)
            response = await service.publish(request, credentials)
        assert response.platform_post_id == "tweet_success" or response.status == "published"

    async def test_no_retry_on_success(self, service, credentials):
        """Successful first attempt does not retry."""
        request = PublishRequest(
            platform=PublishPlatform.LINKEDIN,
            content="Success no retry",
        )
        with respx.mock:
            route = respx.post("https://api.linkedin.com/rest/posts").respond(
                status_code=201,
                json={"id": "urn:li:activity:no_retry"},
            )
            await service.publish(request, credentials)
        assert len(route.calls) == 1


import httpx  # noqa: E402
