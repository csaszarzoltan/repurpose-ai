"""WordPress publisher — REST API with OAuth2."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from app.models.publish import PlatformCredentials

WORDPRESS_API = "https://example.wordpress.com/wp-json/wp/v2"
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
        creds = deepcopy(credentials)
        base_url = self._get_base_url(creds)

        for attempt in range(MAX_RETRIES + 1):
            headers = self._build_headers(creds.access_token)
            payload = self._build_payload(
                content=content,
                title=title,
                status=status,
                categories=categories,
                tags=tags,
                featured_media=featured_media,
            )

            response = await self._http.post(
                f"{base_url}/posts",
                headers=headers,
                json=payload,
            )

            if response.status_code == 201:
                return response.json()

            if response.status_code == 401 and creds.refresh_token and attempt == 0:
                # Try to refresh the token
                await self.refresh_token(creds)
                continue

            if response.status_code == 429:
                retry_after = self._get_retry_after(response)
                await asyncio.sleep(retry_after)
                continue

            if response.status_code >= 500 and attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (2**attempt))
                continue

            response.raise_for_status()

        raise Exception(f"WordPress post failed after {MAX_RETRIES + 1} attempts")

    async def authenticate(
        self,
        credentials: PlatformCredentials,
    ) -> PlatformCredentials:
        """Authenticate via OAuth2 and return refreshed credentials."""
        return await self.refresh_token(credentials)

    async def upload_image(
        self,
        credentials: PlatformCredentials,
        image_url: str,
        alt_text: str = "",
    ) -> dict:
        """Upload an image to the WordPress media library.

        Posts to /wp-json/wp/v2/media and returns the attachment data
        (including the media id used as featured_media). Retries on 401
        (token refresh), 429 (backoff), and 5xx (server errors).
        """
        creds = deepcopy(credentials)
        base_url = self._get_base_url(creds)

        for attempt in range(MAX_RETRIES + 1):
            headers = self._build_headers(creds.access_token)
            payload = {
                "source_url": image_url,
                "alt_text": alt_text,
            }

            response = await self._http.post(
                f"{base_url}/media",
                headers=headers,
                json=payload,
            )

            if response.status_code == 201:
                return response.json()

            if response.status_code == 401 and creds.refresh_token and attempt == 0:
                await self.refresh_token(creds)
                continue

            if response.status_code == 429:
                retry_after = self._get_retry_after(response)
                await asyncio.sleep(retry_after)
                continue

            if response.status_code >= 500 and attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (2**attempt))
                continue

            response.raise_for_status()

        raise Exception(f"WordPress image upload failed after {MAX_RETRIES + 1} attempts")

    async def refresh_token(self, creds: PlatformCredentials) -> PlatformCredentials:
        """Refresh the OAuth2 access token via the token endpoint."""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": creds.refresh_token or "",
            "client_id": "wordpress_client_id",
            "client_secret": "client_secret_placeholder",
        }

        base_url = self._get_base_url(creds)
        token_url = base_url.replace("/wp-json/wp/v2", "/oauth/token")

        response = await self._http.post(token_url, data=data)
        response.raise_for_status()
        body = response.json()
        creds.access_token = body["access_token"]
        if "refresh_token" in body:
            creds.refresh_token = body["refresh_token"]
        return creds

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _get_base_url(self, credentials: PlatformCredentials) -> str:
        """Return the base REST API URL for the credentials."""
        return WORDPRESS_API

    def _build_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        content: str,
        title: str | None = None,
        status: str = "draft",
        categories: list[int] | None = None,
        tags: list[int] | None = None,
        featured_media: str | None = None,
    ) -> dict:
        payload: dict = {
            "content": content,
            "status": status,
        }

        if title:
            payload["title"] = title

        if categories:
            payload["categories"] = categories

        if tags:
            payload["tags"] = tags

        if featured_media:
            payload["featured_media"] = featured_media

        return payload

    @staticmethod
    def _get_retry_after(response: httpx.Response) -> float:
        retry_header = response.headers.get("Retry-After", "1")
        try:
            return float(retry_header)
        except (ValueError, TypeError):
            return 1.0
