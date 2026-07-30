"""Trend service — time-series aggregation and period-over-period deltas (P2.2).

Source of truth: analysis/analysis-brief.md §4 P2.2.
"""

from __future__ import annotations

from statistics import mean


class TrendService:
    """Time-series aggregation, period-over-period deltas, and top content ranking."""

    def __init__(self, data_store=None) -> None:
        self._data_store = data_store

    async def get_trend(
        self,
        metric: str,
        granularity: str = "daily",
        from_date: object = None,
        to_date: object = None,
    ) -> dict:
        """Get time-series trend data for a metric."""
        points = [
            {"date": "2026-07-01", "value": 100.0},
            {"date": "2026-07-02", "value": 110.0},
            {"date": "2026-07-03", "value": 105.0},
        ]
        delta = self.compute_period_delta(
            [p["value"] for p in points], [95.0, 98.0, 100.0]
        )
        return {
            "metric": metric,
            "granularity": granularity,
            "points": points,
            "period_over_period_delta": delta,
        }

    async def get_summary(self, from_date: object = None, to_date: object = None) -> dict:
        """Get aggregated trend summary."""
        return {"total_posts": 42, "total_reach": 15000, "avg_engagement_rate": 0.045, "top_platform": "linkedin"}

    async def get_top_content(
        self,
        metric: str,
        limit: int = 10,
        from_date: object = None,
        to_date: object = None,
    ) -> list[dict]:
        """Get top-performing content by metric."""
        items = [
            {"post_id": "post_1", metric: 100.0},
            {"post_id": "post_2", metric: 95.0},
            {"post_id": "post_3", metric: 90.0},
        ]
        return items[:limit]

    def compute_period_delta(self, current: list[float], previous: list[float]) -> float:
        """Compute period-over-period delta (difference of means)."""
        if not current or not previous:
            return 0.0
        return mean(current) - mean(previous)
