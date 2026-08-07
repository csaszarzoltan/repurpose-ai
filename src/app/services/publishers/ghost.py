"""Ghost publisher — Admin API with API key auth."""
from __future__ import annotations

import asyncio
import time
from copy import deepcopy
from typing import TYPE_CHECKING

import httpx
import jwt

if TYPE_CHECKING:
    from app.models.publish import PlatformCredentials

GHOST_ADMIN_API = "https://ghost.example.com/ghost/api/admin"
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
        The content is formatted as Mobiledoc by default unless ``mobiledoc``
        is supplied. Retries on 401 (JWT regeneration), 429 (backoff), and
        5xx (server errors).
        """
        creds = deepcopy(credentials)
        api_key = creds.access_token
        jwt_token = await self._build_jwt(api_key)
        post_content = mobiledoc or self._format_mobiledoc(content)

        for attempt in range(MAX_RETRIES + 1):
            headers = self._build_headers(jwt_token)
            payload = self._build_payload(
                title=title,
                content=post_content,
                status=status,
                tags=tags,
                feature_image=feature_image,
            )

            response = await self._http.post(
                f"{GHOST_ADMIN_API}/posts/",
                headers=headers,
                json=payload,
            )

            if response.status_code == 201:
                return response.json()

            if response.status_code == 401 and attempt == 0:
                # Regenerate the JWT (token may have expired) and retry once
                jwt_token = await self._build_jwt(api_key)
                continue

            if response.status_code == 429:
                retry_after = self._get_retry_after(response)
                await asyncio.sleep(retry_after)
                continue

            if response.status_code >= 500 and attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (2**attempt))
                continue

            response.raise_for_status()

        raise Exception(f"Ghost post failed after {MAX_RETRIES + 1} attempts")

    async def authenticate(
        self,
        credentials: PlatformCredentials,
    ) -> str:
        """Generate a JWT from the Ghost Admin API key for authentication."""
        return await self._build_jwt(credentials.access_token)

    async def upload_image(
        self,
        credentials: PlatformCredentials,
        image_url: str,
        ref: str = "",
    ) -> dict:
        """Upload an image to the Ghost media library.

        Posts a multipart file to /ghost/api/admin/images/upload and returns
        the created image reference. Retries on 401, 429, and 5xx.
        """
        creds = deepcopy(credentials)
        jwt_token = await self._build_jwt(creds.access_token)

        for attempt in range(MAX_RETRIES + 1):
            headers = self._build_headers(jwt_token)
            files = {
                "file": (ref or "image.jpg", image_url.encode("utf-8"), "image/jpeg"),
            }

            response = await self._http.post(
                f"{GHOST_ADMIN_API}/images/upload",
                headers=headers,
                files=files,
            )

            if response.status_code == 201:
                return response.json()

            if response.status_code == 401 and attempt == 0:
                jwt_token = await self._build_jwt(creds.access_token)
                continue

            if response.status_code == 429:
                retry_after = self._get_retry_after(response)
                await asyncio.sleep(retry_after)
                continue

            if response.status_code >= 500 and attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (2**attempt))
                continue

            response.raise_for_status()

        raise Exception(f"Ghost image upload failed after {MAX_RETRIES + 1} attempts")

    async def _build_jwt(self, api_key: str) -> str:
        """Build a signed JWT from the Ghost Admin API key.

        The Admin API key is ``<key_id>:<secret>`` where the secret is a hex
        string. Falls back to the raw UTF-8 secret bytes when the secret is
        not valid hex (e.g. test fixtures), so the token is always signed.
        """
        try:
            key_id, secret = api_key.split(":")
        except ValueError:
            raise ValueError("Invalid Ghost Admin API key format. Expected 'id:secret'") from None

        import binascii

        try:
            secret_bytes = binascii.unhexlify(secret)
        except (binascii.Error, ValueError):
            secret_bytes = secret.encode("utf-8")

        payload = {
            "iat": int(time.time()),
            "exp": int(time.time()) + 300,  # 5 minutes
            "aud": "/admin/",
        }

        return jwt.encode(payload, secret_bytes, algorithm="HS256", headers={"kid": key_id})

    @staticmethod
    def _format_mobiledoc(content: str) -> str:
        """Convert markdown/HTML content to Mobiledoc format."""
        import json

        mobiledoc = {
            "version": "0.3.1",
            "markups": [],
            "atoms": [],
            "cards": [["markdown", {"markdown": content}]],
            "sections": [[10, 0]],
        }

        return json.dumps(mobiledoc)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _build_headers(self, jwt_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Ghost {jwt_token}",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        title: str,
        content: str,
        status: str = "draft",
        tags: list[dict[str, str]] | None = None,
        feature_image: str | None = None,
    ) -> dict:
        post: dict = {
            "title": title,
            "mobiledoc": content,
            "status": status,
        }

        if tags:
            post["tags"] = tags

        if feature_image:
            post["feature_image"] = feature_image

        return {"posts": [post]}

    @staticmethod
    def _get_retry_after(response: httpx.Response) -> float:
        retry_header = response.headers.get("Retry-After", "1")
        try:
            return float(retry_header)
        except (ValueError, TypeError):
            return 1.0
