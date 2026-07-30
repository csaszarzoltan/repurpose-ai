"""Example: P0.2 — Content Performance Tracking.

Demonstrates MetricsCollector and PostMetrics/AnalyticsSummary models.
"""

import asyncio
from datetime import UTC, datetime

from app.models.analytics import AnalyticsSummary, PostMetrics
from app.services.analytics.metrics_collector import MetricsCollector


async def main() -> None:
    # ── MetricsCollector ──
    collector = MetricsCollector(platform_adapters={})

    # Collect metrics for a single post
    metrics = await collector.collect(platform="linkedin", post_id="post_123")
    print(f"Single post metrics: {metrics}")

    # Collect metrics for a date range
    all_metrics = await collector.collect_range(
        platform="linkedin",
        from_date="2026-01-01",
        to_date="2026-01-31",
    )
    print(f"Range metrics: {all_metrics}")

    # Normalise raw platform data
    normalised = collector.normalise_metrics(
        {"views": 1000, "likes": 50, "shares": 10}
    )
    print(f"Normalised: {normalised}")

    # Normalise with zero views
    empty = collector.normalise_metrics({"views": 0, "likes": 0, "shares": 0})
    print(f"Empty normalised: {empty}")

    # ── PostMetrics model ──
    post = PostMetrics(
        reach=1000,
        impressions=5000,
        engagement_rate=0.05,
        completion_rate=0.8,
        share_rate=0.02,
        growth_rate=0.01,
        post_date=datetime(2026, 1, 15, tzinfo=UTC),
        platform="linkedin",
        post_id="post_123",
    )
    print(f"PostMetrics: platform={post.platform}, engagement={post.engagement_rate}")

    # PostMetrics with minimal fields
    minimal = PostMetrics(platform="twitter", post_id="post_456")
    print(f"Minimal PostMetrics: engagement={minimal.engagement_rate}")  # None

    # ── AnalyticsSummary model ──
    summary = AnalyticsSummary(
        total_reach=15000,
        avg_engagement_rate=0.045,
        follower_growth=120,
        period_start=datetime(2026, 1, 1, tzinfo=UTC),
        period_end=datetime(2026, 1, 31, tzinfo=UTC),
    )
    print(f"Summary: reach={summary.total_reach}, avg_engagement={summary.avg_engagement_rate}")


if __name__ == "__main__":
    asyncio.run(main())
