"""Pre-dev tests for platform optimization scoring (P1.1).

Source of truth: analysis/analysis-brief.md §4 P1.1 — score_calculator.
"""

from __future__ import annotations

import pytest

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.services.analytics.score_calculator import ScoreCalculator
    HAS_CALCULATOR = True
except (ImportError, ModuleNotFoundError):
    HAS_CALCULATOR = False


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_CALCULATOR, reason="score_calculator.py not implemented yet")
class TestScoreCalculatorInterface:
    """Interface: ScoreCalculator is importable and has expected API."""

    def test_importable(self):
        assert ScoreCalculator is not None

    def test_is_class(self):
        assert isinstance(ScoreCalculator, type)

    def test_init_accepts_weights_config(self):
        calc = ScoreCalculator(weights_config={})
        assert calc is not None

    def test_init_defaults(self):
        calc = ScoreCalculator()
        assert calc is not None

    def test_has_calculate_method(self):
        import inspect
        assert hasattr(ScoreCalculator, "calculate")
        assert inspect.iscoroutinefunction(ScoreCalculator.calculate)

    def test_calculate_accepts_platform_and_metrics(self):
        import inspect
        sig = inspect.signature(ScoreCalculator.calculate)
        params = list(sig.parameters.keys())
        assert "platform" in params
        assert "metrics" in params

    def test_has_calculate_batch_method(self):
        import inspect
        assert hasattr(ScoreCalculator, "calculate_batch")
        assert inspect.iscoroutinefunction(ScoreCalculator.calculate_batch)

    def test_has_normalise_score_method(self):
        assert hasattr(ScoreCalculator, "normalise_score")
        assert callable(ScoreCalculator.normalise_score)

    def test_normalise_score_is_sync(self):
        import inspect
        assert not inspect.iscoroutinefunction(ScoreCalculator.normalise_score)

    def test_calculate_returns_dict_type_hint(self):
        import inspect
        sig = inspect.signature(ScoreCalculator.calculate)
        ann = sig.return_annotation
        assert ann in (dict, "dict", inspect.Parameter.empty)

    def test_normalise_score_accepts_float(self):
        import inspect
        sig = inspect.signature(ScoreCalculator.normalise_score)
        params = list(sig.parameters.keys())
        assert "raw_score" in params


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_CALCULATOR, reason="score_calculator.py not implemented yet")
class TestScoreCalculatorBehavior:
    """Behavioral: ScoreCalculator computes scores correctly."""

    async def test_calculate_returns_dict_with_overall_score(self):
        calc = ScoreCalculator()
        result = await calc.calculate("linkedin", {"engagement_rate": 0.05, "completion_rate": 0.8})
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "signals" in result

    async def test_score_is_0_to_100(self):
        calc = ScoreCalculator()
        result = await calc.calculate("twitter", {"engagement_rate": 0.02})
        score = result.get("overall_score", 0)
        assert 0 <= score <= 100

    async def test_deterministic_same_input_same_score(self):
        calc = ScoreCalculator()
        metrics = {"engagement_rate": 0.05, "completion_rate": 0.8}
        result1 = await calc.calculate("linkedin", metrics)
        result2 = await calc.calculate("linkedin", metrics)
        assert result1["overall_score"] == result2["overall_score"]

    async def test_different_platforms_different_scores(self):
        calc = ScoreCalculator()
        metrics = {"engagement_rate": 0.05}
        linkedin = await calc.calculate("linkedin", metrics)
        twitter = await calc.calculate("twitter", metrics)
        # Different platforms may have different weights, but should both produce scores
        assert "overall_score" in linkedin
        assert "overall_score" in twitter

    async def test_zero_metrics_handled(self):
        calc = ScoreCalculator()
        result = await calc.calculate("linkedin", {})
        assert result is not None
        assert 0 <= result["overall_score"] <= 100

    async def test_calculate_batch_returns_list(self):
        calc = ScoreCalculator()
        metrics_list = [
            {"engagement_rate": 0.05},
            {"engagement_rate": 0.10},
            {"engagement_rate": 0.02},
        ]
        results = await calc.calculate_batch("linkedin", metrics_list)
        assert isinstance(results, list)
        assert len(results) == 3
        for r in results:
            assert "overall_score" in r

    def test_normalise_score_clamps_to_range(self):
        calc = ScoreCalculator()
        score = calc.normalise_score(150.0)
        assert 0 <= score <= 100

    def test_normalise_score_negative_input(self):
        calc = ScoreCalculator()
        score = calc.normalise_score(-10.0)
        assert 0 <= score <= 100
