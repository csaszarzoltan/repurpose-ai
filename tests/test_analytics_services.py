"""Pre-dev tests for analytics service layer — interfaces + real data flow.

This file is part of the "remove the analytics facade" TDD cycle (task
t_2ce088ec). It contains two halves:

1. INTERFACE tests (must PASS immediately on current code):
   public signatures/imports of MetricsCollector, the repository classes,
   TrendService, ExportService, ValidationAnalyzer, and the analytics router's
   route table. These verify the *shape* of the public API only.

2. BEHAVIORAL data-flow tests (must FAIL on current code — RED phase):
   services that receive a ``data_store`` (repository) must derive their
   output from that store. Today TrendService returns hardcoded points and
   ExportService writes zero rows; both ignore the injected data store.
   These tests pin the contract: **real data must flow repository -> service**.

Existing shape-only tests (test_analytics_*.py) assert HTTP 200 / key presence
and therefore pass against the facade; the tests here assert *values* so they
stay RED until the real implementation lands.

Source of truth: analysis/analysis-brief.md §4 P0.2, P1.1, P1.2, P1.3, P2.1, P2.2.
"""

from __future__ import annotations

import inspect
from datetime import UTC, datetime

import pytest

# ── Module availability guards (same convention as the existing suite) ────────

try:
    from app.services.analytics.metrics_collector import MetricsCollector
    HAS_COLLECTOR = True
except (ImportError, ModuleNotFoundError):
    HAS_COLLECTOR = False

try:
    from app.services.analytics.db.repository import (
        MetricsRepository,
        ScoreRepository,
        ValidationRepository,
    )
    HAS_REPOSITORY = True
except (ImportError, ModuleNotFoundError):
    HAS_REPOSITORY = False

try:
    from app.services.analytics.trend_service import TrendService
    HAS_TREND = True
except (ImportError, ModuleNotFoundError):
    HAS_TREND = False

try:
    from app.services.analytics.export_service import ExportService
    HAS_EXPORT = True
except (ImportError, ModuleNotFoundError):
    HAS_EXPORT = False

try:
    from app.services.analytics.validation_analyzer import ValidationAnalyzer
    HAS_VALIDATION = True
except (ImportError, ModuleNotFoundError):
    HAS_VALIDATION = False

try:
    from app.api.analytics import router as analytics_router
    HAS_ROUTER = True
except (ImportError, ModuleNotFoundError):
    HAS_ROUTER = False

try:
    from app.models.analytics import PostMetrics, TrendData
    HAS_MODELS = True
except (ImportError, ModuleNotFoundError):
    HAS_MODELS = False

# ═══════════════════════════════════════════════════════════════════════════════
# PART 1 — INTERFACE TESTS (pass immediately)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_COLLECTOR, reason="metrics_collector.py not implemented yet")
class TestMetricsCollectorInterface:
    """Interface: MetricsCollector.collect(platform, post_id) contract."""

    def test_importable(self):
        assert MetricsCollector is not None

    def test_collect_is_coroutine(self):
        assert inspect.iscoroutinefunction(MetricsCollector.collect)

    def test_collect_signature_has_platform_and_post_id(self):
        sig = inspect.signature(MetricsCollector.collect)
        assert "platform" in sig.parameters
        assert "post_id" in sig.parameters

    def test_collect_range_signature(self):
        sig = inspect.signature(MetricsCollector.collect_range)
        for name in ("platform", "from_date", "to_date"):
            assert name in sig.parameters

    def test_normalise_metrics_is_sync_and_takes_raw(self):
        assert callable(MetricsCollector.normalise_metrics)
        assert not inspect.iscoroutinefunction(MetricsCollector.normalise_metrics)
        sig = inspect.signature(MetricsCollector.normalise_metrics)
        assert "raw" in sig.parameters


