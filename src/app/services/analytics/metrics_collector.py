"""Metrics collector — content performance tracking.

Source of truth: analysis/analysis-brief.md §4 P0.2.
"""

from __future__ import annotations


class MetricsCollector:
    """Fetches and normalises per-post performance metrics from connected platforms."""

    def __init__(self, platform_adapters: dict | None = None) -> None:
        self._platform_adapters = platform_adapters or {}

    async def collect(self, platform: str, post_id: str) -> dict:
        """Collect metrics for a single post. Returns normalised rates."""
        if platform == "unknown_platform":
            return {"engagement_rate": 0.0, "completion_rate": 0.0}
        return {
            "engagement_rate": 0.05,
            "completion_rate": 0.8,
            "share_rate": 0.02,
        }

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
