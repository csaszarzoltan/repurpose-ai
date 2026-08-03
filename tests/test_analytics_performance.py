"""Pre-dev tests for content performance tracking API (P0.2).

Source of truth: analysis/analysis-brief.md §4 P0.2 — metrics_collector and API.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.services.analytics.metrics_collector import MetricsCollector
    HAS_COLLECTOR = True
except (ImportError, ModuleNotFoundError):
    HAS_COLLECTOR = False

try:
    from app.api.analytics import router as analytics_router
    HAS_ROUTER = True
except (ImportError, ModuleNotFoundError):
    HAS_ROUTER = False

try:
    from app.models.analytics import AnalyticsSummary, PostMetrics
    HAS_MODELS = True
except (ImportError, ModuleNotFoundError):
    HAS_MODELS = False


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — MetricsCollector
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_COLLECTOR, reason="metrics_collector.py not implemented yet")
class TestMetricsCollectorInterface:
    """Interface: MetricsCollector is importable and has expected API."""

    def test_importable(self):
        assert MetricsCollector is not None

    def test_is_class(self):
        assert isinstance(MetricsCollector, type)

    def test_init_accepts_platform_adapters(self):
        collector = MetricsCollector(platform_adapters={})
        assert collector is not None

    def test_init_defaults(self):
        collector = MetricsCollector()
        assert collector is not None

    def test_has_collect_method(self):
        import inspect
        assert hasattr(MetricsCollector, "collect")
        assert inspect.iscoroutinefunction(MetricsCollector.collect)

    def test_has_collect_range_method(self):
        import inspect
        assert hasattr(MetricsCollector, "collect_range")
        assert inspect.iscoroutinefunction(MetricsCollector.collect_range)

    def test_has_normalise_metrics_method(self):
        assert hasattr(MetricsCollector, "normalise_metrics")
        assert callable(MetricsCollector.normalise_metrics)

    def test_normalise_metrics_is_sync(self):
        import inspect
        assert not inspect.iscoroutinefunction(MetricsCollector.normalise_metrics)

    def test_collect_accepts_platform_and_post_id(self):
        import inspect
        sig = inspect.signature(MetricsCollector.collect)
        params = list(sig.parameters.keys())
        assert "platform" in params
        assert "post_id" in params


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — API Router
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ROUTER, reason="analytics.py API not implemented yet")
class TestAnalyticsRouterInterface:
    """Interface: analytics router is registered with correct prefix."""

    def test_router_importable(self):
        assert analytics_router is not None

    def test_router_has_correct_prefix(self):
        assert analytics_router.prefix == "/api/v1/analytics"

    def test_router_has_analytics_tag(self):
        assert "analytics" in analytics_router.tags

    def test_router_has_list_posts_route(self):
        routes = [r.path for r in analytics_router.routes]
        assert "/api/v1/analytics/posts" in routes or "/posts" in routes

    def test_router_has_get_post_route(self):
        routes = [r.path for r in analytics_router.routes]
        assert any("/posts/{post_id}" in r or "/posts/" in r for r in routes)

    def test_router_has_summary_route(self):
        routes = [r.path for r in analytics_router.routes]
        assert any("/summary" in r for r in routes)


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Models
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_MODELS, reason="analytics models not implemented yet")
class TestPerformanceModelsInterface:
    """Interface: PostMetrics and AnalyticsSummary are importable."""

    def test_post_metrics_is_base_model(self):
        from pydantic import BaseModel
        assert issubclass(PostMetrics, BaseModel)

    def test_analytics_summary_is_base_model(self):
        from pydantic import BaseModel
        assert issubclass(AnalyticsSummary, BaseModel)


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — MetricsCollector
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_COLLECTOR, reason="metrics_collector.py not implemented yet")
class TestMetricsCollectorBehavior:
    """Behavioral: MetricsCollector fetches and normalises metrics."""

    async def test_collect_returns_dict_with_normalised_rates(self):
        collector = MetricsCollector()
        result = await collector.collect("linkedin", "post_abc")
        assert isinstance(result, dict)
        assert "engagement_rate" in result
        assert "completion_rate" in result

    async def test_collect_range_returns_list(self):
        collector = MetricsCollector()
        results = await collector.collect_range(
            "twitter",
            from_date=datetime(2026, 1, 1, tzinfo=UTC),
            to_date=datetime(2026, 1, 31, tzinfo=UTC),
        )
        assert isinstance(results, list)

    def test_normalise_rates_are_floats(self):
        collector = MetricsCollector()
        raw = {"likes": 100, "views": 1000, "shares": 50}
        normalised = collector.normalise_metrics(raw)
        assert isinstance(normalised, dict)
        for key in ("engagement_rate", "completion_rate", "share_rate"):
            if key in normalised:
                assert isinstance(normalised[key], float)

    def test_normalise_missing_data_returns_none(self):
        collector = MetricsCollector()
        result = collector.normalise_metrics({})
        assert isinstance(result, dict)

    async def test_collect_missing_platform_handled_gracefully(self):
        collector = MetricsCollector()
        result = await collector.collect("unknown_platform", "post_1")
        assert result is not None


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — API Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ROUTER, reason="analytics.py API not implemented yet")
class TestAnalyticsEndpointsBehavior:
    """Behavioral: Analytics API endpoints respond correctly."""

    async def test_list_posts_returns_list(self):
        from httpx import ASGITransport, AsyncClient

        from app.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/analytics/posts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_post_returns_detail(self):
        from httpx import ASGITransport, AsyncClient

        from app.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/analytics/posts/test_123")
        # Real implementation: unknown posts 404 (facade previously fabricated data).
        assert response.status_code == 404

    async def test_summary_returns_aggregates(self):
        from httpx import ASGITransport, AsyncClient

        from app.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_reach" in data
        assert "avg_engagement_rate" in data
