"""Seed the analytics store with demo data and serve the API in-process.

The analytics repositories are in-memory singletons (``app.dependencies``), so
a plain ``uvicorn app.main:app`` start has an EMPTY store. This dev helper
seeds realistic metrics, scores, and a validation report into the SAME process
it serves, so the dashboard can be demoed end-to-end against real
``/api/v1/analytics/*`` responses.

Usage:
    PYTHONPATH=src .venv/bin/python scripts/seed_analytics_demo.py [--port 8000] [--no-seed]

``--no-seed`` starts a clean (empty) backend — useful for exercising the
dashboard's onboarding/empty state.
"""

from __future__ import annotations

import argparse
import asyncio
import random
from datetime import UTC, datetime, timedelta

import uvicorn

from app.dependencies import (
    get_metrics_repository,
    get_score_repository,
    get_validation_repository,
)

PLATFORMS = ["twitter", "linkedin", "medium"]
DAYS = 14
POSTS_PER_PLATFORM = 6


async def _seed() -> None:
    """Populate the in-process repositories with deterministic demo data."""
    random.seed(42)
    metrics = get_metrics_repository()
    scores = get_score_repository()
    validations = get_validation_repository()

    today = datetime.now(UTC)
    for platform in PLATFORMS:
        for i in range(POSTS_PER_PLATFORM):
            post_id = f"{platform[:2]}-{today.strftime('%m%d')}-{i + 1:02d}"
            days_ago = random.randint(0, DAYS)
            reach = random.randint(1_200, 48_000)
            impressions = int(reach * random.uniform(1.4, 2.6))
            engagement = round(random.uniform(0.006, 0.058), 4)
            completion = round(random.uniform(0.25, 0.92), 3)
            share = round(random.uniform(0.004, 0.031), 4)
            growth = round(random.uniform(0.0, 0.02), 4)
            post_date = (today - timedelta(days=days_ago)).replace(hour=10, minute=0, second=0, microsecond=0)

            await metrics.store_metrics(
                platform,
                post_id,
                {
                    "reach": reach,
                    "impressions": impressions,
                    "engagement_rate": engagement,
                    "completion_rate": completion,
                    "share_rate": share,
                    "growth_rate": growth,
                    "post_date": post_date,
                },
            )
            overall = min(
                100.0,
                (min(engagement * 800, 40.0) + completion * 30.0 + share * 20.0)
                * (1.0 if platform == "linkedin" else 0.95),
            )
            await scores.store_score(
                post_id,
                platform,
                round(overall, 1),
                {"engagement_rate": engagement, "completion_rate": completion, "share_rate": share},
            )

    await validations.store_validation(
        "demo-validation-001",
        "AI is transforming how content teams work. This guide shows you how to turn one long-form piece "
        "into a week of social posts.",
        "Artificial intelligence is changing content marketing forever. In this guide, we show you exactly "
        "how to repurpose one long-form article into a full week of social media posts.",
        {
            "quality_delta": 0.31,
            "readability": {"flesch_kincaid": 12.4, "dale_chall": 9.1, "ari": 11.2},
            "tone_consistency": {"similarity": 0.75},
            "faithfulness": {"faithfulness": 0.82, "score": 0.82},
            "diff_blocks": [{"type": "insert", "content": "exactly"}],
        },
    )
    print(f"Seeded {len(PLATFORMS) * POSTS_PER_PLATFORM} posts, {len(PLATFORMS) * POSTS_PER_PLATFORM} scores, 1 validation.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-seed", action="store_true", help="Start with an empty analytics store")
    args = parser.parse_args()

    if not args.no_seed:
        asyncio.run(_seed())
    else:
        print("Starting with an EMPTY analytics store (onboarding/empty-state demo).")

    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
