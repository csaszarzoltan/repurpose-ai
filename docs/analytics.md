# Analytics Dashboard Guide

> RepurposeAI v1.6.0 — Real-data content performance tracking, optimization scoring, validation gap analysis, CSV/PDF export, trend visualization, and the Next.js analytics dashboard UI.

## Overview

The Analytics Dashboard consists of **7 internal modules** (priorities P0 → P2) plus a **Next.js dashboard UI** that together provide end-to-end content analytics against real data:

- **P0.1 Data Store** — SQLite-backed repositories for metrics, validation reports, and optimization scores
- **P0.2 Content Performance Tracking** — Per-post metrics collection and normalisation
- **P1.1 Platform Optimization Scoring** — Deterministic 0–100 algorithm-readiness scores
- **P1.2 Validation Gap Analyzer** — Readability analysis, diff detection, tone/faithfulness/LLM judging
- **P1.3 CSV Export** — Real CSV report generation with schedule management
- **P2.1 PDF Export** — Real one-page PDF report generation with schedule management
- **P2.2 Trend Visualization** — Time-series aggregation and period-over-period deltas
- **Dashboard UI** — Next.js 14 + React + Tailwind frontend in `frontend/`

Every REST endpoint lives under `/api/v1/analytics` and reads/writes through the injected repositories — there is **no facade**: what the API returns is what is persisted in the analytics store. Interactive API docs are available at `/docs`.

---

## Table of Contents

