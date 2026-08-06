"""Instagram publisher — Meta Graph API v19.0 (container-based publishing).

Implements the container-based publishing flow for Instagram:
  1. Single image: POST /{ig-user-id}/media -> POST /{ig-user-id}/media_publish
  2. Carousel: create per-item containers, then a CAROUSEL container, then publish
  3. Reel: POST /{ig-user-id}/media with REELS media_type, poll status, then publish

Token refresh uses Graph API /oauth/access_token with fb_exchange_token grant type.
Error mapping for rate limit, permission scope, and app review required.
OAuth tokens never appear in log output.
"""

from __future__ import annotations

import asyncio
import logging
from copy import deepcopy
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from app.models.publish import PlatformCredentials

logger = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v19.0"
MAX_RETRIES = 3
REEL_POLL_INTERVAL = 2.0  # seconds between status polls


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
        creds = deepcopy(credentials)
        ig_user_id = creds.platform_user_id

        if not ig_user_id:
            raise ValueError("platform_user_id (IG user ID) is required for Instagram publishing")

        mt = (media_type or "IMAGE").upper()

        if mt == "CAROUSEL":
            return await self._publish_carousel(creds, ig_user_id, children or [], caption)

        if mt == "REELS":
            if not video_url:
                raise ValueError("video_url is required for REELS media type")
            return await self._publish_reel(creds, ig_user_id, video_url, caption)

        # Default: single image
        if not image_url:
            raise ValueError("image_url is required for IMAGE media type")
        return await self._publish_single_image(creds, ig_user_id, image_url, caption)

    async def refresh_token(self, credentials: PlatformCredentials) -> str:
        """Refresh an expired access token via the Facebook Graph API.

        Calls the Graph API OAuth token endpoint with fb_exchange_token
        grant type and returns the fresh access token string.
        """
        data = {
            "grant_type": "fb_exchange_token",
            "fb_exchange_token": credentials.access_token,
        }

        response = await self._http.post(
            f"{GRAPH_API}/oauth/access_token",
            data=data,
        )
        response.raise_for_status()
        body = response.json()
        new_token = body.get("access_token")
        if not new_token:
            raise RuntimeError("Token refresh response missing access_token")
        return new_token

    async def build_container(
        self,
        credentials: PlatformCredentials,
        payload: dict[str, Any],
    ) -> str:
        """Create a media container via POST /{ig-user-id}/media.

        Returns the container id from the Graph API response.
        """
        creds = deepcopy(credentials)
        ig_user_id = creds.platform_user_id

        if not ig_user_id:
            raise ValueError("platform_user_id (IG user ID) is required")

        container_payload = {**payload, "access_token": creds.access_token}

        response = await self._http.post(
            f"{GRAPH_API}/{ig_user_id}/media",
            json=container_payload,
        )
        response.raise_for_status()
        body = response.json()
        container_id = body.get("id")
        if not container_id:
            raise RuntimeError("Container creation response missing id")
        return container_id

    async def publish_container(
        self,
        credentials: PlatformCredentials,
        creation_id: str,
    ) -> dict:
        """Publish a created container via POST /{ig-user-id}/media_publish.

        Returns the media_publish response dict.
        """
        creds = deepcopy(credentials)
        ig_user_id = creds.platform_user_id

        if not ig_user_id:
            raise ValueError("platform_user_id (IG user ID) is required")

        publish_payload = {
            "creation_id": creation_id,
            "access_token": creds.access_token,
        }

        response = await self._http.post(
            f"{GRAPH_API}/{ig_user_id}/media_publish",
            json=publish_payload,
        )
        response.raise_for_status()
        return response.json()

    # ── Internal helpers ────────────────────────────────────────────────────

    async def _publish_single_image(
        self,
        credentials: PlatformCredentials,
        ig_user_id: str,
        image_url: str,
        caption: str | None,
    ) -> dict:
        """Single image flow: container -> publish."""
        container_payload = {
            "image_url": image_url,
            "access_token": credentials.access_token,
        }
        if caption:
            container_payload["caption"] = caption

        container_id = await self._create_container(credentials, ig_user_id, container_payload)
        return await self._publish_container_with_retry(credentials, ig_user_id, container_id)

    async def _publish_carousel(
        self,
        credentials: PlatformCredentials,
        ig_user_id: str,
        children: list[dict[str, Any]],
        caption: str | None,
    ) -> dict:
        """Carousel flow: per-item containers -> carousel container -> publish."""
        if len(children) < 2:
            raise ValueError("Carousel requires at least 2 child items")

        # Step 1: Create containers for each child item
        child_container_ids: list[str] = []
        for child in children:
            child_payload = {
                "image_url": child.get("image_url"),
                "access_token": credentials.access_token,
            }
            if "video_url" in child:
                child_payload["video_url"] = child["video_url"]
                child_payload["media_type"] = "REELS"
            elif "media_type" in child:
                child_payload["media_type"] = child["media_type"]
            child_id = await self._create_container(credentials, ig_user_id, child_payload)
            child_container_ids.append(child_id)

        # Step 2: Create carousel container with children references
        carousel_payload = {
            "media_type": "CAROUSEL",
            "children": child_container_ids,
            "access_token": credentials.access_token,
        }
        if caption:
            carousel_payload["caption"] = caption

        carousel_container_id = await self._create_container(credentials, ig_user_id, carousel_payload)

        # Step 3: Publish the carousel container
        return await self._publish_container_with_retry(credentials, ig_user_id, carousel_container_id)

    async def _publish_reel(
        self,
        credentials: PlatformCredentials,
        ig_user_id: str,
        video_url: str,
        caption: str | None,
    ) -> dict:
        """Reel flow: REELS container -> poll status -> publish."""
        container_payload = {
            "media_type": "REELS",
            "video_url": video_url,
            "access_token": credentials.access_token,
        }
        if caption:
            container_payload["caption"] = caption

        container_id = await self._create_container(credentials, ig_user_id, container_payload)

        # Poll container status until FINISHED
        await self._poll_container_status(credentials, container_id)

        return await self._publish_container_with_retry(credentials, ig_user_id, container_id)

    async def _create_container(
        self,
        credentials: PlatformCredentials,
        ig_user_id: str,
        payload: dict[str, Any],
    ) -> str:
        """Create a media container and return its id, with token refresh retry."""
        # Note: access_token already in payload
        creds = deepcopy(credentials)

        for attempt in range(MAX_RETRIES + 1):
            current_payload = {**payload, "access_token": creds.access_token}
            response = await self._http.post(
                f"{GRAPH_API}/{ig_user_id}/media",
                json=current_payload,
            )

            if response.status_code == 200:
                body = response.json()
                # Check for error in 200 response body (Graph API style)
                if "error" in body:
                    error = body["error"]
                    if error.get("code") == 190 and error.get("type") == "OAuthException":
                        logger.info("Instagram token expired during container creation, refreshing...")
                        if creds.refresh_token and attempt == 0:
                            creds.access_token = await self.refresh_token(creds)
                            continue
                # Success - extract container id
                container_id = body.get("id")
                if not container_id:
                    raise RuntimeError("Container creation response missing id")
                return container_id

            # Handle HTTP-level errors
            self._map_graph_error(response)
            response.raise_for_status()

        raise RuntimeError(f"Container creation failed after {MAX_RETRIES + 1} attempts")

    async def _publish_container_with_retry(
        self,
        credentials: PlatformCredentials,
        ig_user_id: str,
        container_id: str,
    ) -> dict:
        """Publish container with token refresh retry on OAuthException code 190."""
        creds = deepcopy(credentials)

        for attempt in range(MAX_RETRIES + 1):
            publish_payload = {
                "creation_id": container_id,
                "access_token": creds.access_token,
            }

            response = await self._http.post(
                f"{GRAPH_API}/{ig_user_id}/media_publish",
                json=publish_payload,
            )

            if response.status_code == 200:
                body = response.json()
                return body

            # Check for expired token (OAuthException code 190)
            try:
                error_body = response.json()
                error = error_body.get("error", {})
                if error.get("code") == 190 and error.get("type") == "OAuthException":
                    logger.info("Instagram token expired, refreshing...")
                    if creds.refresh_token and attempt == 0:
                        creds.access_token = await self.refresh_token(creds)
                        continue
            except Exception:
                pass

            # Handle other Graph API errors
            self._map_graph_error(response)

            # For other errors, raise
            response.raise_for_status()

        raise RuntimeError(f"Instagram publish failed after {MAX_RETRIES + 1} attempts")

    async def _poll_container_status(
        self,
        credentials: PlatformCredentials,
        container_id: str,
    ) -> None:
        """Poll container status endpoint until FINISHED."""
        creds = deepcopy(credentials)
        max_polls = 30  # 60 seconds max with 2s interval

        for _ in range(max_polls):
            await asyncio.sleep(REEL_POLL_INTERVAL)

            response = await self._http.get(
                f"{GRAPH_API}/{container_id}",
                params={"access_token": creds.access_token},
            )

            if response.status_code != 200:
                logger.warning("Container status check failed: %s", response.status_code)
                continue

            body = response.json()
            status = body.get("status_code")

            if status == "FINISHED":
                return
            if status in ("EXPIRED", "ERROR"):
                raise RuntimeError(f"Reel container status: {status}")

        raise TimeoutError("Reel container processing timed out")

    def _map_graph_error(self, response: httpx.Response) -> None:
        """Map Graph API error codes to appropriate exceptions."""
        try:
            body = response.json()
            error = body.get("error", {})
            code = error.get("code")
            subcode = error.get("error_subcode")
        except Exception:
            return

        if response.status_code == 429 or code == 4:
            raise RuntimeError("Instagram rate limit exceeded")
        if code == 200 and subcode == 1888029:
            raise RuntimeError("Instagram permission scope error")
        if code == 10:
            raise RuntimeError("Instagram app review required")
        if code == 190:
            # This is handled at call sites for retry logic
            pass
