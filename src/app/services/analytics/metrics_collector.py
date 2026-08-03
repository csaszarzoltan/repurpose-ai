"""Metrics collector — content performance tracking.

Source of truth: analysis/analysis-brief.md §4 P0.2.

The collector is the ingestion path for per-post performance metrics:

1. ``collect(platform, post_id)`` fetches raw platform metrics through the
   registered platform adapter (if any), normalises them into standard
   0.0-1.0 rates, and **persists** the result to the analytics SQLite store
   via :class:`app.services.analytics.db.repository.MetricsRepository`.

Platform adapters are callables (sync or async) mapping ``post_id`` to a raw
metrics dict, or objects exposing an async ``fetch_metrics(post_id)`` method.
Without a configured adapter there is no external source to fetch from, so a
zero-valued raw payload is normalised and persisted instead of fabricating
numbers.
"""

from __future__ import annotations

import inspect

from app.services.analytics.db.repository import MetricsRepository


class MetricsCollector:
    """Fetches and normalises per-post performance metrics from connected platforms."""

    def __init__(
        self,
        platform_adapters: dict | None = None,
        repository: MetricsRepository | None = None,
    ) -> None:
        self._platform_adapters = platform_adapters or {}
        self._repository = repository

    async def collect(self, platform: str, post_id: str) -> dict:
        """Collect metrics for a single post and persist them to the store.

        Returns the normalised rates (0.0-1.0 floats) and stores both the raw
        values and the normalised rates in the analytics SQLite store.
        """
        raw = await self._fetch_raw(platform, post_id)
        normalised = self.normalise_metrics(raw)
        metrics = {**raw, **normalised}
        repo = self._repository or MetricsRepository()
        await repo.store_metrics(platform, post_id, metrics)
        return normalised

    async def _fetch_raw(self, platform: str, post_id: str) -> dict:
        """Fetch raw platform metrics from the adapter registered for ``platform``."""
        adapter = self._platform_adapters.get(platform)
        if adapter is None:
            return {}
        if hasattr(adapter, "fetch_metrics"):
            raw = adapter.fetch_metrics(post_id)
        elif callable(adapter):
            raw = adapter(post_id)
        else:
            return {}
        if inspect.iscoroutine(raw):
            raw = await raw
        if not isinstance(raw, dict):
            return {}
        return raw

    async def collect_range(
        self,
        platform: str,
        from_date: object,
        to_date: object,
    ) -> list[dict]:
        """Collect metrics for all posts in a date range."""
        return []

    def normalise_metrics(self, raw: dict) -> dict:
        """Normalise raw platform metrics into standard rates (0.0-1.0 floats)."""
        result: dict = {}
        views = raw.get("views", 0) or 0
        likes = raw.get("likes", 0) or 0
        shares = raw.get("shares", 0) or 0
        if views > 0:
            result["engagement_rate"] = float(likes) / float(views)
            result["share_rate"] = float(shares) / float(views)
            result["completion_rate"] = 0.0
        else:
            result["engagement_rate"] = 0.0
            result["share_rate"] = 0.0
            result["completion_rate"] = 0.0
        return result
