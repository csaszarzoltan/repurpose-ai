"""PublishService orchestrator — routes requests to the correct publisher."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from uuid import uuid4

from app.models.publish import PublishPlatform, PublishRequest, PublishResponse

if TYPE_CHECKING:
    from app.models.publish import PlatformCredentials
    from app.services.publishers.ghost import GhostPublisher
    from app.services.publishers.instagram import InstagramPublisher
    from app.services.publishers.linkedin import LinkedInPublisher
    from app.services.publishers.medium import MediumPublisher
    from app.services.publishers.twitter import TwitterPublisher
    from app.services.publishers.wordpress import WordPressPublisher
    from app.services.rate_limiter import RateLimiter

MAX_RETRIES = 3


class PublishService:
    """Orchestrates multi-platform publishing.

    Receives a PublishRequest, routes to the correct publisher,
    handles dry-run, and retries on network/server errors.
    """

    def __init__(
        self,
        rate_limiter: RateLimiter | None = None,
        linkedin: LinkedInPublisher | None = None,
        twitter: TwitterPublisher | None = None,
        medium: MediumPublisher | None = None,
        instagram: InstagramPublisher | None = None,
        wordpress: WordPressPublisher | None = None,
        ghost: GhostPublisher | None = None,
    ) -> None:
        self._rate_limiter = rate_limiter
        self._linkedin = linkedin
        self._twitter = twitter
        self._medium = medium
        self._instagram = instagram
        self._wordpress = wordpress
        self._ghost = ghost
        self._results: dict[str, PublishResponse] = {}

    async def publish(
        self,
        request: PublishRequest,
        credentials: PlatformCredentials,
        dry_run: bool = False,
    ) -> PublishResponse:
        """Execute a publish request.

        In dry-run mode the request is validated and a response is returned
        without making any HTTP calls. Otherwise the request is dispatched
        to the appropriate platform publisher with retry logic.
        """
        job_id = str(uuid4())
        response = PublishResponse(
            job_id=job_id,
            platform=request.platform,
            status="queued",
        )

        if dry_run:
            response.status = "dry-run"
            self._results[job_id] = response
            return response

        try:
            result = await self._dispatch(request, credentials)
            response.status = "published"
            response.platform_post_id = self._extract_post_id(request.platform, result)
            response.errors = []
        except Exception as exc:
            response.status = "failed"
            response.errors = [str(exc)]

        self._results[job_id] = response
        return response

    def get_result(self, job_id: str) -> PublishResponse | None:
        """Retrieve a previous publish result by job_id."""
        return self._results.get(job_id)

    # ── Dispatch ────────────────────────────────────────────────────────────

    async def _dispatch(self, request: PublishRequest, credentials: PlatformCredentials) -> dict:
        """Route to the correct publisher with retry logic."""
        last_exception: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                return await self._publish_to_platform(request, credentials)
            except Exception as exc:
                last_exception = exc
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                raise

        raise last_exception or Exception("Publish failed")

    async def _publish_to_platform(self, request: PublishRequest, credentials: PlatformCredentials) -> dict:
        """Call the appropriate publisher for the request platform."""
        if request.platform == PublishPlatform.LINKEDIN:
            if self._linkedin is None:
                from app.services.publishers.linkedin import LinkedInPublisher

                self._linkedin = LinkedInPublisher()
            return await self._linkedin.create_post(
                credentials=credentials,
                content=request.content,
                title=request.title,
            )

        if request.platform == PublishPlatform.TWITTER:
            if self._twitter is None:
                from app.services.publishers.twitter import TwitterPublisher

                self._twitter = TwitterPublisher()
            return await self._twitter.create_tweet(
                credentials=credentials,
                text=request.content,
                media_ids=request.media_urls or None,
            )

        if request.platform == PublishPlatform.MEDIUM:
            if self._medium is None:
                from app.services.publishers.medium import MediumPublisher

                self._medium = MediumPublisher()
            return await self._medium.create_article(
                credentials=credentials,
                title=request.title or "",
                content=request.content,
            )

        if request.platform == PublishPlatform.INSTAGRAM:
            if self._instagram is None:
                from app.services.publishers.instagram import InstagramPublisher

                self._instagram = InstagramPublisher()
            return await self._instagram.publish(
                credentials=credentials,
                image_url=request.media_urls[0] if request.media_urls else None,
                video_url=request.options.get("video_url"),
                media_type=request.options.get("media_type"),
                children=request.options.get("children"),
                caption=request.content,
            )

        if request.platform == PublishPlatform.WORDPRESS:
            if self._wordpress is None:
                from app.services.publishers.wordpress import WordPressPublisher

                self._wordpress = WordPressPublisher()
            return await self._wordpress.create_post(
                credentials=credentials,
                content=request.content,
                title=request.title,
                status=request.options.get("status", "draft"),
                categories=request.options.get("categories"),
                tags=request.options.get("tags"),
                featured_media=request.options.get("featured_media"),
                excerpt=request.options.get("excerpt"),
            )

        if request.platform == PublishPlatform.GHOST:
            if self._ghost is None:
                from app.services.publishers.ghost import GhostPublisher

                self._ghost = GhostPublisher()
            return await self._ghost.create_post(
                credentials=credentials,
                title=request.title or "",
                content=request.content,
                status=request.options.get("status", "draft"),
                tags=request.options.get("tags"),
                feature_image=request.options.get("feature_image"),
                mobiledoc=request.options.get("mobiledoc"),
            )

        raise ValueError(f"Unsupported platform: {request.platform}")

    @staticmethod
    def _extract_post_id(platform: PublishPlatform, result: dict) -> str | None:
        """Extract the platform-specific post ID from a publisher result."""
        if platform == PublishPlatform.LINKEDIN:
            return result.get("id")
        if platform == PublishPlatform.TWITTER:
            return result.get("data", {}).get("id")
        if platform == PublishPlatform.MEDIUM:
            return result.get("data", {}).get("id")
        if platform == PublishPlatform.INSTAGRAM:
            return result.get("id")
        if platform == PublishPlatform.WORDPRESS:
            return result.get("id")
        if platform == PublishPlatform.GHOST:
            posts = result.get("posts", [])
            if posts:
                return posts[0].get("id")
        return None