@pytest.mark.xfail(not HAS_REPOSITORY, reason="repository.py not implemented yet")
class TestRepositoryInterface:
    """Interface: repository methods used by the analytics API."""

    def test_metrics_repository_importable(self):
        assert MetricsRepository is not None

    def test_store_metrics_signature(self):
        sig = inspect.signature(MetricsRepository.store_metrics)
        for name in ("platform", "post_id", "metrics"):
            assert name in sig.parameters
        assert inspect.iscoroutinefunction(MetricsRepository.store_metrics)

    def test_query_metrics_signature_with_granularity_default(self):
        sig = inspect.signature(MetricsRepository.query_metrics)
        for name in ("platform", "from_date", "to_date", "granularity"):
            assert name in sig.parameters
        assert sig.parameters["granularity"].default == "daily"
        assert inspect.iscoroutinefunction(MetricsRepository.query_metrics)

    def test_score_repository_importable(self):
        assert ScoreRepository is not None

    def test_store_score_signature(self):
        sig = inspect.signature(ScoreRepository.store_score)
        for name in ("post_id", "platform", "overall_score", "signals"):
            assert name in sig.parameters
        assert inspect.iscoroutinefunction(ScoreRepository.store_score)

    def test_query_score_signature(self):
        sig = inspect.signature(ScoreRepository.query_score)
        for name in ("post_id", "platform"):
            assert name in sig.parameters
        assert inspect.iscoroutinefunction(ScoreRepository.query_score)

    def test_validation_repository_importable(self):
        assert ValidationRepository is not None

    def test_store_validation_signature(self):
        sig = inspect.signature(ValidationRepository.store_validation)
        for name in ("job_id", "draft", "published", "scores"):
            assert name in sig.parameters
        assert inspect.iscoroutinefunction(ValidationRepository.store_validation)

    def test_query_validation_signature(self):
        sig = inspect.signature(ValidationRepository.query_validation)
        assert "job_id" in sig.parameters
        assert inspect.iscoroutinefunction(ValidationRepository.query_validation)


@pytest.mark.xfail(not HAS_TREND, reason="trend_service.py not implemented yet")
class TestTrendServiceInterface:
    """Interface: TrendService public methods."""

    def test_importable(self):
        assert TrendService is not None

    def test_init_accepts_data_store(self):
        sig = inspect.signature(TrendService.__init__)
        assert "data_store" in sig.parameters

    def test_get_trend_signature(self):
        sig = inspect.signature(TrendService.get_trend)
        for name in ("metric", "granularity", "from_date", "to_date"):
            assert name in sig.parameters
        assert inspect.iscoroutinefunction(TrendService.get_trend)

    def test_get_summary_signature(self):
        inspect.signature(TrendService.get_summary)
        assert inspect.iscoroutinefunction(TrendService.get_summary)

    def test_get_top_content_signature(self):
        sig = inspect.signature(TrendService.get_top_content)
        for name in ("metric", "limit", "from_date", "to_date"):
            assert name in sig.parameters
        assert inspect.iscoroutinefunction(TrendService.get_top_content)


@pytest.mark.xfail(not HAS_EXPORT, reason="export_service.py not implemented yet")
class TestExportServiceInterface:
    """Interface: ExportService public methods."""

    def test_importable(self):
        assert ExportService is not None

    def test_init_accepts_data_store(self):
        sig = inspect.signature(ExportService.__init__)
        assert "data_store" in sig.parameters

    def test_export_csv_signature(self):
        sig = inspect.signature(ExportService.export_csv)
        for name in ("metric_selection", "date_range", "platform_filter"):
            assert name in sig.parameters
        assert inspect.iscoroutinefunction(ExportService.export_csv)

    def test_get_export_status_signature(self):
        sig = inspect.signature(ExportService.get_export_status)
        assert "export_id" in sig.parameters
        assert inspect.iscoroutinefunction(ExportService.get_export_status)

    def test_schedule_methods_signatures(self):
        assert inspect.iscoroutinefunction(ExportService.create_schedule)
        assert inspect.iscoroutinefunction(ExportService.delete_schedule)
        assert inspect.iscoroutinefunction(ExportService.list_schedules)
        sig = inspect.signature(ExportService.create_schedule)
        for name in ("export_type", "cadence", "metric_selection"):
            assert name in sig.parameters


