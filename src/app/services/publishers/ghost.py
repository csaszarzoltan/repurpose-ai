"""Ghost publisher — Admin API with API key auth."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import TYPE_CHECKING
import httpx

if TYPE_CHECKING:
    from app.models.publish import PlatformCredentials

GHOST_ADMIN_API = "/ghost/api/admin"
MAX_RETRIES = 3


class GhostPublisher:
    """Publish content to Ghost CMS via the Admin API.

    Handles API key authentication (HMAC JWT), tag mapping,
    Mobiledoc content formatting, and featured images.
    Supports exponential backoff on 429/5xx.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._http = http_client or httpx.AsyncClient()

    async def create_post(
        self,
        credentials: PlatformCredentials,
        title: str,
        content: str,
        status: str = "draft",
        tags: list[dict[str, str]] | None = None,
        feature_image: str | None = None,
        mobiledoc: str | None = None,
    ) -> dict:
        """Create a Ghost post.

        Builds a Ghost Admin API payload and posts to /ghost/api/admin/posts/.
        The content is formatted as Mobiledoc by default.
        """
        raise NotImplementedError("GhostPublisher.create_post not implemented")

    async def authenticate(
        self,
        credentials: PlatformCredentials,
    ) -> str:
        """Generate a JWT from the Ghost Admin API key for authentication."""
        raise NotImplementedError("GhostPublisher.authenticate not implemented")

    async def upload_image(
        self,
        credentials: PlatformCredentials,
        image_url: str,
        ref: str = "",
    ) -> dict:
        """Upload an image to Ghost media library."""
        raise NotImplementedError("GhostPublisher.upload_image not implemented")

    async def _build_jwt(self, api_key: str) -> str:
        """Build a signed JWT from the Ghost Admin API key."""
        raise NotImplementedError("GhostPublisher._build_jwt not implemented")

    @staticmethod
    def _format_mobiledoc(content: str) -> str:
        """Convert markdown/HTML content to Mobiledoc format."""
        raise NotImplementedError("GhostPublisher._format_mobiledoc not implemented")

    @staticmethod
    def _get_retry_after(response: httpx.Response) -> float:
        retry_header = response.headers.get("Retry-After", "1")
        try:
            return float(retry_header)
        except (ValueError, TypeError):
            return 1.0
