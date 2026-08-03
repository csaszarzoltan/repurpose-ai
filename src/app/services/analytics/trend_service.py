"""Trend service — time-series aggregation and period-over-period deltas (P2.2).

Source of truth: analysis/analysis-brief.md §4 P2.2.

All series, summaries, and rankings are derived from the injected
``data_store`` (a MetricsRepository). A ``None`` store yields empty series —
the service is safe to construct without a store (interface tests do this).
"""

from __future__ import annotations

from datetime import datetime
from statistics import mean


class TrendService:
    """Time-series aggregation, period-over-period deltas, and top content ranking."""

    def __init__(self, data_store=None) -> None:
        self._data_store = data_store

    async def _rows(self, from_date: object = None, to_date: object = None) -> list[dict]:
        """Rows from the data store, filtered to the requested date window."""
        if self._data_store is None:
            return []
        rows = await self._data_store.list_all()
        if from_date is not None or to_date is not None:
            rows = [r for r in rows if self._in_range(r.get("post_date"), from_date, to_date)]
        return rows

    @staticmethod
    def _in_range(post_date: object, from_date: object, to_date: object) -> bool:
        """Date-window membership. Posts without a date are always included."""
        if post_date is None:
            return True
        if from_date is not None and post_date < from_date:
            return False
        return not (to_date is not None and post_date > to_date)

    @staticmethod
    def _day(post_date: object) -> str:
        if isinstance(post_date, datetime):
            return post_date.date().isoformat()
        return str(post_date)[:10]

    async def get_trend(
        self,
        metric: str,
        granularity: str = "daily",
        from_date: object = None,
        to_date: object = None,
    ) -> dict:
        """Get time-series trend data for a metric, aggregated per day."""
        rows = await self._rows(from_date, to_date)
        daily: dict[str, float] = {}
        for row in rows:
            value = row.get(metric)
            if value is None:
                continue
            day = self._day(row.get("post_date"))
            daily[day] = daily.get(day, 0.0) + float(value)
        points = [{"date": day, "value": value} for day, value in sorted(daily.items())]
        delta = self._split_delta(points)
        return {
            "metric": metric,
            "granularity": granularity,
            "points": points,
            "period_over_period_delta": delta,
        }

    def _split_delta(self, points: list[dict]) -> float:
        """Period-over-period delta: second half of the window vs the first half."""
        if len(points) < 2:
            return 0.0
        mid = len(points) // 2
        current = [p["value"] for p in points[mid:]]
        previous = [p["value"] for p in points[:mid]]
        return self.compute_period_delta(current, previous)

    async def get_summary(self, from_date: object = None, to_date: object = None) -> dict:
        """Get aggregated trend summary over the data store."""
        rows = await self._rows(from_date, to_date)
        rates = [
            float(r["engagement_rate"])
            for r in rows
            if r.get("engagement_rate") is not None
        ]
        platforms = [r.get("platform", "") for r in rows]
        return {
            "total_posts": len(rows),
            "total_reach": sum(int(r.get("reach") or 0) for r in rows),
            "avg_engagement_rate": round(sum(rates) / len(rates), 6) if rates else 0.0,
            "top_platform": max(set(platforms), key=platforms.count) if platforms else "",
        }

    async def get_top_content(
        self,
        metric: str,
        limit: int = 10,
        from_date: object = None,
        to_date: object = None,
    ) -> list[dict]:
        """Get top-performing content by metric, ranked highest first."""
        rows = await self._rows(from_date, to_date)
        ranked = sorted(
            rows,
            key=lambda r: float(r.get(metric) or 0.0),
            reverse=True,
        )
        result: list[dict] = []
        for row in ranked[:limit]:
            item = {"post_id": row.get("post_id", "")}
            item[metric] = float(row.get(metric) or 0.0)
            result.append(item)
        return result

    def compute_period_delta(self, current: list[float], previous: list[float]) -> float:
        """Compute period-over-period delta (difference of means)."""
        if not current or not previous:
            return 0.0
        return mean(current) - mean(previous)