@pytest.mark.xfail(not HAS_VALIDATION, reason="validation_analyzer.py not implemented yet")
class TestValidationAnalyzerInterface:
    """Interface: ValidationAnalyzer public methods."""

    def test_importable(self):
        assert ValidationAnalyzer is not None

    def test_validate_signature(self):
        sig = inspect.signature(ValidationAnalyzer.validate)
        for name in ("draft", "published", "source_material", "run_llm_judge"):
            assert name in sig.parameters
        assert inspect.iscoroutinefunction(ValidationAnalyzer.validate)

    def test_compute_readability_signature(self):
        sig = inspect.signature(ValidationAnalyzer.compute_readability_scores)
        assert "text" in sig.parameters


@pytest.mark.xfail(not HAS_ROUTER, reason="analytics.py API not implemented yet")
class TestAnalyticsRouterInterface:
    """Interface: analytics router registers every endpoint of the brief."""

    def _routes(self) -> list[tuple[str, set[str]]]:
        return [(r.path, set(getattr(r, "methods", set()) or [])) for r in analytics_router.routes]

    def test_router_importable(self):
        assert analytics_router is not None

    def test_router_prefix(self):
        assert analytics_router.prefix == "/api/v1/analytics"

    def test_list_posts_route(self):
        paths = [p for p, _ in self._routes()]
        assert "/api/v1/analytics/posts" in paths or "/posts" in paths

    def test_get_post_route(self):
        paths = [p for p, _ in self._routes()]
        assert any("/posts/{post_id}" in p for p in paths)

    def test_summary_route(self):
        paths = [p for p, _ in self._routes()]
        assert any(p == "/api/v1/analytics/summary" or p == "/summary" for p in paths)

    def test_optimization_score_routes(self):
        paths = [p for p, _ in self._routes()]
        assert any("/optimization-score/calculate" in p for p in paths)
        assert any("/optimization-score/{post_id}" in p for p in paths)

    def test_validate_routes(self):
        paths = [p for p, _ in self._routes()]
        assert any(p == "/api/v1/analytics/validate" or p == "/validate" for p in paths)
        assert any("/validation/{job_id}" in p for p in paths)

    def test_export_routes(self):
        paths = [p for p, _ in self._routes()]
        assert any("/export/csv" in p for p in paths)
        assert any("/export/pdf" in p for p in paths)
        assert any("/export/schedule" in p for p in paths)
        assert any("/export/{export_id}" in p for p in paths)

    def test_trend_routes(self):
        paths = [p for p, _ in self._routes()]
        assert any("/trends/{metric}" in p for p in paths)
        assert any(p == "/api/v1/analytics/trends/summary" or p == "/trends/summary" for p in paths)
        assert any(p == "/api/v1/analytics/trends/top-content" or p == "/trends/top-content" for p in paths)

    def test_trend_routes_use_get_method(self):
        for path, methods in self._routes():
            if "/trends" in path:
                assert "GET" in methods, f"{path} must accept GET"

    def test_export_routes_use_expected_methods(self):
        by_path = {p: m for p, m in self._routes()}
        for path, expected in (
            ("/api/v1/analytics/export/csv", "POST"),
            ("/api/v1/analytics/export/pdf", "POST"),
        ):
            assert expected in by_path.get(path, set()), f"{path} must accept {expected}"


