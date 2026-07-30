"""Pre-dev tests for trend visualization API (P2.2).

Source of truth: analysis/analysis-brief.md §4 P2.2 — trend_service.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.services.analytics.trend_service import TrendService
    HAS_SERVICE = True
except (ImportError, ModuleNotFoundError):
    HAS_SERVICE = False

try:
    from app.models.analytics import DataPoint, TrendData
    HAS_MODELS = True
except (ImportError, ModuleNotFoundError):
    HAS_MODELS = False


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — TrendService
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_SERVICE, reason="trend_service.py not implemented yet")
class TestTrendServiceInterface:
    """Interface: TrendService is importable and has expected API."""

    def test_importable(self):
        assert TrendService is not None

    def test_is_class(self):
        assert isinstance(TrendService, type)

    def test_init_accepts_data_store(self):
        svc = TrendService(data_store=None)
        assert svc is not None

    def test_init_defaults(self):
        svc = TrendService()
        assert svc is not None

    def test_has_get_trend_method(self):
        import inspect
        assert hasattr(TrendService, "get_trend")
        assert inspect.iscoroutinefunction(TrendService.get_trend)

    def test_get_trend_accepts_metric_and_granularity(self):
        import inspect
        sig = inspect.signature(TrendService.get_trend)
        assert "metric" in sig.parameters
        assert "granularity" in sig.parameters

    def test_has_get_summary_method(self):
        import inspect
        assert hasattr(TrendService, "get_summary")
        assert inspect.iscoroutinefunction(TrendService.get_summary)

    def test_has_get_top_content_method(self):
        import inspect
        assert hasattr(TrendService, "get_top_content")
        assert inspect.iscoroutinefunction(TrendService.get_top_content)

    def test_get_top_content_accepts_metric_and_limit(self):
        import inspect
        sig = inspect.signature(TrendService.get_top_content)
        assert "metric" in sig.parameters
        assert "limit" in sig.parameters

    def test_has_compute_period_delta_method(self):
        assert hasattr(TrendService, "compute_period_delta")
        assert callable(TrendService.compute_period_delta)

    def test_compute_period_delta_is_sync(self):
        import inspect
        assert not inspect.iscoroutinefunction(TrendService.compute_period_delta)

    def test_get_trend_returns_dict_type_hint(self):
        import inspect
        sig = inspect.signature(TrendService.get_trend)
        ann = sig.return_annotation
        assert ann in (dict, "dict", inspect.Parameter.empty)

    def test_compute_period_delta_returns_float_type_hint(self):
        import inspect
        sig = inspect.signature(TrendService.compute_period_delta)
        ann = sig.return_annotation
        assert ann in (float, "float", inspect.Parameter.empty)


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Models
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_MODELS, reason="analytics models not implemented yet")
class TestTrendModelsInterface:
    """Interface: TrendData and DataPoint have expected fields."""

    def test_trend_data_is_base_model(self):
        from pydantic import BaseModel
        assert issubclass(TrendData, BaseModel)

    def test_trend_data_has_points(self):
        assert "points" in TrendData.model_fields

    def test_trend_data_has_metric(self):
        assert "metric" in TrendData.model_fields

    def test_data_point_has_date(self):
        assert "date" in DataPoint.model_fields

    def test_data_point_has_value(self):
        assert "value" in DataPoint.model_fields


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — TrendService
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_SERVICE, reason="trend_service.py not implemented yet")
class TestTrendServiceBehavior:
    """Behavioral: TrendService aggregates and returns trend data."""

    async def test_get_trend_returns_dict_with_points(self):
        svc = TrendService()
        result = await svc.get_trend("engagement_rate", granularity="daily")
        assert isinstance(result, dict)
        assert "points" in result
        assert "period_over_period_delta" in result

    async def test_get_trend_with_date_range(self):
        svc = TrendService()
        result = await svc.get_trend(
            "reach",
            granularity="weekly",
            from_date=datetime(2026, 1, 1, tzinfo=UTC),
            to_date=datetime(2026, 6, 30, tzinfo=UTC),
        )
        assert isinstance(result, dict)

    async def test_get_trend_defaults_to_daily(self):
        svc = TrendService()
        result = await svc.get_trend("impressions")
        assert isinstance(result, dict)

    async def test_get_summary_returns_dict(self):
        svc = TrendService()
        result = await svc.get_summary()
        assert isinstance(result, dict)

    async def test_get_summary_with_dates(self):
        svc = TrendService()
        result = await svc.get_summary(
            from_date=datetime(2026, 1, 1, tzinfo=UTC),
            to_date=datetime(2026, 3, 31, tzinfo=UTC),
        )
        assert isinstance(result, dict)

    async def test_get_top_content_returns_list(self):
        svc = TrendService()
        results = await svc.get_top_content("engagement_rate", limit=5)
        assert isinstance(results, list)
        assert len(results) <= 5

    async def test_get_top_content_default_limit(self):
        svc = TrendService()
        results = await svc.get_top_content("reach")
        assert isinstance(results, list)

    async def test_get_top_content_with_date_filter(self):
        svc = TrendService()
        results = await svc.get_top_content(
            "engagement_rate",
            limit=10,
            from_date=datetime(2026, 1, 1, tzinfo=UTC),
            to_date=datetime(2026, 6, 30, tzinfo=UTC),
        )
        assert isinstance(results, list)


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Period-over-period delta
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_SERVICE, reason="trend_service.py not implemented yet")
class TestPeriodDeltaBehavior:
    """Behavioral: Period-over-period delta computation."""

    def test_positive_delta(self):
        svc = TrendService()
        delta = svc.compute_period_delta([100.0, 110.0, 120.0], [80.0, 90.0, 100.0])
        assert isinstance(delta, float)
        assert delta > 0

    def test_negative_delta(self):
        svc = TrendService()
        delta = svc.compute_period_delta([80.0, 90.0], [100.0, 110.0])
        assert delta < 0

    def test_zero_delta(self):
        svc = TrendService()
        delta = svc.compute_period_delta([100.0], [100.0])
        assert delta == 0.0

    def test_empty_current_returns_zero(self):
        svc = TrendService()
        delta = svc.compute_period_delta([], [100.0])
        assert delta == 0.0

    def test_empty_previous_returns_zero(self):
        svc = TrendService()
        delta = svc.compute_period_delta([100.0], [])
        assert delta == 0.0

    def test_single_item_lists(self):
        svc = TrendService()
        delta = svc.compute_period_delta([150.0], [100.0])
        assert delta == 50.0

    def test_large_values(self):
        svc = TrendService()
        delta = svc.compute_period_delta([1000000.0], [500000.0])
        assert delta > 0
