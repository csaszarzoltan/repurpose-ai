"""WordPress publisher — REST API with OAuth2."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import TYPE_CHECKING
import httpx

if TYPE_CHECKING:
    from app.models.publish import PlatformCredentials

WORDPRESS_API = "/wp-json/wp/v2"
MAX_RETRIES = 3


class WordPressPublisher:
    """Publish content to WordPress via the REST API.

    Handles draft/publish/schedule status, OAuth2 token refresh,
    category/tag mapping, and featured image uploads.
    Supports auto-refresh on 401 and exponential backoff on 429/5xx.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._http = http_client or httpx.AsyncClient()

    async def create_post(
        self,
        credentials: PlatformCredentials,
        content: str,
        title: str | None = None,
        status: str = "draft",
        categories: list[int] | None = None,
        tags: list[int] | None = None,
        featured_media: str | None = None,
    ) -> dict:
        """Create a WordPress post.

        Builds a WordPress REST API payload and posts to /wp-json/wp/v2/posts.
        Retries on 401 (token refresh), 429 (backoff), and 5xx (server errors).
        """
        raise NotImplementedError("WordPressPublisher.create_post not implemented")

    async def authenticate(
        self,
        credentials: PlatformCredentials,
    ) -> PlatformCredentials:
        """Authenticate via OAuth2 and return refreshed credentials."""
        raise NotImplementedError("WordPressPublisher.authenticate not implemented")

    async def upload_image(
        self,
        credentials: PlatformCredentials,
        image_url: str,
        alt_text: str = "",
    ) -> dict:
        """Upload an image to WordPress media library and return attachment data."""
        raise NotImplementedError("WordPressPublisher.upload_image not implemented")

    async def refresh_token(self, creds: PlatformCredentials) -> None:
        """Refresh the OAuth2 access token."""
        raise NotImplementedError("WordPressPublisher.refresh_token not implemented")

    @staticmethod
    def _get_retry_after(response: httpx.Response) -> float:
        retry_header = response.headers.get("Retry-After", "1")
        try:
            return float(retry_header)
        except (ValueError, TypeError):
            return 1.0