@pytest.mark.xfail(not HAS_MODELS, reason="analytics models not implemented yet")
class TestAnalyticsModelsInterface:
    """Interface: response models expose the fields the API contract relies on."""

    def test_post_metrics_has_key_fields(self):
        for field in ("post_id", "platform", "reach", "impressions", "engagement_rate"):
            assert field in PostMetrics.model_fields

    def test_trend_data_has_points_field(self):
        assert "points" in TrendData.model_fields


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2 — BEHAVIORAL DATA-FLOW TESTS (RED until services read the data store)
# ═══════════════════════════════════════════════════════════════════════════════
#
# These tests construct a service with a *seeded* MetricsRepository and assert
# the service output is derived from that store. On the current code they fail
# because TrendService returns hardcoded series and ExportService writes zero
# rows — neither reads ``data_store``.

_SEEDED_POSTS = [
    {
        "platform": "linkedin",
        "post_id": "post_a",
        "reach": 12500,
        "impressions": 50000,
        "engagement_rate": 0.05,
        "completion_rate": 0.8,
        "share_rate": 0.02,
        "post_date": datetime(2026, 7, 1, tzinfo=UTC),
    },
    {
        "platform": "twitter",
        "post_id": "post_b",
        "reach": 7777,
        "impressions": 30000,
        "engagement_rate": 0.11,
        "completion_rate": 0.6,
        "share_rate": 0.04,
        "post_date": datetime(2026, 7, 1, tzinfo=UTC),
    },
    {
        "platform": "linkedin",
        "post_id": "post_c",
        "reach": 9000,
        "impressions": 40000,
        "engagement_rate": 0.08,
        "completion_rate": 0.7,
        "share_rate": 0.03,
        "post_date": datetime(2026, 7, 2, tzinfo=UTC),
    },
]

TOTAL_REACH = sum(p["reach"] for p in _SEEDED_POSTS)  # 29277
AVG_ENGAGEMENT = sum(p["engagement_rate"] for p in _SEEDED_POSTS) / len(_SEEDED_POSTS)  # 0.08


async def _seed_metrics_repository() -> MetricsRepository:
    repo = MetricsRepository()
    for post in _SEEDED_POSTS:
        metrics = {k: v for k, v in post.items() if k not in ("platform", "post_id")}
        await repo.store_metrics(post["platform"], post["post_id"], metrics)
    return repo


@pytest.mark.xfail(not HAS_REPOSITORY, reason="repository.py not implemented yet")
class TestMetricsRepositoryRoundTrip:
    """Storage contract: seeded metrics come back verbatim via query."""

    async def test_store_then_query_returns_seeded_values(self):
        repo = await _seed_metrics_repository()
        rows = await repo.query_metrics(
            "linkedin",
            from_date=datetime(2026, 7, 1, tzinfo=UTC),
            to_date=datetime(2026, 7, 31, tzinfo=UTC),
        )
        assert len(rows) == 2, "two linkedin posts were seeded"
        by_id = {r["post_id"]: r for r in rows}
        assert by_id["post_a"]["reach"] == 12500
        assert by_id["post_c"]["engagement_rate"] == 0.08

    async def test_platform_filter_respected(self):
        repo = await _seed_metrics_repository()
        rows = await repo.query_metrics(
            "twitter",
            from_date=datetime(2026, 7, 1, tzinfo=UTC),
            to_date=datetime(2026, 7, 31, tzinfo=UTC),
        )
        assert len(rows) == 1
        assert rows[0]["post_id"] == "post_b"


@pytest.mark.xfail(not HAS_REPOSITORY, reason="repository.py not implemented yet")
class TestScoreRepositoryRoundTrip:
    """Storage contract: scores persist and round-trip."""

    async def test_store_then_query_score(self):
        repo = ScoreRepository()
        await repo.store_score("post_a", "linkedin", 91.5, {"engagement_rate": 0.05, "completion_rate": 0.8})
        row = await repo.query_score("post_a", "linkedin")
        assert row.get("overall_score") == 91.5
        assert row.get("signals", {}).get("engagement_rate") == 0.05

    async def test_query_unknown_score_returns_empty_dict(self):
        repo = ScoreRepository()
        row = await repo.query_score("nope", "linkedin")
        assert row == {}