- [Architecture](#architecture)
- [P0.1 — Data Store](#p01--data-store)
- [P0.2 — Content Performance Tracking](#p02--content-performance-tracking)
- [P1.1 — Platform Optimization Scoring](#p11--platform-optimization-scoring)
- [P1.2 — Validation Gap Analyzer](#p12--validation-gap-analyzer)
- [P1.3 & P2.1 — CSV & PDF Export](#p13--p21--csv--pdf-export)
- [P2.2 — Trend Visualization](#p22--trend-visualization)
- [Dashboard UI](#dashboard-ui)
- [API Reference](#api-reference)
- [Running the Dashboard Locally](#running-the-dashboard-locally)
- [Running Tests](#running-tests)
- [Known Limitations](#known-limitations)

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              Next.js Dashboard UI (frontend/)                 │
│   Summary cards · Trend chart · Top content · Score panel     │
│   Validation gaps panel · Export dialog                       │
└───────────────────────────┬──────────────────────────────────┘
                            │  fetch() → /api/v1/analytics/*
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                 FastAPI router (analytics.py)                 │
│   posts · summary · optimization-score · validate · export    │
│   trends · validation/{job_id} · export/schedule              │
└──────┬───────────────┬───────────────┬───────────┬───────────┘
       ▼               ▼               ▼           ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   P0.2      │  │  P1.1        │  │  P1.2        │  │  P2.2        │
│ Metrics     │  │ Score        │  │ Validation   │  │ Trend        │
│ Collector   │  │ Calculator   │  │ Analyzer     │  │ Service      │
└──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                │                │                 │
       ▼                ▼                ▼                 ▼
┌──────────────────────────────────────────────────────────────┐
│              P0.1 SQLite repositories (db/repository.py)      │
│   analytics_metrics · analytics_validations · analytics_scores │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **MetricsCollector** (P0.2) fetches raw metrics through a registered platform adapter (if any) and normalises them into standard 0.0–1.0 rates.
2. **MetricsRepository** (P0.1) persists normalised metrics to the SQLite `analytics_metrics` table.
3. **ScoreCalculator** (P1.1) computes 0–100 optimization scores from metrics; **ScoreRepository** persists them.
4. **ValidationAnalyzer** (P1.2) compares AI drafts against published content; **ValidationRepository** persists the report.
5. **ExportService** (P1.3/P2.1) generates real CSV strings and real one-page PDF files from the stored rows.
6. **TrendService** (P2.2) derives daily time-series, period-over-period deltas, and top-content rankings from the same stored rows.
7. The **dashboard UI** renders all of the above by calling the public endpoints.

The repositories are provided to the router via `app.dependencies` as module-level singletons, so data written through the API (e.g. by `MetricsCollector`) stays visible across requests in the same process.

---

## P0.1 — Data Store

**File**: `src/app/services/analytics/db/repository.py`
**Models**: MetricsRepository, ValidationRepository, ScoreRepository

All three repositories are SQLite-backed. The default connection is an in-memory database (`:memory:`), which gives every repository instance an isolated store — this is what the test suite relies on. Pass a `connection_string` (a file path or `sqlite:///` URI) to persist across process restarts.

Tables:

| Table | Purpose |
|-------|---------|
| `analytics_metrics` | Per-post metrics keyed by `(platform, post_id)` (upsert on conflict) |
| `analytics_validations` | Validation reports keyed by `job_id` |
| `analytics_scores` | Optimization scores keyed by `(post_id, platform)` |

### MetricsRepository

```python
import asyncio
from app.services.analytics.db.repository import MetricsRepository

async def main():
    repo = MetricsRepository()  # in-memory SQLite

    # Store metrics (upserts on the same platform + post_id)
    post_id = await repo.store_metrics(
        platform="linkedin",
        post_id="post_123",
        metrics={"engagement_rate": 0.05, "reach": 1000, "post_date": "2026-01-15T00:00:00+00:00"},
    )
    assert post_id == "post_123"

    # List everything (all platforms)
    rows = await repo.list_all()

    # Single post lookup (None if unknown)
    row = await repo.get_by_post_id("post_123")

    # Platform + date-window query (posts without a date are always included)
    matches = await repo.query_metrics(platform="linkedin", from_date=None, to_date=None)

asyncio.run(main())
```

### ValidationRepository

```python
from app.services.analytics.db.repository import ValidationRepository

vrepo = ValidationRepository()

# Store a validation result
await vrepo.store_validation(
    job_id="val_001",
    draft="AI generated draft...",
    published="Published version...",
    scores={"quality_delta": 0.15, "readability": {"flesch_kincaid": 12.5}},
)

# Retrieve ({} if unknown)
report = await vrepo.query_validation(job_id="val_001")
```

### ScoreRepository

```python
from app.services.analytics.db.repository import ScoreRepository

srepo = ScoreRepository()

# Store a score
score_id = await srepo.store_score(
    post_id="post_123",
    platform="linkedin",
    overall_score=78.5,
    signals={"engagement_rate": 0.05, "completion_rate": 0.8},
)

# Query by post + platform, or latest for a post across any platform
entry = await srepo.query_score(post_id="post_123", platform="linkedin")
latest = await srepo.query_score_by_post(post_id="post_123")
```

---

## P0.2 — Content Performance Tracking

**File**: `src/app/services/analytics/metrics_collector.py`
**Models**: PostMetrics, AnalyticsSummary (`src/app/models/analytics.py`)

### MetricsCollector

The collector is the ingestion path for per-post performance metrics: `collect(platform, post_id)` fetches raw metrics through the registered platform adapter, normalises them into standard 0.0–1.0 rates, and persists the result via `MetricsRepository`.

Platform adapters are callables (sync or async) mapping `post_id` to a raw metrics dict, or objects exposing an async `fetch_metrics(post_id)` method. Without a configured adapter there is no external source to fetch from, so a zero-valued raw payload is normalised and persisted instead of fabricating numbers.

```python
import asyncio
from app.services.analytics.metrics_collector import MetricsCollector

async def main():
    collector = MetricsCollector(platform_adapters={})

    # Normalise raw platform data into standard 0.0–1.0 rates
    normalised = collector.normalise_metrics({"views": 1000, "likes": 50, "shares": 10})
    # → {"engagement_rate": 0.05, "share_rate": 0.01, "completion_rate": 0.0}

    # Collect for a single post (persists to the repository)
    metrics = await collector.collect(platform="linkedin", post_id="post_123")

asyncio.run(main())
```

Rates are computed as `likes / views` (engagement), `shares / views` (share), and `completion_rate` defaults to `0.0` (platforms rarely report it via a generic adapter).

### PostMetrics Model

```python
from datetime import datetime
from app.models.analytics import PostMetrics

post = PostMetrics(
    reach=1000,
    impressions=5000,
    engagement_rate=0.05,
    completion_rate=0.8,
    share_rate=0.02,
    post_date=datetime(2026, 1, 15),
    platform="linkedin",
    post_id="post_123",
)
```

Optional fields: `send_rate`, `growth_rate`.

### AnalyticsSummary Model

```python
from datetime import datetime
from app.models.analytics import AnalyticsSummary

summary = AnalyticsSummary(
    total_reach=15000,
    avg_engagement_rate=0.045,
    follower_growth=120,
    period_start=datetime(2026, 1, 1),
    period_end=datetime(2026, 1, 31),
)
```

---

## P1.1 — Platform Optimization Scoring

**File**: `src/app/services/analytics/score_calculator.py`
**Models**: OptimizationScore (`src/app/models/analytics.py`)

### ScoreCalculator

Computes a deterministic 0–100 algorithm-readiness score per platform based on engagement signals.

**Scoring formula:**

| Signal | Contribution | Source |
|--------|--------------|--------|
| Engagement rate | `min(engagement_rate × 800, 40)` | likes / views |
| Completion rate | `completion_rate × 30` | completions / starts |
| Share rate | `share_rate × 20` | shares / views |
| Platform multiplier | ×1.0 (LinkedIn), ×0.95 (all others) | — |

```
overall = clamp_0_100((engagement_score + completion_score + share_score) × platform_multiplier)
```

Because the engagement contribution is capped at 40, the maximum possible score is **90.0** on LinkedIn and **85.5** on any other platform.

```python
import asyncio
from app.services.analytics.score_calculator import ScoreCalculator

async def main():
    calc = ScoreCalculator(weights_config={})

    # Single calculation — LinkedIn example: 40 (capped) + 24 + 0.4 = 64.4
    result = await calc.calculate(
        platform="linkedin",
        metrics={"engagement_rate": 0.05, "completion_rate": 0.8, "share_rate": 0.02},
    )
    # → {"overall_score": 64.4, "signals": {"engagement_rate": 0.05, "completion_rate": 0.8, "share_rate": 0.02}}

    # Non-LinkedIn platforms get the 0.95 multiplier
    other = await calc.calculate(
        platform="twitter",
        metrics={"engagement_rate": 0.03, "completion_rate": 0.7, "share_rate": 0.01},
    )
    # → {"overall_score": 42.94, "signals": {...}}

    # Batch calculation
    results = await calc.calculate_batch(
        platform="twitter",
        metrics_list=[
            {"engagement_rate": 0.03, "completion_rate": 0.7, "share_rate": 0.01},
            {"engagement_rate": 0.08, "completion_rate": 0.9, "share_rate": 0.05},
        ],
    )

    # Clamp a raw score to the 0-100 range
    clamped = calc.normalise_score(raw_score=120.0)  # → 100.0

asyncio.run(main())
```

### OptimizationScore Model

```python
from datetime import UTC, datetime
from app.models.analytics import OptimizationScore

score = OptimizationScore(
    overall_score=78.5,
    signals={"engagement_rate": 0.05, "completion_rate": 0.8},
    platform="linkedin",
    calculated_at=datetime.now(UTC),
)
```

---

## P1.2 — Validation Gap Analyzer

**File**: `src/app/services/analytics/validation_analyzer.py`
**Models**: ValidationReport (`src/app/models/analytics.py`)

### ValidationAnalyzer

Performs side-by-side quality analysis of AI-generated content vs. the published version. Includes:

- **Quality delta** — `1 − difflib.SequenceMatcher.ratio(draft, published)`: identical texts yield `0.0`, diverging texts move toward `1.0`
- **Readability scoring** — Flesch-Kincaid, Dale-Chall, Automated Readability Index (ARI)
- **Diff detection** — diff blocks via `difflib.SequenceMatcher` over lines
- **Faithfulness** — vocabulary overlap between draft and source material (only when `source_material` is provided)
- **LLM judge** — optional heuristic coherence/persuasiveness/clarity scores (see Known Limitations)

```python
import asyncio
from app.services.analytics.validation_analyzer import ValidationAnalyzer

async def main():
    analyzer = ValidationAnalyzer(llm_router=None)

    # Full validation pipeline (diff + readability + optional faithfulness + optional LLM judge)
    report = await analyzer.validate(
        draft="The quick brown fox jumps over the lazy dog.",
        published="The quick brown fox leaps over the sleepy dog.",
        source_material="The quick brown fox jumps over the lazy dog. It is a classic pangram.",
        run_llm_judge=True,
    )
    # → {
    #     "quality_delta": 0.1333,
    #     "readability": {"flesch_kincaid": 2.34, "dale_chall": 1.48, "ari": 6.1},
    #     "diff_blocks": [{"type": "replace",
    #                      "content": "The quick brown fox leaps over the sleepy dog.",
    #                      "original": "The quick brown fox jumps over the lazy dog."}],
    #     "faithfulness": {"faithfulness": 0.6154, "score": 0.6154},
    #     "llm_judge": {"coherence": 0.85, "persuasiveness": 0.75, "clarity": 0.9},
    # }

    # Standalone readability
    readability = analyzer.compute_readability_scores(
        "The quick brown fox jumps over the lazy dog."
    )
    # → {"flesch_kincaid": 2.34, "dale_chall": 1.48, "ari": 6.1}

    # Standalone diff (note: content/original are whole lines, not words)
    blocks = analyzer.compute_diff_blocks(
        draft="Hello world version A",
        published="Hello world version B",
    )
    # → [{"type": "replace", "content": "Hello world version B", "original": "Hello world version A"}]

    # Tone consistency (simplified similarity; 0.85 with a brand exemplar, 0.75 without)
    tone = await analyzer.compute_tone_consistency(
        draft="...", published="...", brand_voice_exemplar="professional",
    )
    # → {"similarity": 0.85}

    # Faithfulness (word-set overlap between draft and source material)
    faith = await analyzer.compute_faithfulness(
        draft="The quick brown fox jumps over the lazy dog.",
        source_material="The quick brown fox jumps over the lazy dog. It is a classic pangram.",
    )
    # → {"faithfulness": 0.6154, "score": 0.6154}

    # LLM judge (heuristic, fixed values in the current implementation)
    judge = await analyzer.compute_llm_judge(draft="...", published="...")
    # → {"coherence": 0.85, "persuasiveness": 0.75, "clarity": 0.9}

asyncio.run(main())
```

### Readability Formulas

| Metric | Formula | Interpretation |
|--------|---------|---------------|
| **Flesch-Kincaid** | `0.39×(words/sentences) + 11.8×(syllables/words) − 15.59` | Lower = easier (3 = very easy, 20+ = very hard) |
| **Dale-Chall** | `0.1579×(words/sentences) + 0.0496×(syllables/words)` | <5 = easy, >9 = difficult |
| **ARI** | `4.71×(chars/words) + 0.5×(words/sentences) − 21.43` | Corresponds to US grade level |

### Diff Block Types

| Type | Meaning | Content |
|------|---------|---------|
| `replace` | Draft text was replaced in published | Published version (field: `content`), Draft original (field: `original`) |
| `delete` | Text present in draft, absent in published | Removed text |
| `insert` | Text absent in draft, added in published | Added text |

### ValidationReport Model

```python
from app.models.analytics import ValidationReport

report = ValidationReport(
    quality_delta=0.15,
    readability={"flesch_kincaid": 12.5, "dale_chall": 8.0, "ari": 14.0},
    tone_consistency={"similarity": 0.85},
    faithfulness={"faithfulness": 0.72},
    llm_judge={"coherence": 0.85, "persuasiveness": 0.75},
    diff_blocks=[{"type": "replace", "content": "new text", "original": "old text"}],
)
```

---

## P1.3 & P2.1 — CSV & PDF Export

**File**: `src/app/services/analytics/export_service.py`

### ExportService

Generates **real CSV content** (header row + one row per post, `date` first) and **real one-page PDF documents** (`%PDF-` files written to `/tmp/report_<id>.pdf`) from the stored analytics rows, with in-memory schedule management.

```python
import asyncio
from app.services.analytics.db.repository import MetricsRepository
from app.services.analytics.export_service import ExportService

async def main():
    repo = MetricsRepository()
    await repo.store_metrics("linkedin", "post_123", {"reach": 1000, "engagement_rate": 0.05,
                                                      "post_date": "2026-01-15T00:00:00+00:00"})
    await repo.store_metrics("twitter", "post_456", {"reach": 500, "engagement_rate": 0.08,
                                                     "post_date": "2026-01-20T00:00:00+00:00"})
    svc = ExportService(data_store=repo)

    # CSV export — note \r\n line endings (Python csv module default)
    csv_content = await svc.export_csv(
        metric_selection=["reach", "engagement_rate"],
        date_range=None,
        platform_filter=None,
    )
    # → 'date,reach,engagement_rate\r\n2026-01-15,1000,0.05\r\n2026-01-20,500,0.08\r\n'

    # PDF export — writes a real, self-contained one-page PDF and returns its path
    pdf_path = await svc.export_pdf(
        metric_selection=["reach"],
        date_range=None,
        brand_config={"title": "Analytics Report"},
    )
    # → "/tmp/report_export_2.pdf" (file begins with %PDF-; export_csv above took id export_1)

    # Export status (in-process registry)
    status = await svc.get_export_status(export_id="export_1")
    # → {"status": "completed", "id": "export_1"}

    # Schedule management (in-memory)
    schedule_id = await svc.create_schedule(
        export_type="csv",
        cadence="daily",
        metric_selection=["reach", "engagement_rate"],
    )
    await svc.delete_schedule(schedule_id=schedule_id)

asyncio.run(main())
```

| Method | Description |
|--------|-------------|
| `export_csv(metric_selection, date_range, platform_filter)` | Generate CSV string with headers and data rows |
| `export_pdf(metric_selection, date_range, brand_config)` | Generate a real one-page PDF, returns `/tmp/report_*.pdf` path |
| `get_export_status(export_id)` | Check if an export is completed or not found |
| `create_schedule(export_type, cadence, metric_selection)` | Create recurring export schedule (in-memory) |
| `delete_schedule(schedule_id)` | Remove an export schedule |

---

## P2.2 — Trend Visualization

**File**: `src/app/services/analytics/trend_service.py`
**Models**: DataPoint, TrendData (`src/app/models/analytics.py`)

### TrendService

Computes per-day time-series, period-over-period deltas, trend summaries, and top-content rankings — all derived from the injected `MetricsRepository` (a `None` store yields empty series).

```python
import asyncio
from app.services.analytics.db.repository import MetricsRepository
from app.services.analytics.trend_service import TrendService

async def main():
    repo = MetricsRepository()
    await repo.store_metrics("linkedin", "post_123", {"reach": 1000, "engagement_rate": 0.05,
                                                      "post_date": "2026-01-15T00:00:00+00:00"})
    await repo.store_metrics("twitter", "post_456", {"reach": 500, "engagement_rate": 0.08,
                                                     "post_date": "2026-01-20T00:00:00+00:00"})
    svc = TrendService(data_store=repo)

    # Per-day time series with period-over-period delta
    trend = await svc.get_trend(metric="reach", granularity="daily")
    # → {"metric": "reach", "granularity": "daily",
    #     "points": [{"date": "2026-01-15", "value": 1000.0}, {"date": "2026-01-20", "value": 500.0}],
    #     "period_over_period_delta": -500.0}

    # Aggregated summary over the store
    summary = await svc.get_summary()
    # → {"total_posts": 2, "total_reach": 1500, "avg_engagement_rate": 0.065, "top_platform": "linkedin"}

    # Top-performing content, ranked highest first
    top = await svc.get_top_content(metric="reach", limit=5)
    # → [{"post_id": "post_123", "reach": 1000.0}, {"post_id": "post_456", "reach": 500.0}]

    # Standalone period-over-period delta = mean(current half) − mean(previous half)
    delta = svc.compute_period_delta(current=[100.0, 110.0, 105.0], previous=[95.0, 98.0, 100.0])
    # → 7.3333...

asyncio.run(main())
```

The period-over-period delta splits the sorted points in half and computes `mean(second half) − mean(first half)`; series with fewer than two points return `0.0`.

### TrendData & DataPoint Models

```python
from app.models.analytics import DataPoint, TrendData

point = DataPoint(date="2026-07-01", value=100.0)

trend = TrendData(
    points=[point],
    period_over_period_delta=7.33,
    metric="reach",
    granularity="daily",
)
```

---

## Dashboard UI

The dashboard is a **Next.js 14** (React 18 + Tailwind CSS 3 + TypeScript) app in `frontend/`. It renders real data fetched from the `/api/v1/analytics` endpoints:

- **Header** — platform filter (All platforms / X-Twitter / LinkedIn / Medium), per-platform post counts, refresh and export buttons.
- **Summary cards** — total reach, impressions, engagement (impressions × engagement rate), and post/platform/top-platform counts.
- **Performance trends** — daily totals line chart with a metric switcher (reach, impressions, engagement rate) and the period-over-period delta. The all-platforms view refetches the server series (`/trends/{metric}`); platform-filtered views aggregate the fetched posts client-side.
- **Top content** — ranking of the top 8 posts by the selected metric (default: reach, from `/trends/top-content`).
- **Optimization score** — algorithm-readiness 0–100 computed live via the `/optimization-score/calculate` endpoint; select any listed post to score it.
- **Validation gaps** — quality delta between AI draft and published content (readability, tone consistency, faithfulness, LLM coherence) from the validation API.
- **Export dialog** — CSV or PDF export with metric selection (reach, impressions, engagement/completion/share rate), platform filter, and client-side file download (the CSV text is taken from the `content` field of the export response).
- **Empty state** — shown when the store has no posts, with a "View demo data" action.

The API client (`frontend/lib/api.ts`) resolves its base URL from `NEXT_PUBLIC_API_BASE`, defaulting to the same-origin `/api/v1/analytics` path (how the dashboard is served behind the backend in production).

See [Running the Dashboard Locally](#running-the-dashboard-locally) for setup.

---

## API Reference

All analytics endpoints produce JSON and are currently **open** (no authentication dependency). Malformed `from_date`/`to_date` values return **422 Unprocessable Entity** with a descriptive `detail`; unknown posts/scores/validation jobs return **404**.

Date parameters accept ISO 8601 values such as `2026-07-01` or `2026-07-01T00:00:00Z` (date-only strings are interpreted as UTC).

### List Posts

```
GET /api/v1/analytics/posts
```

```bash
curl http://localhost:8000/api/v1/analytics/posts
```

Response: `[PostMetrics]` array. Each item includes `post_id`, `platform`, `post_date`, `reach`, `impressions`, `engagement_rate`, `completion_rate`, `share_rate`, `send_rate`, `growth_rate`.

### Get Post

```
GET /api/v1/analytics/posts/{post_id}
```

```bash
curl http://localhost:8000/api/v1/analytics/posts/post_123
```

Response: `PostMetrics` object, or `404` when the post is unknown.

### Aggregate Summary

```
GET /api/v1/analytics/summary?from_date=2026-07-01&to_date=2026-08-01
```

`from_date`/`to_date` are optional ISO 8601 filters (`2026-07-01` or `2026-07-01T00:00:00Z`); without them the whole store is summarised.

```bash
curl http://localhost:8000/api/v1/analytics/summary
```

Response (full store):

```json
{
  "total_reach": 364502,
  "avg_engagement_rate": 0.0335,
  "follower_growth": 0,
  "period_start": "2026-07-20T10:00:00Z",
  "period_end": "2026-08-03T10:00:00Z"
}
```

### Calculate Optimization Score

```
POST /api/v1/analytics/optimization-score/calculate
```

```bash
curl -X POST http://localhost:8000/api/v1/analytics/optimization-score/calculate \
  -H "Content-Type: application/json" \
  -d '{"platform": "linkedin", "metrics": {"engagement_rate": 0.05, "completion_rate": 0.8, "share_rate": 0.02}}'
```

Response:

```json
{
  "overall_score": 64.4,
  "signals": {"engagement_rate": 0.05, "completion_rate": 0.8, "share_rate": 0.02},
  "platform": "linkedin",
  "calculated_at": "2026-08-03T17:24:58Z"
}
```

### Get Optimization Score

```
GET /api/v1/analytics/optimization-score/{post_id}
```

```bash
curl http://localhost:8000/api/v1/analytics/optimization-score/post_123
```

Response: `OptimizationScore` object, or `404` when no score is stored for the post.

### Validate Content

```
POST /api/v1/analytics/validate
```

```bash
curl -X POST http://localhost:8000/api/v1/analytics/validate \
  -H "Content-Type: application/json" \
  -d '{"draft": "The quick brown fox jumps over the lazy dog.", "published": "The quick brown fox leaps over the sleepy dog.", "run_llm_judge": true}'
```

Response: `ValidationReport` object — `quality_delta`, `readability`, `diff_blocks`, plus `faithfulness` (when `source_material` is sent) and `llm_judge` (when `run_llm_judge` is true). The report is persisted and retrievable via the job endpoint below.

### Get Validation Report

```
GET /api/v1/analytics/validation/{job_id}
```

```bash
curl http://localhost:8000/api/v1/analytics/validation/val_001
```

Response: `ValidationReport` object, or `404` when the job is unknown.

### Export to CSV

```
POST /api/v1/analytics/export/csv
```

```bash
curl -X POST http://localhost:8000/api/v1/analytics/export/csv \
  -H "Content-Type: application/json" \
  -d '{"metric_selection": ["reach", "engagement_rate"], "platform_filter": "linkedin"}'
```

Response:

```json
{
  "export_id": "6af5c0bc-cfc8-49ad-83f9-58fa4119df9b",
  "status": "completed",
  "content": "date,reach,engagement_rate\r\n2026-07-24,8496,0.0203\r\n..."
}
```

### Export to PDF

```
POST /api/v1/analytics/export/pdf
```

```bash
curl -X POST http://localhost:8000/api/v1/analytics/export/pdf \
  -H "Content-Type: application/json" \
  -d '{"metric_selection": ["reach", "engagement_rate"]}'
```

Response: `{"export_id": "...", "status": "completed", "file_path": "/tmp/report_export_1.pdf"}` — the file is a real, self-contained one-page PDF.

### Create Export Schedule

```
POST /api/v1/analytics/export/schedule
```

```bash
curl -X POST http://localhost:8000/api/v1/analytics/export/schedule \
  -H "Content-Type: application/json" \
  -d '{"export_type": "csv", "cadence": "daily", "metric_selection": ["reach"]}'
```

Response: `{"schedule_id": "<uuid>", "status": "active"}`.

### Delete Export Schedule

```
DELETE /api/v1/analytics/export/schedule/{schedule_id}
```

```bash
curl -X DELETE http://localhost:8000/api/v1/analytics/export/schedule/<schedule_id>
```

Response: `{"schedule_id": "...", "status": "deleted"}`.

### Get Export Status

```
GET /api/v1/analytics/export/{export_id}
```

```bash
curl http://localhost:8000/api/v1/analytics/export/export_1
```

Response: `{"export_id": "...", "status": "completed"}` (`not_found` for unknown ids).

### Get Trend Data

```
GET /api/v1/analytics/trends/{metric}?granularity=daily&from_date=2026-07-01&to_date=2026-08-01
```

```bash
curl "http://localhost:8000/api/v1/analytics/trends/reach?granularity=daily"
```

Response (points abbreviated — the live window returned 10 daily points):

```json
{
  "metric": "reach",
  "granularity": "daily",
  "points": [
    {"date": "2026-07-20", "value": 36941.0},
    {"date": "2026-07-22", "value": 24884.0},
    {"date": "2026-08-03", "value": 69289.0}
  ],
  "period_over_period_delta": 3740.4
}
```

### Trends Summary

```
GET /api/v1/analytics/trends/summary?from_date=2026-07-01&to_date=2026-08-01
```

```bash
curl "http://localhost:8000/api/v1/analytics/trends/summary"
```

Response:

```json
{"total_posts": 18, "total_reach": 364502, "avg_engagement_rate": 0.0335, "top_platform": "linkedin"}
```

### Top Content

```
GET /api/v1/analytics/trends/top-content?metric=reach&limit=8&from_date=2026-07-01&to_date=2026-08-01
```

```bash
curl "http://localhost:8000/api/v1/analytics/trends/top-content?metric=reach&limit=3"
```

Response:

```json
[
  {"post_id": "me-0803-01", "reach": 43329.0},
  {"post_id": "tw-0803-03", "reach": 37981.0},
  {"post_id": "tw-0803-02", "reach": 36941.0}
]
```

---

## Running the Dashboard Locally

### 1. Backend API (FastAPI)

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

The API is served at `http://localhost:8000`; interactive docs at `/docs`.

### 2. Seed the analytics store with demo data (optional)

The analytics repositories are in-process singletons, so a plain start has an **empty** store. A dev helper seeds realistic metrics, scores, and a validation report into the same process it serves, so the dashboard can be demoed end-to-end against real responses:

```bash
PYTHONPATH=src .venv/bin/python scripts/seed_analytics_demo.py --port 8000
```

`--no-seed` starts a clean (empty) backend — useful for exercising the dashboard's onboarding/empty state. The seed is deterministic (`random.seed(42)`): 18 posts across `twitter`, `linkedin`, and `medium`, plus matching scores and one validation report.

### 3. Dashboard UI (Next.js)

```bash
cd frontend
npm install

# Dev server, pointed at the local backend
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1/analytics npm run dev
# → http://localhost:3000
```

For a production-style run: `npm run build && npm run start`. Type-checking runs via `npm run typecheck`. When `NEXT_PUBLIC_API_BASE` is unset, the client uses the same-origin `/api/v1/analytics` path (e.g. when the dashboard is served behind the backend).

---

## Running Tests

```bash
# All analytics tests + the frontend gate (313 tests)
.venv/bin/python -m pytest tests/test_analytics_*.py tests/test_frontend_gate.py -v

# Single module
.venv/bin/python -m pytest tests/test_analytics_scoring.py -v

# Specific test
.venv/bin/python -m pytest tests/test_analytics_scoring.py::test_calculate_returns_expected_range -v
```

| Test File | Tests | Module |
|-----------|-------|--------|
| `test_analytics_data_store.py` | 39 | P0.1 Data Store |
| `test_analytics_models.py` | 58 | Pydantic models |
| `test_analytics_scoring.py` | 19 | P1.1 Score Calculator |
| `test_analytics_validation.py` | 31 | P1.2 Validation Analyzer |
| `test_analytics_export.py` | 26 | P1.3/P2.1 CSV & PDF Export |
| `test_analytics_trends.py` | 33 | P2.2 Trend Service |
| `test_analytics_performance.py` | 25 | P0.2 Performance Tracking |
| `test_analytics_services.py` | 50 | Service wiring / real data flow |
| `test_analytics_real_data.py` | 28 | Real repository-backed API behavior (incl. date-validation regressions) |
| `test_frontend_gate.py` | 4 | Frontend build/typecheck gate |

---

## Known Limitations

- The repository singletons in `app.dependencies` default to **in-memory SQLite** — data survives across requests in the same process but is lost on restart. Pass a file-backed `connection_string` (or wire `get_metrics_repository` etc. to a file path) for durable persistence.
- Analytics endpoints currently have **no authentication** — they are open to any API consumer (consistent with the dashboard scaffold).
- `compute_tone_consistency` and `compute_llm_judge` are **simplified heuristics** returning fixed similarity/quality values, not model-based judgments.
- `MetricsCollector.collect_range` is a placeholder returning `[]` — batch collection is not implemented.
- Export **schedules** are in-memory only (`ExportService` instance state) — they do not survive restarts and no background scheduler executes them.
- The PDF export writes a real, self-contained one-page report to `/tmp`; branding (`brand_config`) is currently limited to the report title.
- The `follower_growth` summary field is reported as `0` (no follower-growth ingestion path yet).
