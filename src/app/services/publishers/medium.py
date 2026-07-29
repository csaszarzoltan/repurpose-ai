"""Medium publisher — API v1."""
from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from app.models.publish import PlatformCredentials

MEDIUM_API = "https://api.medium.com"


class MediumPublisher:
    """Publish articles to Medium via the Medium API v1.

    Supports user posts and publication posts with markdown content format.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._http = http_client or httpx.AsyncClient()

    async def create_article(
        self,
        credentials: PlatformCredentials,
        title: str,
        content: str,
        content_format: str = "markdown",
        publish_status: str = "draft",
        publication_id: str | None = None,
    ) -> dict:
        """Create a Medium article.

        If ``publication_id`` is provided the article is posted to that
        publication's endpoint; otherwise it is posted to the user's
        personal posts endpoint.
        """
        headers = self._build_headers(credentials.access_token)
        payload: dict = {
            "title": title,
            "contentFormat": content_format,
            "content": content,
            "publishStatus": publish_status,
        }

        if publication_id:
            url = f"{MEDIUM_API}/v1/publications/{publication_id}/posts"
        else:
            user_id = credentials.platform_user_id or ""
            url = f"{MEDIUM_API}/v1/users/{user_id}/posts"

        response = await self._http.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _build_headers(access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
