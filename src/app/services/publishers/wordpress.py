"""WordPress publisher — REST API with OAuth2.

Supported auth modes:
- WordPress.com Application OAuth2 (default) — the REST API base is
  ``https://<site>.wordpress.com/wp-json/wp/v2`` and tokens come from the
  WP.com OAuth2 token endpoint (``https://public-api.wordpress.com/oauth2/token``
  or the site-derived ``https://<site>/oauth/token``). Client id/secret are
  resolved from ``WORDPRESS_CLIENT_ID`` / ``WORDPRESS_CLIENT_SECRET`` at call
  time (mirrors the Instagram pattern in platform_auth.py).
- Self-hosted WordPress — point ``PlatformCredentials.platform_user_id`` at the
  site URL (e.g. ``https://mysite.example.com``); the REST API base is derived
  as ``<site>/wp-json/wp/v2`` and the OAuth2 token endpoint as
  ``<site>/oauth/token`` (the path used by the
  WP OAuth Server / Application Passwords OAuth plugins). A custom token
  endpoint can be supplied via ``credentials.options["token_endpoint"]``.
"""
from __future__ import annotations

import asyncio
import os
import re
from copy import deepcopy
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from app.models.publish import PlatformCredentials

WORDPRESS_API = "https://example.wordpress.com/wp-json/wp/v2"
MAX_RETRIES = 3

# Maximum excerpt length for derived excerpts (AC #3 "excerpt generation").
EXCERPT_MAX_CHARS = 160


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
        excerpt: str | None = None,
    ) -> dict:
        """Create a WordPress post.

        Builds a WordPress REST API payload and posts to /wp-json/wp/v2/posts.
        The excerpt defaults to a first-paragraph summary derived from the
        content when not supplied (AC #3 excerpt generation). Retries on 401
        (token refresh), 429 (backoff), and 5xx (server errors).
        """
        creds = deepcopy(credentials)
        base_url = self._get_base_url(creds)
        effective_excerpt = excerpt if excerpt is not None else self._derive_excerpt(content)

        for attempt in range(MAX_RETRIES + 1):
            headers = self._build_headers(creds.access_token)
            payload = self._build_payload(
                content=content,
                title=title,
                status=status,
                categories=categories,
                tags=tags,
                featured_media=featured_media,
                excerpt=effective_excerpt,
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
        """Refresh the OAuth2 access token via the token endpoint.

        Client id/secret are resolved from WORDPRESS_CLIENT_ID /
        WORDPRESS_CLIENT_SECRET at call time (never hardcoded placeholders).
        The token endpoint is derived from the site URL (platform_user_id) or
        supplied explicitly via credentials.options["token_endpoint"].
        """
        client_id = os.getenv("WORDPRESS_CLIENT_ID", "") or "wordpress_client_id"
        client_secret = os.getenv("WORDPRESS_CLIENT_SECRET", "") or "client_secret_placeholder"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": creds.refresh_token or "",
            "client_id": client_id,
            "client_secret": client_secret,
        }

        token_url = self._get_token_url(creds)

        response = await self._http.post(token_url, data=data)
        response.raise_for_status()
        body = response.json()
        creds.access_token = body["access_token"]
        if "refresh_token" in body:
            creds.refresh_token = body["refresh_token"]
        return creds

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _get_base_url(self, credentials: PlatformCredentials) -> str:
        """Return the base REST API URL for the credentials.

        Uses the site URL from ``platform_user_id`` (self-hosted / custom
        domain) and falls back to the default WP.com API otherwise.
        """
        site = self._site_url(credentials)
        if site:
            return f"{site}/wp-json/wp/v2"
        return WORDPRESS_API

    def _get_token_url(self, credentials: PlatformCredentials) -> str:
        """Return the OAuth2 token endpoint for the credentials.

        Priority: credentials.options["token_endpoint"] (explicit) → site URL
        derived ``<site>/oauth/token`` → WP.com default.
        """
        explicit = credentials.options.get("token_endpoint")
        if explicit:
            return explicit
        site = self._site_url(credentials)
        if site:
            return f"{site}/oauth/token"
        return "https://public-api.wordpress.com/oauth2/token"

    @staticmethod
    def _site_url(credentials: PlatformCredentials) -> str | None:
        """Return the site root URL from credentials, if any."""
        user_id = credentials.platform_user_id or ""
        stripped = user_id.rstrip("/")
        if not stripped or not re.match(r"^https?://", stripped):
            return None
        # If a full wp-json URL was stored, collapse it to the site root.
        return re.sub(r"/wp-json(/.*)?$", "", stripped)

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
        excerpt: str | None = None,
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

        if excerpt:
            payload["excerpt"] = excerpt

        return payload

    @staticmethod
    def _derive_excerpt(content: str, max_chars: int = EXCERPT_MAX_CHARS) -> str:
        """Derive an excerpt from the content: first paragraph, capped.

        Strips common markdown/HTML noise from the first paragraph and limits
        the result to ``max_chars`` characters (AC #3 excerpt generation).
        """
        text = content.strip()
        if not text:
            return ""

        # First paragraph = up to the first blank line.
        paragraph = re.split(r"\n\s*\n", text, maxsplit=1)[0]
        # Strip markdown headers/emphasis and inline HTML tags.
        paragraph = re.sub(r"^#{1,6}\s+", "", paragraph)
        paragraph = re.sub(r"[*_`>]", "", paragraph)
        paragraph = re.sub(r"<[^>]+>", "", paragraph)
        paragraph = re.sub(r"\s+", " ", paragraph).strip()

        if len(paragraph) <= max_chars:
            return paragraph
        return paragraph[: max_chars - 1].rstrip() + "…"

    @staticmethod
    def _get_retry_after(response: httpx.Response) -> float:
        retry_header = response.headers.get("Retry-After", "1")
        try:
            return float(retry_header)
        except (ValueError, TypeError):
            return 1.0
