"""Instagram publisher — Meta Graph API v19.0 (container-based publishing).

Pre-development stub (TDD RED phase). All publishing methods raise
NotImplementedError until the developer implements the Instagram Graph API
container flow:

  1. Single image: POST /{ig-user-id}/media -> POST /{ig-user-id}/media_publish
  2. Carousel: create per-item containers, then a CAROUSEL container, then publish
  3. Reel: POST /{ig-user-id}/media with REELS media_type, poll status, then publish

Contract pinned by tests/test_publish_instagram.py (interface tests must pass
immediately; behavioral tests fail with NotImplementedError until implemented).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from app.models.publish import PlatformCredentials

GRAPH_API = "https://graph.facebook.com/v19.0"
MAX_RETRIES = 3


class InstagramPublisher:
    """Publish content to Instagram via the Meta Graph API v19.0.

    Uses the container-based publishing flow: media is first uploaded by
    creating a container (POST /{ig-user-id}/media), then the container is
    published (POST /{ig-user-id}/media_publish). Supports single images,
    carousels, and reels.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._http = http_client or httpx.AsyncClient()

    async def publish(
        self,
        credentials: PlatformCredentials,
        *,
        image_url: str | None = None,
        video_url: str | None = None,
        media_type: str | None = None,
        children: list[dict[str, Any]] | None = None,
        caption: str | None = None,
    ) -> dict:
        """Publish content to Instagram.

        Creates one or more media containers, then publishes the final
        container. ``media_type`` selects the flow:

        * ``IMAGE`` (default) — single image container + publish
        * ``CAROUSEL`` — per-item containers, carousel container, publish
        * ``REELS`` — video container with ``REELS`` media type, status
          polling, then publish

        Returns the media_publish response (contains the published media id).
        """
        raise NotImplementedError

    async def refresh_token(self, credentials: PlatformCredentials) -> str:
        """Refresh an expired access token via the Facebook Graph API.

        Calls the Graph API OAuth token endpoint and returns the fresh
        access token string.
        """
        raise NotImplementedError

    async def build_container(
        self,
        credentials: PlatformCredentials,
        payload: dict[str, Any],
    ) -> str:
        """Create a media container via POST /{ig-user-id}/media.

        Returns the container id from the Graph API response.
        """
        raise NotImplementedError

    async def publish_container(
        self,
        credentials: PlatformCredentials,
        creation_id: str,
    ) -> dict:
        """Publish a created container via POST /{ig-user-id}/media_publish.

        Returns the media_publish response dict.
        """
        raise NotImplementedError
