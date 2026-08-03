"""Analytics REST API router — content performance, scoring, validation, export, trends.

Source of truth: analysis/analysis-brief.md §4 P0.2, P1.1, P1.2, P1.3, P2.1, P2.2.

Every endpoint receives its repositories via FastAPI ``Depends`` and derives
its response from the injected data — the API is a thin read/aggregate layer
over the services and the analytics SQLite store. Static trend routes
(``/trends/summary``, ``/trends/top-content``) are registered **before** the
dynamic ``/trends/{metric}`` route so they are not shadowed by it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import (
    get_metrics_repository,
    get_score_repository,
    get_validation_repository,
)
from app.models.analytics import (
    AnalyticsSummary,
    ExportRequest,
    ExportScheduleRequest,
    OptimizationScore,
    PostMetrics,
    ScoreRequest,
    TrendData,
    ValidationReport,
    ValidationRequest,
)
from app.services.analytics.export_service import ExportService
from app.services.analytics.score_calculator import ScoreCalculator
from app.services.analytics.trend_service import TrendService
from app.services.analytics.validation_analyzer import ValidationAnalyzer

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


def _parse_date(value: str | None) -> datetime | None:
    """Parse an ISO date string into a tz-aware datetime (None stays None).

    Date-only strings (``2026-07-01``) are interpreted as UTC so they are
    comparable with the tz-aware ``post_date`` values stored by the repository.
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=(
                "Invalid date format: expected ISO 8601 "
                "(e.g. 2026-07-01 or 2026-07-01T00:00:00Z)"
            ),
        ) from None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _parse_range(values: list[str] | None) -> tuple[datetime | None, datetime | None]:
    if not values:
        return None, None
    start = _parse_date(values[0]) if len(values) > 0 else None
    end = _parse_date(values[1]) if len(values) > 1 else None
    return start, end


def _in_range(post_date: datetime | None, start: datetime | None, end: datetime | None) -> bool:
    if post_date is None:
        return True
    if start is not None and post_date < start:
        return False
    return not (end is not None and post_date > end)


@router.get("/posts", response_model=list[PostMetrics])
async def list_posts(
    store = Depends(get_metrics_repository),
) -> list[PostMetrics]:
    """List all tracked posts with their metrics."""
    rows = await store.list_all()
    return [PostMetrics(**row) for row in rows]


@router.get("/posts/{post_id}", response_model=PostMetrics)
async def get_post(
    post_id: str,
    store = Depends(get_metrics_repository),
) -> PostMetrics:
    """Get detailed metrics for a specific post."""
    row = await store.get_by_post_id(post_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostMetrics(**row)


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    store = Depends(get_metrics_repository),
) -> AnalyticsSummary:
    """Get aggregate summary of metrics over a date range."""
    rows = await store.list_all()
    start, end = _parse_date(from_date), _parse_date(to_date)
    if start is not None or end is not None:
        rows = [r for r in rows if _in_range(r.get("post_date"), start, end)]
    rates = [
        float(r["engagement_rate"]) for r in rows if r.get("engagement_rate") is not None
    ]
    dates = [r["post_date"] for r in rows if r.get("post_date") is not None]
    return AnalyticsSummary(
        total_reach=sum(int(r.get("reach") or 0) for r in rows),
        avg_engagement_rate=round(sum(rates) / len(rates), 6) if rates else 0.0,
        follower_growth=0,
        period_start=min(dates) if dates else None,
        period_end=max(dates) if dates else None,
    )


@router.post("/optimization-score/calculate", response_model=OptimizationScore)
async def calculate_optimization_score(payload: ScoreRequest) -> OptimizationScore:
    """Calculate algorithm-readiness score for a post."""
    result = await ScoreCalculator().calculate(payload.platform, payload.metrics)
    return OptimizationScore(
        overall_score=result["overall_score"],
        signals=result["signals"],
        platform=payload.platform,
        calculated_at=datetime.now(UTC),
    )


@router.get("/optimization-score/{post_id}", response_model=OptimizationScore)
async def get_optimization_score(
    post_id: str,
    scores = Depends(get_score_repository),
) -> OptimizationScore:
    """Get stored optimization score for a post."""
    row = await scores.query_score_by_post(post_id)
    if not row:
        raise HTTPException(status_code=404, detail="Optimization score not found")
    return OptimizationScore(
        overall_score=row["overall_score"],
        signals=row.get("signals") or {},
        platform=row.get("platform", ""),
        calculated_at=datetime.now(UTC),
    )


