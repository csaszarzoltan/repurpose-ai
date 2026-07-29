"""Twitter/X publisher — API v2."""
from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from app.models.publish import PlatformCredentials

TWITTER_API = "https://api.twitter.com"
MAX_RETRIES = 3


class TwitterPublisher:
    """Publish tweets and threads to Twitter/X via API v2.

    Handles single tweets with optional media, threaded multi-tweet chains,
    and rate-limit backoff.
    """

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._http = http_client or httpx.AsyncClient()

    async def create_tweet(
        self,
        credentials: PlatformCredentials,
        text: str,
        media_ids: list[str] | None = None,
    ) -> dict:
        """Post a single tweet. Optionally include media_ids."""
        creds = deepcopy(credentials)

        for attempt in range(MAX_RETRIES + 1):
            headers = self._build_headers(creds.access_token)
            payload: dict = {"text": text}

            if media_ids:
                payload["media"] = {"media_ids": media_ids}

            response = await self._http.post(
                f"{TWITTER_API}/2/tweets",
                headers=headers,
                json=payload,
            )

            if response.status_code == 201:
                return response.json()

            if response.status_code == 429:
                retry_after = self._get_retry_after(response)
                await asyncio.sleep(retry_after)
                continue

            if response.status_code >= 500 and attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (2**attempt))
                continue

            response.raise_for_status()

        raise Exception(f"Twitter tweet failed after {MAX_RETRIES + 1} attempts")

    async def create_thread(
        self,
        credentials: PlatformCredentials,
        tweets: list[str],
    ) -> list[dict]:
        """Post a thread of tweets, each chained via reply settings.

        The first tweet is a standalone post. Each subsequent tweet
        includes ``reply.in_reply_to_tweet_id`` pointing to the previous one.
        """
        results: list[dict] = []
        previous_id: str | None = None

        for tweet_text in tweets:
            headers = self._build_headers(credentials.access_token)
            payload: dict = {"text": tweet_text}

            if previous_id:
                payload["reply"] = {"in_reply_to_tweet_id": previous_id}

            # Retry pattern for each tweet in the thread
            for attempt in range(MAX_RETRIES + 1):
                response = await self._http.post(
                    f"{TWITTER_API}/2/tweets",
                    headers=headers,
                    json=payload,
                )

                if response.status_code == 201:
                    body = response.json()
                    results.append(body)
                    previous_id = body.get("data", {}).get("id")
                    break

                if response.status_code == 429:
                    await asyncio.sleep(self._get_retry_after(response))
                    continue

                if response.status_code >= 500 and attempt < MAX_RETRIES:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue

                response.raise_for_status()
            else:
                raise Exception(f"Thread tweet failed after {MAX_RETRIES + 1} attempts")

        return results

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _build_headers(access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _get_retry_after(response: httpx.Response) -> float:
        retry_header = response.headers.get("Retry-After", "1")
        try:
            return float(retry_header)
        except (ValueError, TypeError):
            return 1.0
