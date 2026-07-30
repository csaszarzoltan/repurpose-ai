"""Pre-dev tests for analytics Pydantic models.

Source of truth: analysis/analysis-brief.md §4 — models for P0.2, P1.1, P1.2, P2.2.
"""

from __future__ import annotations

from app.models.analytics import (
    AnalyticsSummary,
    DataPoint,
    OptimizationScore,
    PostMetrics,
    TrendData,
    ValidationReport,
)

# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS
# ═══════════════════════════════════════════════════════════════════════════════
# Note: Pydantic v2 with `from __future__ import annotations` stores fields
# in model_fields, not as class-level attributes. We use model_fields for checks.


class TestPostMetricsInterface:
    """Interface: PostMetrics is importable and has expected fields."""

    def test_importable(self):
        assert PostMetrics is not None

    def test_is_pydantic(self):
        from pydantic import BaseModel
        assert issubclass(PostMetrics, BaseModel)

    def test_has_reach(self):
        assert "reach" in PostMetrics.model_fields

    def test_has_impressions(self):
        assert "impressions" in PostMetrics.model_fields

    def test_has_engagement_rate(self):
        assert "engagement_rate" in PostMetrics.model_fields

    def test_has_completion_rate(self):
        assert "completion_rate" in PostMetrics.model_fields

    def test_has_share_rate(self):
        assert "share_rate" in PostMetrics.model_fields

    def test_has_send_rate(self):
        assert "send_rate" in PostMetrics.model_fields

    def test_has_growth_rate(self):
        assert "growth_rate" in PostMetrics.model_fields

    def test_has_post_date(self):
        assert "post_date" in PostMetrics.model_fields

    def test_has_platform(self):
        assert "platform" in PostMetrics.model_fields

    def test_has_post_id(self):
        assert "post_id" in PostMetrics.model_fields

    def test_field_count(self):
        assert len(PostMetrics.model_fields) == 10


class TestAnalyticsSummaryInterface:
    """Interface: AnalyticsSummary is importable and has expected fields."""

    def test_importable(self):
        assert AnalyticsSummary is not None

    def test_is_pydantic(self):
        from pydantic import BaseModel
        assert issubclass(AnalyticsSummary, BaseModel)

    def test_has_total_reach(self):
        assert "total_reach" in AnalyticsSummary.model_fields

    def test_has_avg_engagement_rate(self):
        assert "avg_engagement_rate" in AnalyticsSummary.model_fields

    def test_has_follower_growth(self):
        assert "follower_growth" in AnalyticsSummary.model_fields

    def test_has_period_start(self):
        assert "period_start" in AnalyticsSummary.model_fields

    def test_has_period_end(self):
        assert "period_end" in AnalyticsSummary.model_fields

    def test_field_count(self):
        assert len(AnalyticsSummary.model_fields) == 5


class TestOptimizationScoreInterface:
    """Interface: OptimizationScore is importable and has expected fields."""

    def test_importable(self):
        assert OptimizationScore is not None

    def test_is_pydantic(self):
        from pydantic import BaseModel
        assert issubclass(OptimizationScore, BaseModel)

    def test_has_overall_score(self):
        assert "overall_score" in OptimizationScore.model_fields

    def test_has_signals(self):
        assert "signals" in OptimizationScore.model_fields

    def test_has_platform(self):
        assert "platform" in OptimizationScore.model_fields

    def test_has_calculated_at(self):
        assert "calculated_at" in OptimizationScore.model_fields

    def test_field_count(self):
        assert len(OptimizationScore.model_fields) == 4


