"""Example: P1.1 — Platform Optimization Scoring.

Demonstrates ScoreCalculator and OptimizationScore model.
"""

import asyncio
from datetime import UTC, datetime

from app.models.analytics import OptimizationScore
from app.services.analytics.score_calculator import ScoreCalculator


async def main() -> None:
    calc = ScoreCalculator(weights_config={})

    # ── Single calculation ──
    result = await calc.calculate(
        platform="linkedin",
        metrics={
            "engagement_rate": 0.05,
            "completion_rate": 0.8,
            "share_rate": 0.02,
        },
    )
    print(f"LinkedIn score: {result['overall_score']:.1f}")
    print(f"Signals: {result['signals']}")

    # ── Batch calculation ──
    results = await calc.calculate_batch(
        platform="twitter",
        metrics_list=[
            {"engagement_rate": 0.03, "completion_rate": 0.7, "share_rate": 0.01},
            {"engagement_rate": 0.08, "completion_rate": 0.9, "share_rate": 0.05},
            {"engagement_rate": 0.01, "completion_rate": 0.2, "share_rate": 0.005},
        ],
    )
    for i, r in enumerate(results, 1):
        print(f"  Batch {i}: score={r['overall_score']:.1f}")

    # ── Normalise ──
    clamped = calc.normalise_score(raw_score=120.0)
    print(f"Clamped 120 → {clamped}")

    clamped_low = calc.normalise_score(raw_score=-10.0)
    print(f"Clamped -10 → {clamped_low}")

    # ── OptimizationScore model ──
    score = OptimizationScore(
        overall_score=78.5,
        signals={"engagement_rate": 0.05, "completion_rate": 0.8},
        platform="linkedin",
        calculated_at=datetime.now(UTC),
    )
    print(f"Model: platform={score.platform}, score={score.overall_score}")


if __name__ == "__main__":
    asyncio.run(main())
