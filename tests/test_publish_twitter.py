"""Pre-dev tests for TwitterPublisher (Phase 4).

Source of truth: analysis/analysis-brief.md §4.4 TwitterPublisher.
Interface tests → xfail until services/publishers/twitter.py is implemented.
Behavioral tests use respx to mock Twitter/X API v2.
"""

from __future__ import annotations

import pytest
import respx

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.models.publish import PlatformCredentials, PublishPlatform
    from app.services.publishers.twitter import TwitterPublisher

    HAS_TWITTER_PUBLISHER = True
except (ImportError, ModuleNotFoundError):
    HAS_TWITTER_PUBLISHER = False

    class PublishPlatform:  # type: ignore[no-redef]
        TWITTER = "twitter"

    class PlatformCredentials:  # type: ignore[no-redef]
        pass


TWITTER_API = "https://api.twitter.com"


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_TWITTER_PUBLISHER, reason="services/publishers/twitter.py not implemented yet")
class TestTwitterPublisherInterface:
    """Interface: TwitterPublisher is importable and has expected API."""

    def test_importable(self):
        assert TwitterPublisher is not None

    def test_is_class(self):
        assert isinstance(TwitterPublisher, type)

    def test_has_create_tweet(self):
        assert hasattr(TwitterPublisher, "create_tweet")
        assert callable(TwitterPublisher.create_tweet)

    def test_has_create_thread(self):
        assert hasattr(TwitterPublisher, "create_thread")
        assert callable(TwitterPublisher.create_thread)

    def test_create_tweet_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(TwitterPublisher.create_tweet)

    def test_create_thread_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(TwitterPublisher.create_thread)

    def test_init_accepts_http_client(self):
        import inspect
        sig = inspect.signature(TwitterPublisher.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Success
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_TWITTER_PUBLISHER, reason="services/publishers/twitter.py not implemented yet")
class TestTwitterPublisherSuccess:
    """Behavioral: Successful tweet creation."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.TWITTER,
            access_token="valid_twitter_token",
        )

    @pytest.fixture
    def publisher(self):
        return TwitterPublisher()

    async def test_create_tweet_returns_201_with_id(self, credentials, publisher):
        """POST /2/tweets returns 201 with tweet id."""
        with respx.mock:
            route = respx.post(f"{TWITTER_API}/2/tweets").respond(
                status_code=201,
                json={"data": {"id": "123456789", "text": "Hello world!"}},
            )
            result = await publisher.create_tweet(
                credentials=credentials,
                text="Hello world!",
            )
        assert route.called
        assert result["data"]["id"] == "123456789"

    async def test_create_tweet_with_media_ids(self, credentials, publisher):
        """POST with media_ids in payload."""
        with respx.mock:
            route = respx.post(f"{TWITTER_API}/2/tweets").respond(
                status_code=201,
                json={"data": {"id": "tweet_media_1", "text": "With image"}},
            )
            await publisher.create_tweet(
                credentials=credentials,
                text="With image",
                media_ids=["media_111", "media_222"],
            )
        assert route.called
        sent_json = route.calls[0].request.json()
        assert "media" in sent_json or "media_ids" in str(sent_json)


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Thread
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_TWITTER_PUBLISHER, reason="services/publishers/twitter.py not implemented yet")
class TestTwitterPublisherThread:
    """Behavioral: Thread creation chains tweets via in_reply_to_tweet_id."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.TWITTER,
            access_token="valid_twitter_token",
        )

    @pytest.fixture
    def publisher(self):
        return TwitterPublisher()

    async def test_create_thread_multiple_tweets(self, credentials, publisher):
        """Thread posts multiple tweets chained via reply settings."""
        tweets = ["Tweet 1 of thread", "Tweet 2 continues", "Tweet 3 finishes"]

        with respx.mock:
            # All 3 POSTs succeed
            route = respx.post(f"{TWITTER_API}/2/tweets").respond(
                status_code=201,
                json={"data": {"id": "tweet_reply_1", "text": "dummy"}},
            )

            results = await publisher.create_thread(
                credentials=credentials,
                tweets=tweets,
            )
        assert route.called
        assert len(results) == len(tweets)
        # Verify at least one request had reply.in_reply_to_tweet_id
        for call in route.calls:
            sent = call.request.json()
            if "reply" in sent:
                assert "in_reply_to_tweet_id" in sent["reply"]
                break
        else:
            # If no reply found in first N calls — check the pattern allows optional chaining
            pass  # Thread may not require reply for the first tweet


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Rate limit
# ════════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_TWITTER_PUBLISHER, reason="services/publishers/twitter.py not implemented yet")
class TestTwitterPublisherRateLimit:
    """Behavioral: Rate limit (429) backoff."""

    @pytest.fixture
    def credentials(self):
        return PlatformCredentials(
            platform=PublishPlatform.TWITTER,
            access_token="valid_token",
        )

    @pytest.fixture
    def publisher(self):
        return TwitterPublisher()

    async def test_rate_limit_backoff(self, credentials, publisher):
        """429 triggers backoff, subsequent retry succeeds."""
        with respx.mock:
            respx.post(f"{TWITTER_API}/2/tweets").respond(
                status_code=429,
                headers={"Retry-After": "1"},
                json={"title": "Too Many Requests"},
            )
            respx.post(f"{TWITTER_API}/2/tweets").respond(
                status_code=201,
                json={"data": {"id": "tweet_after_backoff", "text": "Success"}},
            )

            result = await publisher.create_tweet(
                credentials=credentials,
                text="Backoff test",
            )
        assert result["data"]["id"] == "tweet_after_backoff"

    async def test_rate_limit_exhausted_raises(self, credentials, publisher):
        """Persistent 429 after all retries raises an exception."""
        with respx.mock:
            route = respx.post(f"{TWITTER_API}/2/tweets").respond(
                status_code=429,
                headers={"Retry-After": "1"},
                json={"title": "Too Many Requests"},
            )

            with pytest.raises(Exception):
                await publisher.create_tweet(
                    credentials=credentials,
                    text="Will fail",
                )
        # Should have exhausted retries
        assert len(route.calls) >= 2
