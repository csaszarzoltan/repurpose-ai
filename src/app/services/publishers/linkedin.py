"""LinkedIn publisher — Posts API (REST)."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from app.models.publish import PlatformCredentials

LINKEDIN_API = "https://api.linkedin.com"
MAX_RETRIES = 3


class LinkedInPublisher:
    """Publish content to LinkedIn via the LinkedIn Posts API.

    Handles text commentary, article links, and image posts.
    Supports auto-refresh on 401 and exponential backoff on 429/5xx.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._http = http_client or httpx.AsyncClient()

    async def create_post(
        self,
        credentials: PlatformCredentials,
        content: str,
        title: str | None = None,
        media_url: str | None = None,
        image_urn: str | None = None,
    ) -> dict:
        """Create a LinkedIn post.

        Builds a LinkedIn Posts API payload and posts to /rest/posts.
        Retries on 401 (token refresh), 429 (backoff), and 5xx (server errors).
        """
        creds = deepcopy(credentials)

        for attempt in range(MAX_RETRIES + 1):
            headers = self._build_headers(creds.access_token)
            payload = self._build_payload(content, title, media_url, image_urn)

            response = await self._http.post(
                f"{LINKEDIN_API}/rest/posts",
                headers=headers,
                json=payload,
            )

            if response.status_code == 201:
                return response.json()

            if response.status_code == 401 and creds.refresh_token and attempt == 0:
                # Try to refresh the token
                await self._refresh_token(creds)
                continue

            if response.status_code == 429:
                retry_after = self._get_retry_after(response)
                await asyncio.sleep(retry_after)
                continue

            if response.status_code >= 500 and attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (2**attempt))
                continue

            response.raise_for_status()

        raise Exception(f"LinkedIn post failed after {MAX_RETRIES + 1} attempts")

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _build_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202304",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        content: str,
        title: str | None = None,
        media_url: str | None = None,
        image_urn: str | None = None,
    ) -> dict:
        payload: dict = {
            "author": "urn:li:person:unknown",
            "commentary": content,
            "visibility": "PUBLIC",
            "lifecycleState": "PUBLISHED",
        }

        # Article content
        if media_url:
            payload["content"] = {
                "article": {
                    "source": media_url,
                    "title": title or "",
                    "description": content[:200],
                }
            }

        # Image content
        if image_urn:
            if "content" not in payload:
                payload["content"] = {}
            payload["content"]["media"] = {
                "id": image_urn,
            }

        return payload

    async def _refresh_token(self, creds: PlatformCredentials) -> None:
        """Refresh the access token via the OAuth2 token endpoint."""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": creds.refresh_token or "",
            "client_id": "linkedin_client_id",
            "client_secret": "client_secret_placeholder",
        }
        resp = await self._http.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data=data,
        )
        resp.raise_for_status()
        body = resp.json()
        creds.access_token = body["access_token"]

    @staticmethod
    def _get_retry_after(response: httpx.Response) -> float:
        retry_header = response.headers.get("Retry-After", "1")
        try:
            return float(retry_header)
        except (ValueError, TypeError):
            return 1.0
