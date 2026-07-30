"""Example: P2.2 — Trend Visualization.

Demonstrates TrendService: time-series trends, period-over-period deltas,
aggregated summaries, and top-content ranking.
"""

import asyncio

from app.models.analytics import DataPoint, TrendData
from app.services.analytics.trend_service import TrendService


async def main() -> None:
    svc = TrendService(data_store=None)

    # ── Get trend data for a metric ──
    trend = await svc.get_trend(
        metric="engagement_rate",
        granularity="daily",
        from_date="2026-01-01",
        to_date="2026-01-31",
    )
    print(f"Trend for {trend['metric']} ({trend['granularity']}):")
    print(f"  Points: {len(trend['points'])}")
    print(f"  Period-over-period delta: {trend['period_over_period_delta']:.2f}")
    for p in trend['points']:
        print(f"    {p['date']}: {p['value']}")

    # ── Get aggregated summary ──
    summary = await svc.get_summary(
        from_date="2026-01-01",
        to_date="2026-01-31",
    )
    print(f"Summary: {summary['total_posts']} posts, "
          f"{summary['total_reach']} reach, "
          f"top platform={summary['top_platform']}")

    # ── Get top content ──
    top = await svc.get_top_content(
        metric="engagement_rate",
        limit=3,
        from_date="2026-01-01",
        to_date="2026-01-31",
    )
    for item in top:
        print(f"  Top: {item['post_id']} → {item['engagement_rate']}")

    # Larger limit
    top_10 = await svc.get_top_content(
        metric="reach",
        limit=10,
    )
    print(f"Top content (limit 10): {len(top_10)} items")

    # ── Period-over-period delta ──
    delta = svc.compute_period_delta(
        current=[100.0, 110.0, 105.0],
        previous=[95.0, 98.0, 100.0],
    )
    print(f"Period delta: {delta:.2f} (mean current − mean previous)")

    # Empty lists
    empty_delta = svc.compute_period_delta(current=[], previous=[])
    print(f"Empty delta: {empty_delta}")

    # ── DataPoint and TrendData models ──
    point = DataPoint(date="2026-07-01", value=100.0)
    print(f"DataPoint: {point.date} = {point.value}")

    trend_data = TrendData(
        points=[DataPoint(date="2026-07-01", value=100.0)],
        period_over_period_delta=7.33,
        metric="engagement_rate",
        granularity="daily",
    )
    print(f"TrendData: metric={trend_data.metric}, "
          f"delta={trend_data.period_over_period_delta}, "
          f"points={len(trend_data.points)}")


if __name__ == "__main__":
    asyncio.run(main())