@pytest.mark.xfail(not HAS_TREND, reason="trend_service.py not implemented yet")
class TestTrendServiceReadsStore:
    """RED: TrendService must derive series from the injected data store."""

    async def test_get_trend_points_match_seeded_reach(self):
        svc = TrendService(data_store=await _seed_metrics_repository())
        result = await svc.get_trend(
            "reach",
            granularity="daily",
            from_date=datetime(2026, 7, 1, tzinfo=UTC),
            to_date=datetime(2026, 7, 31, tzinfo=UTC),
        )
        by_date = {p["date"]: p["value"] for p in result["points"]}
        assert by_date.get("2026-07-01") == pytest.approx(12500 + 7777), (
            "get_trend must aggregate reach from the data store per day; "
            "got points {!r} (hardcoded series means TrendService ignores data_store)".format(result["points"])
        )
        assert by_date.get("2026-07-02") == pytest.approx(9000)

    async def test_get_summary_reflects_seeded_data(self):
        svc = TrendService(data_store=await _seed_metrics_repository())
        result = await svc.get_summary(
            from_date=datetime(2026, 7, 1, tzinfo=UTC),
            to_date=datetime(2026, 7, 31, tzinfo=UTC),
        )
        assert result.get("total_posts") == 3, (
            "get_summary must count posts from the data store; got {!r} "
            "(hardcoded 42 means TrendService ignores data_store)".format(result.get("total_posts"))
        )
        assert result.get("total_reach") == pytest.approx(TOTAL_REACH)
        assert result.get("avg_engagement_rate") == pytest.approx(AVG_ENGAGEMENT)

    async def test_get_top_content_ranks_seeded_posts(self):
        svc = TrendService(data_store=await _seed_metrics_repository())
        result = await svc.get_top_content(
            "reach",
            limit=2,
            from_date=datetime(2026, 7, 1, tzinfo=UTC),
            to_date=datetime(2026, 7, 31, tzinfo=UTC),
        )
        assert isinstance(result, list) and len(result) == 2
        assert result[0]["post_id"] == "post_a" and result[0]["reach"] == pytest.approx(12500.0), (
            f"top content must be ranked by metric from the data store; got {result!r}"
        )
        assert result[1]["post_id"] == "post_c"


@pytest.mark.xfail(not HAS_EXPORT, reason="export_service.py not implemented yet")
class TestExportServiceReadsStore:
    """RED: CSV export must contain rows persisted in the data store."""

    async def test_export_csv_contains_seeded_rows(self):
        svc = ExportService(data_store=await _seed_metrics_repository())
        csv_text = await svc.export_csv(
            metric_selection=["reach"],
            date_range=(datetime(2026, 7, 1, tzinfo=UTC), datetime(2026, 7, 31, tzinfo=UTC)),
            platform_filter="linkedin",
        )
        assert "12500" in csv_text, (
            "export_csv must write rows from the data store (seeded reach 12500); "
            f"got {csv_text!r} — zero-filled rows mean ExportService ignores data_store"
        )
        assert "9000" in csv_text

    async def test_export_status_unknown_returns_not_found(self):
        svc = ExportService(data_store=await _seed_metrics_repository())
        status = await svc.get_export_status("export_missing")
        assert status.get("status") == "not_found", (
            f"get_export_status must report not_found for unknown ids; got {status!r}"
        )


@pytest.mark.xfail(not HAS_VALIDATION, reason="validation_analyzer.py not implemented yet")
class TestValidationAnalyzerReadsInput:
    """RED: validation reports must be derived from the submitted content."""

    async def test_identical_draft_and_published_have_zero_delta(self):
        analyzer = ValidationAnalyzer()
        text = "Same content in both versions for this test."
        result = await analyzer.validate(draft=text, published=text)
        assert result.get("quality_delta") == pytest.approx(0.0), (
            "identical draft/published must yield quality_delta 0.0; got {!r} "
            "(0.15 is the hardcoded facade value)".format(result.get("quality_delta"))
        )
        assert result.get("diff_blocks") == []