class TestValidationReportInterface:
    """Interface: ValidationReport is importable and has expected fields."""

    def test_importable(self):
        assert ValidationReport is not None

    def test_is_pydantic(self):
        from pydantic import BaseModel
        assert issubclass(ValidationReport, BaseModel)

    def test_has_quality_delta(self):
        assert "quality_delta" in ValidationReport.model_fields

    def test_has_readability(self):
        assert "readability" in ValidationReport.model_fields

    def test_has_tone_consistency(self):
        assert "tone_consistency" in ValidationReport.model_fields

    def test_has_faithfulness(self):
        assert "faithfulness" in ValidationReport.model_fields

    def test_has_llm_judge(self):
        assert "llm_judge" in ValidationReport.model_fields

    def test_has_diff_blocks(self):
        assert "diff_blocks" in ValidationReport.model_fields

    def test_field_count(self):
        assert len(ValidationReport.model_fields) == 6


class TestTrendDataInterface:
    """Interface: TrendData and DataPoint are importable and have expected fields."""

    def test_data_point_importable(self):
        assert DataPoint is not None

    def test_data_point_is_pydantic(self):
        from pydantic import BaseModel
        assert issubclass(DataPoint, BaseModel)

    def test_data_point_has_date(self):
        assert "date" in DataPoint.model_fields

    def test_data_point_has_value(self):
        assert "value" in DataPoint.model_fields

    def test_data_point_field_count(self):
        assert len(DataPoint.model_fields) == 2

    def test_trend_data_importable(self):
        assert TrendData is not None

    def test_trend_data_is_pydantic(self):
        from pydantic import BaseModel
        assert issubclass(TrendData, BaseModel)

    def test_trend_data_has_points(self):
        assert "points" in TrendData.model_fields

    def test_trend_data_has_period_over_period_delta(self):
        assert "period_over_period_delta" in TrendData.model_fields

    def test_trend_data_has_metric(self):
        assert "metric" in TrendData.model_fields

    def test_trend_data_has_granularity(self):
        assert "granularity" in TrendData.model_fields

    def test_trend_data_field_count(self):
        assert len(TrendData.model_fields) == 4


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestPostMetricsBehavior:
    """Behavioral: PostMetrics constructs and defaults correctly."""

    def test_minimal_construction(self):
        m = PostMetrics()
        assert m.reach is None
        assert m.impressions is None

    def test_partial_metrics(self):
        m = PostMetrics(reach=100, engagement_rate=0.05)
        assert m.reach == 100
        assert m.engagement_rate == 0.05
        assert m.impressions is None

    def test_with_platform_and_post_id(self):
        m = PostMetrics(platform="linkedin", post_id="abc123")
        assert m.platform == "linkedin"
        assert m.post_id == "abc123"


class TestAnalyticsSummaryBehavior:
    """Behavioral: AnalyticsSummary constructs and defaults correctly."""

    def test_default_zero_values(self):
        s = AnalyticsSummary()
        assert s.total_reach == 0
        assert s.avg_engagement_rate == 0.0
        assert s.follower_growth == 0

    def test_custom_values(self):
        s = AnalyticsSummary(total_reach=5000, avg_engagement_rate=0.032)
        assert s.total_reach == 5000
        assert s.avg_engagement_rate == 0.032


class TestOptimizationScoreBehavior:
    """Behavioral: OptimizationScore constructs and defaults correctly."""

    def test_default_zero_score(self):
        s = OptimizationScore()
        assert s.overall_score == 0.0
        assert s.signals == {}

    def test_with_signals(self):
        s = OptimizationScore(
            overall_score=78.5,
            signals={"dwell_time": 0.9, "completion_rate": 0.85},
            platform="linkedin",
        )
        assert s.overall_score == 78.5
        assert len(s.signals) == 2


class TestTrendDataBehavior:
    """Behavioral: TrendData and DataPoint construct correctly."""

    def test_data_point_construction(self):
        dp = DataPoint(date="2026-07-01", value=150.0)
        assert dp.date == "2026-07-01"
        assert dp.value == 150.0

    def test_trend_data_with_points(self):
        points = [DataPoint(date="2026-07-01", value=100.0)]
        td = TrendData(points=points, period_over_period_delta=0.15, metric="engagement_rate", granularity="daily")
        assert len(td.points) == 1
        assert td.period_over_period_delta == 0.15
        assert td.metric == "engagement_rate"
