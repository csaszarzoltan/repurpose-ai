"""Analytics Pydantic models for content performance, validation, and scoring.

Source of truth: analysis/analysis-brief.md §4 (P0 — P2 modules).
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — needed at runtime for model_rebuild
from typing import Any

from pydantic import BaseModel

# ═══════════════════════════════════════════════════════════════════════════════
# P0.2 — Content Performance Tracking (Module A)
# ═══════════════════════════════════════════════════════════════════════════════


class PostMetrics(BaseModel):
    """Per-post performance metrics from a connected platform."""

    reach: int | None = None
    impressions: int | None = None
    engagement_rate: float | None = None
    completion_rate: float | None = None
    share_rate: float | None = None
    send_rate: float | None = None
    growth_rate: float | None = None
    post_date: datetime | None = None
    platform: str = ""
    post_id: str = ""


class AnalyticsSummary(BaseModel):
    """Aggregate metrics over a date range."""

    total_reach: int = 0
    avg_engagement_rate: float = 0.0
    follower_growth: int = 0
    period_start: datetime | None = None
    period_end: datetime | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# P1.1 — Platform Optimization Scoring (Module B)
# ═══════════════════════════════════════════════════════════════════════════════


class OptimizationScore(BaseModel):
    """Algorithm-readiness score (0-100) with per-signal breakdown."""

    overall_score: float = 0.0
    signals: dict[str, float] = {}
    platform: str = ""
    calculated_at: datetime | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# P1.2 — Validation Gap Analyzer (Module C)
# ═══════════════════════════════════════════════════════════════════════════════


class ValidationReport(BaseModel):
    """Side-by-side quality delta report between AI draft and published content."""

    quality_delta: float = 0.0
    readability: dict[str, Any] = {}
    tone_consistency: dict[str, Any] = {}
    faithfulness: dict[str, Any] = {}
    llm_judge: dict[str, Any] = {}
    diff_blocks: list[dict[str, Any]] = []


# ═══════════════════════════════════════════════════════════════════════════════
# P2.2 — Trend Visualization (Module E)
# ═══════════════════════════════════════════════════════════════════════════════


class DataPoint(BaseModel):
    """A single time-series data point."""

    date: str = ""
    value: float = 0.0


class TrendData(BaseModel):
    """Time-series trend data with period-over-period delta."""

    points: list[DataPoint] = []
    period_over_period_delta: float = 0.0
    metric: str = ""
    granularity: str = ""


# ── Forward-reference resolution (Pydantic v2 + from __future__ annotations) ──

PostMetrics.model_rebuild()
AnalyticsSummary.model_rebuild()
OptimizationScore.model_rebuild()
ValidationReport.model_rebuild()
DataPoint.model_rebuild()
TrendData.model_rebuild()
