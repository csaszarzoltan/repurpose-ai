"""Pre-dev tests: analytics API must serve REAL data from the repository layer.

Part of task t_2ce088ec — "remove the analytics facade". Today
``src/app/api/analytics.py`` returns hardcoded values on every endpoint and
never touches ``app.services.analytics``, so these tests are RED until the API
is wired to the services + repository layer.

Strategy per endpoint:
  1. Seed the store through ``app.services.analytics.db.repository``
     (MetricsRepository / ScoreRepository / ValidationRepository).
  2. Build a FastAPI app from the analytics router and override the repository
     dependency providers with the seeded instances.
  3. Call the real HTTP endpoint.
  4. Assert the response VALUES equal the persisted/calculated data —
     never just HTTP 200 / field presence.

REAL IMPLEMENTATION CONTRACT (what makes these tests pass):

1. ``app.dependencies`` must expose three repository providers:
       def get_metrics_repository() -> MetricsRepository
       def get_score_repository() -> ScoreRepository
       def get_validation_repository() -> ValidationRepository
2. Every analytics router endpoint must receive its repositories via FastAPI
   ``Depends``, e.g.
       async def list_posts(store: MetricsRepository = Depends(get_metrics_repository)) ...
   Endpoints may add service-level providers (TrendService / ExportService /
   ValidationAnalyzer / ScoreCalculator), but those services MUST be built
   from the DI-provided repository so seeded data flows through.
3. Endpoints must return data read from / derived by the services and
   repositories — never hardcoded literals.
4. Static trend routes (``/trends/summary``, ``/trends/top-content``) must be
   registered BEFORE ``/trends/{metric}`` — today they are shadowed by the
   dynamic route and unreachable.
5. Unknown-resource lookups (unknown post_id / export_id) must 404 / report
   ``not_found`` instead of returning fabricated data.

The failure message on every test names the missing piece, so a run of this
file is a checklist for the implementer.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# ── Guards: what exists today ──────────────────────────────────────────────────

try:
    from app.api.analytics import router as analytics_router
    HAS_ROUTER = True
except (ImportError, ModuleNotFoundError):
    HAS_ROUTER = False

try:
    from app.services.analytics.db.repository import (
        MetricsRepository,
        ScoreRepository,
        ValidationRepository,
    )
    HAS_REPOSITORY = True
except (ImportError, ModuleNotFoundError):
    HAS_REPOSITORY = False

# ── The REAL implementation contract: DI providers (missing today → RED) ───────

try:
    from app.dependencies import (
        get_metrics_repository,
        get_score_repository,
        get_validation_repository,
    )
    HAS_DI = True
    _DI_ERROR = None
except (ImportError, ModuleNotFoundError) as _exc:
    HAS_DI = False
    _DI_ERROR = str(_exc)

_DI_MESSAGE = (
    "REAL IMPLEMENTATION MISSING: analytics DI providers not importable from "
    f"app.dependencies ({_DI_ERROR}). Add get_metrics_repository / get_score_repository / "
    "get_validation_repository and wire every analytics endpoint with "
    "Depends(...) so seeded data flows repository -> service -> API."
)


def _require_di() -> None:
    """Every behavioral test starts here: fail fast with a pinpointing message."""
    assert HAS_DI, _DI_MESSAGE


# ── Seed data ──────────────────────────────────────────────────────────────────
#
# Values are deliberately distinct from the facade's hardcoded numbers
# (reach 1000, engagement 0.05, summary 15000/0.045, score 78.5, delta 0.15)
# so any leftover hardcoding is caught by the assertions.

POST_A = {
    "platform": "linkedin",
    "post_id": "post_a",
    "reach": 12500,
    "impressions": 50000,
    "engagement_rate": 0.05,
    "completion_rate": 0.8,
    "share_rate": 0.02,
    "post_date": datetime(2026, 7, 1, tzinfo=UTC),
}
POST_B = {
    "platform": "twitter",
    "post_id": "post_b",
    "reach": 7777,
    "impressions": 30000,
    "engagement_rate": 0.11,
    "completion_rate": 0.6,
    "share_rate": 0.04,
    "post_date": datetime(2026, 7, 1, tzinfo=UTC),
}
POST_C = {
    "platform": "linkedin",
    "post_id": "post_c",
    "reach": 9000,
    "impressions": 40000,
    "engagement_rate": 0.08,
    "completion_rate": 0.7,
    "share_rate": 0.03,
    "post_date": datetime(2026, 7, 2, tzinfo=UTC),
}

ALL_POSTS = [POST_A, POST_B, POST_C]
TOTAL_REACH = sum(p["reach"] for p in ALL_POSTS)  # 29277
AVG_ENGAGEMENT = sum(p["engagement_rate"] for p in ALL_POSTS) / len(ALL_POSTS)  # 0.08

RANGE_START = datetime(2026, 7, 1, tzinfo=UTC)
RANGE_END = datetime(2026, 7, 31, tzinfo=UTC)


@dataclass
class SeededStore:
    """Three repositories seeded with the same deterministic data set."""

    metrics: MetricsRepository
    scores: ScoreRepository
    validations: ValidationRepository


async def _build_seeded_store() -> SeededStore:
    metrics = MetricsRepository()
    for post in ALL_POSTS:
        payload = {k: v for k, v in post.items() if k not in ("platform", "post_id")}
        await metrics.store_metrics(post["platform"], post["post_id"], payload)

    scores = ScoreRepository()
    await scores.store_score(
        "post_a",
        "linkedin",
        91.5,
        {"engagement_rate": 0.05, "completion_rate": 0.8},
    )

    validations = ValidationRepository()
    await validations.store_validation(
        "job_seed_1",
        "Draft text for seeding the validation store.",
        "Published text for seeding the validation store.",
        {
            "quality_delta": 0.42,
            "readability": {"flesch_kincaid": 9.9, "dale_chall": 8.0, "ari": 10.5},
            "diff_blocks": [{"type": "replace", "content": "Published"}],
        },
    )
    return SeededStore(metrics=metrics, scores=scores, validations=validations)


async def _client(store: SeededStore) -> AsyncClient:
    """Fresh app per test: analytics router + seeded repository overrides."""
    _require_di()
    test_app = FastAPI()
    test_app.include_router(analytics_router)
    test_app.dependency_overrides[get_metrics_repository] = lambda: store.metrics
    test_app.dependency_overrides[get_score_repository] = lambda: store.scores
    test_app.dependency_overrides[get_validation_repository] = lambda: store.validations
    return AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test")


# ═══════════════════════════════════════════════════════════════════════════════
# /posts — list and detail must come from MetricsRepository
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ROUTER or not HAS_REPOSITORY, reason="analytics API/repository not implemented yet")
class TestListPostsRealData:
    async def test_list_posts_returns_all_seeded_posts(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/posts")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 3, (
            "GET /posts must return every post persisted via MetricsRepository "
            f"(seeded 3); got {len(data)} item(s) — endpoint returns a hardcoded list"
        )
        ids = {p.get("post_id") for p in data}
        assert ids == {"post_a", "post_b", "post_c"}, f"seeded post ids missing from response: {ids}"

    async def test_list_posts_returns_seeded_metrics_values(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/posts")
        data = resp.json()
        by_id = {p["post_id"]: p for p in data}
        assert by_id["post_a"]["platform"] == "linkedin"
        assert by_id["post_a"]["reach"] == 12500, (
            "GET /posts must return the persisted reach (12500); got {!r} — "
            "value is hardcoded".format(by_id["post_a"].get("reach"))
        )
        assert by_id["post_b"]["platform"] == "twitter"
        assert by_id["post_b"]["reach"] == 7777
        assert by_id["post_b"]["engagement_rate"] == pytest.approx(0.11)

    async def test_get_post_returns_seeded_metrics_for_that_post(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/posts/post_b")
        assert resp.status_code == 200
        data = resp.json()
        assert data["post_id"] == "post_b"
        assert data["platform"] == "twitter", (
            "GET /posts/{{id}} must return the persisted platform for that post "
            "(twitter); got {!r} — handler returns hardcoded linkedin data".format(data.get("platform"))
        )
        assert data["reach"] == 7777
        assert data["engagement_rate"] == pytest.approx(0.11)

    async def test_get_unknown_post_returns_404(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/posts/does_not_exist")
        assert resp.status_code == 404, (
            f"GET /posts/{{id}} must 404 for unknown posts; got {resp.status_code} — "
            "handler fabricates data for any id"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# /summary — aggregates must be computed from persisted metrics
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ROUTER or not HAS_REPOSITORY, reason="analytics API/repository not implemented yet")
class TestSummaryRealData:
    async def test_summary_total_reach_matches_seeded_sum(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("total_reach") == TOTAL_REACH, (
            "GET /summary must sum reach over the repository "
            f"(seeded total {TOTAL_REACH}); got {data.get('total_reach')!r} — aggregate is hardcoded"
        )

    async def test_summary_avg_engagement_matches_seeded_mean(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/summary")
        data = resp.json()
        assert data.get("avg_engagement_rate") == pytest.approx(AVG_ENGAGEMENT), (
            "GET /summary must average engagement_rate over the repository "
            "(seeded mean {:.4f}); got {!r}".format(AVG_ENGAGEMENT, data.get("avg_engagement_rate"))
        )


# ═══════════════════════════════════════════════════════════════════════════════
# /optimization-score — stored scores and ScoreCalculator output
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ROUTER or not HAS_REPOSITORY, reason="analytics API/repository not implemented yet")
class TestOptimizationScoreRealData:
    async def test_get_optimization_score_returns_stored_score(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/optimization-score/post_a")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("overall_score") == pytest.approx(91.5), (
            "GET /optimization-score/{{post_id}} must return the score persisted "
            "via ScoreRepository (91.5); got {!r} — value is hardcoded".format(data.get("overall_score"))
        )
        assert data.get("signals", {}).get("engagement_rate") == pytest.approx(0.05)
        assert data.get("platform") == "linkedin"

    async def test_calculate_optimization_score_uses_score_calculator(self):
        from app.services.analytics.score_calculator import ScoreCalculator

        platform = "twitter"
        metrics = {"engagement_rate": 0.05, "completion_rate": 0.8, "share_rate": 0.02}
        expected = await ScoreCalculator().calculate(platform, metrics)

        async with await _client(await _build_seeded_store()) as client:
            resp = await client.post(
                "/api/v1/analytics/optimization-score/calculate",
                json={"platform": platform, "metrics": metrics},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("overall_score") == pytest.approx(expected["overall_score"]), (
            "POST /optimization-score/calculate must delegate to ScoreCalculator "
            f"(expected {expected['overall_score']:.4f} for the submitted metrics); "
            f"got {data.get('overall_score')!r} — value is hardcoded"
        )
        assert data.get("platform") == platform, (
            "calculated score must carry the submitted platform; got {!r}".format(data.get("platform"))
        )
        assert data.get("signals", {}).get("engagement_rate") == pytest.approx(0.05)


# ═══════════════════════════════════════════════════════════════════════════════
# /validate + /validation/{job_id} — reports derived from content / persistence
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ROUTER or not HAS_REPOSITORY, reason="analytics API/repository not implemented yet")
class TestValidationRealData:
    async def test_validate_readability_computed_from_draft(self):
        from app.services.analytics.validation_analyzer import ValidationAnalyzer

        draft = "This is a simple test sentence."
        published = "This is a heavily edited and expanded published version of the content."
        expected = ValidationAnalyzer().compute_readability_scores(draft)

        async with await _client(await _build_seeded_store()) as client:
            resp = await client.post(
                "/api/v1/analytics/validate",
                json={"draft": draft, "published": published, "run_llm_judge": False},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("readability", {}).get("flesch_kincaid") == pytest.approx(
            expected["flesch_kincaid"], abs=0.01
        ), (
            "POST /validate must compute readability from the submitted draft "
            f"(expected {expected['flesch_kincaid']:.2f}); "
            f"got {data.get('readability', {}).get('flesch_kincaid')!r} — report is hardcoded"
        )

    async def test_validate_identical_texts_have_zero_quality_delta(self):
        text = "Identical content in both the draft and the published version."
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.post(
                "/api/v1/analytics/validate",
                json={"draft": text, "published": text, "run_llm_judge": False},
            )
        data = resp.json()
        assert data.get("quality_delta") == pytest.approx(0.0), (
            "POST /validate with draft == published must yield quality_delta 0.0; "
            "got {!r} — delta is the hardcoded facade value 0.15".format(data.get("quality_delta"))
        )

    async def test_get_validation_returns_stored_report(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/validation/job_seed_1")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("quality_delta") == pytest.approx(0.42), (
            "GET /validation/{{job_id}} must return the report persisted via "
            "ValidationRepository (quality_delta 0.42); got {!r} — report is hardcoded".format(data.get("quality_delta"))
        )
        assert data.get("readability", {}).get("flesch_kincaid") == pytest.approx(9.9)

    async def test_get_unknown_validation_returns_404(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/validation/does_not_exist")
        assert resp.status_code == 404, (
            f"GET /validation/{{job_id}} must 404 for unknown job ids; got {resp.status_code}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# /export — CSV/PDF exports and schedules backed by ExportService + data store
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ROUTER or not HAS_REPOSITORY, reason="analytics API/repository not implemented yet")
class TestExportRealData:
    async def test_export_csv_contains_seeded_rows(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.post(
                "/api/v1/analytics/export/csv",
                json={
                    "metric_selection": ["reach"],
                    "date_range": ["2026-07-01", "2026-07-31"],
                    "platform_filter": "linkedin",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "content" in data, (
            "POST /export/csv must return JSON with a 'content' field holding the "
            f"CSV text produced from the data store; got keys {list(data)!r} — endpoint returns "
            "a fabricated export_id without exporting anything"
        )
        csv_text = data["content"]
        assert "12500" in csv_text and "9000" in csv_text, (
            f"CSV export must contain the persisted reach rows (12500, 9000); got {csv_text!r} — "
            "ExportService writes zero-filled rows instead of reading the data store"
        )

    async def test_export_pdf_returns_file_path(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.post(
                "/api/v1/analytics/export/pdf",
                json={"metric_selection": ["reach"], "date_range": ["2026-07-01", "2026-07-31"]},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "file_path" in data, (
            "POST /export/pdf must return JSON with a 'file_path' to the generated "
            f"report; got keys {list(data)!r}"
        )
        assert data["file_path"].endswith(".pdf")

    async def test_export_schedule_returns_unique_id(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.post(
                "/api/v1/analytics/export/schedule",
                json={"export_type": "csv", "cadence": "daily", "metric_selection": ["reach"]},
            )
        assert resp.status_code == 200
        data = resp.json()
        schedule_id = data.get("schedule_id", "")
        assert schedule_id != "schedule_new", (
            "POST /export/schedule must return the schedule id created by "
            "ExportService.create_schedule; 'schedule_new' is the hardcoded facade value"
        )
        uuid.UUID(schedule_id)  # raises ValueError if the id is not a real uuid

    async def test_get_unknown_export_returns_not_found(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/export/export_missing_123")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "not_found", (
            "GET /export/{{export_id}} must report 'not_found' for unknown ids "
            "(ExportService.get_export_status contract); got {!r} — facade claims "
            "'completed' for everything".format(data.get("status"))
        )


# ═══════════════════════════════════════════════════════════════════════════════
# /trends — series, summary, and top content derived from persisted metrics
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ROUTER or not HAS_REPOSITORY, reason="analytics API/repository not implemented yet")
class TestTrendsRealData:
    async def test_trend_points_match_seeded_reach_by_day(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/trends/reach")
        assert resp.status_code == 200
        data = resp.json()
        by_date = {p["date"]: p["value"] for p in data.get("points", [])}
        assert by_date.get("2026-07-01") == pytest.approx(12500 + 7777), (
            "GET /trends/{{metric}} must aggregate the persisted metric per day from "
            "the repository (2026-07-01 reach = 20277); got points {!r} — series is hardcoded".format(data.get("points"))
        )
        assert by_date.get("2026-07-02") == pytest.approx(9000)

    async def test_trends_summary_reflects_seeded_data(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/trends/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_posts" in data, (
            f"GET /trends/summary must return the aggregate dict; got {data!r} — the route "
            "is shadowed by /trends/{metric} (static trend routes must be registered "
            "before the dynamic one) or still returns hardcoded values"
        )
        assert data["total_posts"] == 3, (
            "trends summary must count posts from the repository (seeded 3); got {!r}".format(data.get("total_posts"))
        )
        assert data["total_reach"] == TOTAL_REACH

    async def test_top_content_ranks_seeded_posts(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/trends/top-content?metric=reach&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list), (
            f"GET /trends/top-content must return a ranked list of posts; got {data!r} — "
            "the route is shadowed by /trends/{metric} or still returns hardcoded items"
        )
        assert len(data) == 2
        assert data[0]["post_id"] == "post_a" and data[0].get("reach") == pytest.approx(12500.0), (
            "top content must be ranked by the requested metric from the repository "
            f"(post_a reach 12500 first); got {data!r}"
        )
        assert data[1]["post_id"] == "post_c"


# ═══════════════════════════════════════════════════════════════════════════════
# Facade guards — source-level acceptance checks
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ROUTER, reason="analytics.py API not implemented yet")
class TestRouterIsNotAFacade:
    """The router must reference the services/dependencies layer.

    The retrospective (2026-08-03) names this exact signal: a facade router
    has zero references to the services layer while all shape tests pass.
    """

    def test_router_source_references_services_or_dependencies(self):
        import inspect

        import app.api.analytics as analytics_module

        source = inspect.getsource(analytics_module)
        assert "app.services" in source or "app.dependencies" in source, (
            "analytics.py is a facade: its source never references app.services / "
            "app.dependencies. Wire the endpoints to repository/service providers."
        )

    def test_router_source_has_no_hardcoded_post_metrics_return(self):
        import inspect

        import app.api.analytics as analytics_module

        source = inspect.getsource(analytics_module)
        assert "PostMetrics(reach=1000" not in source, (
            "analytics.py still contains the hardcoded PostMetrics(reach=1000, ...) "
            "facade return — endpoints must build responses from repository data."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Malformed from_date/to_date params — must 422, never 500 (review finding B1)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_ROUTER or not HAS_REPOSITORY, reason="analytics API/repository not implemented yet")
class TestMalformedDateParamsReturn422:
    """Malformed from_date/to_date must yield 422, never an unhandled 500.

    Regression for tech-lead review finding B1 (t_babe742e): every endpoint
    that accepts from_date/to_date funnels through ``_parse_date``, which used
    to let ``datetime.fromisoformat``'s ValueError escape as HTTP 500.
    """

    async def _assert_422(self, path: str, query: str) -> None:
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get(f"/api/v1/analytics{path}?{query}")
        assert resp.status_code == 422, (
            f"GET {path}?{query} must return 422 for malformed dates; got "
            f"{resp.status_code} — _parse_date is leaking ValueError as a 500"
        )

    async def test_summary_rejects_garbage_from_date(self):
        await self._assert_422("/summary", "from_date=garbage")

    async def test_summary_rejects_garbage_to_date(self):
        await self._assert_422("/summary", "to_date=notadate")

    async def test_summary_rejects_impossible_date(self):
        await self._assert_422("/summary", "from_date=2026-13-99")

    async def test_trends_summary_rejects_garbage_to_date(self):
        await self._assert_422("/trends/summary", "to_date=notadate")

    async def test_trends_top_content_rejects_garbage_from_date(self):
        await self._assert_422("/trends/top-content", "from_date=x")

    async def test_trends_metric_rejects_impossible_date(self):
        await self._assert_422("/trends/reach", "from_date=2026-13-99")

    async def test_control_summary_without_dates_stays_200(self):
        async with await _client(await _build_seeded_store()) as client:
            resp = await client.get("/api/v1/analytics/summary")
        assert resp.status_code == 200, (
            "control: GET /summary with no date params must stay 200; got "
            f"{resp.status_code}"
        )
