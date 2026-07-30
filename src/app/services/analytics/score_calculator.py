"""Score calculator — platform optimization scoring (P1.1).

Calculates 0-100 algorithm-readiness scores per platform based on
engagement metrics. Different platforms use different weight configs.

Source of truth: analysis/analysis-brief.md §4 P1.1.
"""

from __future__ import annotations


class ScoreCalculator:
    """Calculates 0-100 algorithm-readiness score per platform."""

    def __init__(self, weights_config: dict | None = None) -> None:
        self._weights_config = weights_config or {}

    async def calculate(
        self,
        platform: str,
        metrics: dict,
    ) -> dict:
        """Calculate algorithm-readiness score (0-100) for given metrics."""
        engagement_rate = metrics.get("engagement_rate", 0.0) or 0.0
        engagement_score = min(engagement_rate * 800, 40.0)
        completion_rate = metrics.get("completion_rate", 0.0) or 0.0
        completion_score = completion_rate * 30.0
        share_rate = metrics.get("share_rate", 0.0) or 0.0
        share_score = share_rate * 20.0
        platform_multiplier = 1.0 if platform == "linkedin" else 0.95
        overall = (engagement_score + completion_score + share_score) * platform_multiplier
        overall = max(0.0, min(100.0, overall))
        signals = {
            "engagement_rate": engagement_rate,
            "completion_rate": completion_rate,
            "share_rate": share_rate,
        }
        return {"overall_score": overall, "signals": signals}

    async def calculate_batch(
        self,
        platform: str,
        metrics_list: list[dict],
    ) -> list[dict]:
        """Calculate scores for multiple metric sets."""
        results = []
        for metrics in metrics_list:
            result = await self.calculate(platform, metrics)
            results.append(result)
        return results

    def normalise_score(self, raw_score: float) -> float:
        """Clamp a raw score to the 0-100 range."""
        return max(0.0, min(100.0, raw_score))