@router.post("/validate", response_model=ValidationReport)
async def validate_content(
    payload: ValidationRequest,
    validations = Depends(get_validation_repository),
) -> ValidationReport:
    """Validate AI-generated content against published version."""
    analyzer = ValidationAnalyzer()
    result = await analyzer.validate(
        draft=payload.draft,
        published=payload.published,
        source_material=payload.source_material,
        run_llm_judge=payload.run_llm_judge,
    )
    job_id = str(uuid4())
    await validations.store_validation(job_id, payload.draft, payload.published, result)
    return ValidationReport(**result)


@router.get("/validation/{job_id}", response_model=ValidationReport)
async def get_validation(
    job_id: str,
    validations = Depends(get_validation_repository),
) -> ValidationReport:
    """Get validation report by job ID."""
    row = await validations.query_validation(job_id)
    if not row:
        raise HTTPException(status_code=404, detail="Validation report not found")
    fields = {k: v for k, v in row.items() if k in ValidationReport.model_fields}
    return ValidationReport(**fields)


@router.post("/export/csv")
async def export_csv(
    payload: ExportRequest,
    store = Depends(get_metrics_repository),
) -> dict:
    """Export analytics data as CSV."""
    svc = ExportService(data_store=store)
    csv_text = await svc.export_csv(
        metric_selection=payload.metric_selection,
        date_range=_parse_range(payload.date_range),
        platform_filter=payload.platform_filter,
    )
    return {"export_id": str(uuid4()), "status": "completed", "content": csv_text}


@router.post("/export/pdf")
async def export_pdf(
    payload: ExportRequest,
    store = Depends(get_metrics_repository),
) -> dict:
    """Export analytics report as PDF."""
    svc = ExportService(data_store=store)
    file_path = await svc.export_pdf(
        metric_selection=payload.metric_selection,
        date_range=_parse_range(payload.date_range),
        brand_config=payload.brand_config,
    )
    return {"export_id": str(uuid4()), "status": "completed", "file_path": file_path}


@router.post("/export/schedule")
async def create_export_schedule(payload: ExportScheduleRequest) -> dict:
    """Create a scheduled export."""
    svc = ExportService()
    schedule_id = await svc.create_schedule(
        export_type=payload.export_type,
        cadence=payload.cadence,
        metric_selection=payload.metric_selection,
    )
    return {"schedule_id": schedule_id, "status": "active"}


@router.delete("/export/schedule/{schedule_id}")
async def delete_export_schedule(schedule_id: str) -> dict:
    """Delete an export schedule."""
    svc = ExportService()
    await svc.delete_schedule(schedule_id)
    return {"schedule_id": schedule_id, "status": "deleted"}


@router.get("/export/{export_id}")
async def get_export(export_id: str) -> dict:
    """Get export status by ID."""
    svc = ExportService()
    status = await svc.get_export_status(export_id)
    return {"export_id": export_id, "status": status.get("status", "not_found")}


# ── Static trend routes: MUST be registered before /trends/{metric} ───────────


@router.get("/trends/summary")
async def get_trends_summary(
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    store = Depends(get_metrics_repository),
) -> dict:
    """Get summary of all trend metrics."""
    svc = TrendService(data_store=store)
    return await svc.get_summary(
        from_date=_parse_date(from_date),
        to_date=_parse_date(to_date),
    )


@router.get("/trends/top-content")
async def get_top_content(
    metric: str = Query(default="reach"),
    limit: int = Query(default=10, ge=1),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    store = Depends(get_metrics_repository),
) -> list[dict]:
    """Get top-performing content across all platforms."""
    svc = TrendService(data_store=store)
    return await svc.get_top_content(
        metric=metric,
        limit=limit,
        from_date=_parse_date(from_date),
        to_date=_parse_date(to_date),
    )


@router.get("/trends/{metric}", response_model=TrendData)
async def get_trend(
    metric: str,
    granularity: str = Query(default="daily"),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    store = Depends(get_metrics_repository),
) -> TrendData:
    """Get time-series trend data for a metric."""
    svc = TrendService(data_store=store)
    result = await svc.get_trend(
        metric=metric,
        granularity=granularity,
        from_date=_parse_date(from_date),
        to_date=_parse_date(to_date),
    )
    return TrendData(**result)
