# Analytics Dashboard Guide

> RepurposeAI v0.7.0 — Content performance tracking, optimization scoring, validation, export, and trend visualization.

## Overview

The Analytics Dashboard consists of **7 internal modules** organized by priority (P0 → P2) that together provide end-to-end content analytics:

- **P0.1 Data Store** — Database connections, versioned migrations, and in-memory CRUD repositories
- **P0.2 Content Performance Tracking** — Per-post metrics collection and normalisation
- **P1.1 Platform Optimization Scoring** — Deterministic 0–100 algorithm-readiness scores
- **P1.2 Validation Gap Analyzer** — Readability analysis, diff detection, tone/faithfulness/LLM judging
- **P1.3 CSV Export** — CSV report generation with schedule management
- **P2.1 PDF Export** — PDF report stub generation with schedule management
- **P2.2 Trend Visualization** — Time-series aggregation and period-over-period deltas

All REST endpoints are under `/api/v1/analytics`. Interactive API docs at `/docs`.

---

## Table of Contents

- [Architecture](#architecture)
- [P0.1 — Data Store](#p01--data-store)
- [P0.2 — Content Performance Tracking](#p02--content-performance-tracking)
- [P1.1 — Platform Optimization Scoring](#p11--platform-optimization-scoring)
- [P1.2 — Validation Gap Analyzer](#p12--validation-gap-analyzer)
- [P1.3 & P2.1 — CSV & PDF Export](#p13--p21--csv--pdf-export)
- [P2.2 — Trend Visualization](#p22--trend-visualization)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Analytics Dashboard                    │
│  ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌──────────┐ │
│  │  P0.1    │ │  P0.2      │ │  P1.1    │ │  P1.2    │ │
│  │ Data     │→│ Content    │→│Opt.      │→│Validation│ │
│  │ Store    │ │ Performance│ │ Scoring  │ │ Gap      │ │
│  └──────────┘ └────────────┘ └──────────┘ └──────────┘ │
│       │              │              │           │        │
│       ▼              ▼              ▼           ▼        │
│  ┌──────────┐ ┌────────────┐ ┌──────────────────────┐   │
│  │  P1.3    │ │  P2.1      │ │  P2.2                │   │
│  │ CSV Exp. │ │ PDF Exp.   │ │ Trend Visualization   │   │
│  └──────────┘ └────────────┘ └──────────────────────┘   │
└─────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
  │ CSV on disk  │   │ PDF stub     │   │ JSON time-series │
  └──────────────┘   └──────────────┘   └──────────────────┘
```

### Data Flow

1. **MetricsCollection** (P0.2) collects raw metrics from platform adapters
2. **MetricsRepository** (P0.1) stores normalised metrics in-memory
3. **ScoreCalculator** (P1.1) computes optimization scores from stored metrics
4. **ValidationAnalyzer** (P1.2) compares AI drafts against published content
5. **ExportService** (P1.3/P2.1) generates CSV/PDF reports from stored data
6. **TrendService** (P2.2) computes period-over-period deltas and top-content ranking

---

## P0.1 — Data Store

**File**: `src/app/services/analytics/db/`
**Models**: DatabaseConnection, MetricsRepository, ValidationRepository, ScoreRepository, Migration, Migrator

### DatabaseConnection

Manages SQLite/PostgreSQL connection lifecycle for analytics storage.

```python
from app.services.analytics.db.connection import DatabaseConnection

# Create connection
db = DatabaseConnection(connection_string="sqlite:///analytics.db")
await db.connect()
assert db.is_connected is True

# Execute queries (stub — returns empty in scaffold)
await db.execute("CREATE TABLE IF NOT EXISTS metrics (...)")
rows = await db.fetch("SELECT * FROM metrics WHERE platform = :p", {"p": "linkedin"})

# Close
await db.disconnect()
assert db.is_connected is False
```

| Method | Description |
|--------|-------------|
| `connect()` | Open the database connection |
| `disconnect()` | Close the database connection |
| `execute(query, params)` | Execute a SQL query |
| `fetch(query, params)` | Fetch rows from a SQL query |
| `is_connected` (property) | Whether connection is open |

### MetricsRepository

In-memory store for time-series metrics.

```python
from app.services.analytics.db.repository import MetricsRepository

repo = MetricsRepository()

# Store metrics
post_id = await repo.store_metrics(
    platform="linkedin",
    post_id="post_123",
    metrics={"engagement_rate": 0.05, "reach": 1000},
)

# Query by platform
results = await repo.query_metrics(
    platform="linkedin",
    from_date=None,
    to_date=None,
    granularity="daily",
)
```

### ValidationRepository

In-memory store for validation reports.

```python
from app.services.analytics.db.repository import ValidationRepository

vrepo = ValidationRepository()

# Store validation result
job_id = await vrepo.store_validation(
    job_id="val_001",
    draft="AI generated draft...",
    published="Published version...",
    scores={"quality_delta": 0.15, "readability": {...}},
)

# Retrieve
report = await vrepo.query_validation(job_id="val_001")
```

### ScoreRepository

In-memory store for optimization scores.

```python
from app.services.analytics.db.repository import ScoreRepository

srepo = ScoreRepository()

# Store score
score_id = await srepo.store_score(
    post_id="post_123",
    platform="linkedin",
    overall_score=78.5,
    signals={"engagement_rate": 0.05, "completion_rate": 0.8},
)

# Query
entry = await srepo.query_score(post_id="post_123", platform="linkedin")
```

### Migration & Migrator

Schema version management for the analytics database.

```python
from app.services.analytics.db.migrations import Migration, Migrator

# Define a migration step
migration = Migration(
    version=1,
    description="Create metrics table",
    sql_up="CREATE TABLE metrics (...)",
    sql_down="DROP TABLE metrics",
)

# Apply/rollback
migrator = Migrator(connection_string="sqlite:///analytics.db")
current = await migrator.apply(target_version=1)       # → 1
rolled_back = await migrator.rollback(target_version=0) # → 0
version = await migrator.current_version()              # → 0 or latest
pending = await migrator.pending_migrations()            # → list
```

---

## P0.2 — Content Performance Tracking

**File**: `src/app/services/analytics/metrics_collector.py`
**Models**: PostMetrics, AnalyticsSummary (`src/app/models/analytics.py`)

### MetricsCollector

Fetches and normalises per-post performance metrics from connected platforms.

```python
from app.services.analytics.metrics_collector import MetricsCollector

collector = MetricsCollector(platform_adapters={})

# Collect metrics for a single post
metrics = await collector.collect(platform="linkedin", post_id="post_123")
# → {"engagement_rate": 0.05, "completion_rate": 0.8, "share_rate": 0.02}

# Collect for a date range
all_metrics = await collector.collect_range(
    platform="linkedin",
    from_date="2026-01-01",
    to_date="2026-01-31",
)

# Normalise raw platform data into standard 0.0–1.0 rates
normalised = collector.normalise_metrics(
    {"views": 1000, "likes": 50, "shares": 10}
)
# → {"engagement_rate": 0.05, "share_rate": 0.01, "completion_rate": 0.0}
```

### PostMetrics Model

```python
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

| Signal | Weight | Source |
|--------|--------|--------|
| Engagement rate | ×800 (capped at 40) | likes / views |
| Completion rate | ×30 | completions / starts |
| Share rate | ×20 | shares / views |
| Platform multiplier | ×1.0 (LinkedIn), ×0.95 (others) | — |

```
overall = clamp(engagement_score + completion_score + share_score) × platform_multiplier
```

```python
from app.services.analytics.score_calculator import ScoreCalculator

calc = ScoreCalculator(weights_config={})

# Single calculation
result = await calc.calculate(
    platform="linkedin",
    metrics={"engagement_rate": 0.05, "completion_rate": 0.8, "share_rate": 0.02},
)
# → {"overall_score": 64.5, "signals": {"engagement_rate": 0.05, "completion_rate": 0.8, "share_rate": 0.02}}

# Batch calculation
results = await calc.calculate_batch(
    platform="twitter",
    metrics_list=[
        {"engagement_rate": 0.03, "completion_rate": 0.7, "share_rate": 0.01},
        {"engagement_rate": 0.08, "completion_rate": 0.9, "share_rate": 0.05},
    ],
)

# Normalise raw score
clamped = calc.normalise_score(raw_score=120.0)  # → 100.0
```

### OptimizationScore Model

```python
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

Performs side-by-side quality analysis of AI-generated content vs. published version. Includes:

- **Readability scoring** — Flesch-Kincaid, Dale-Chall, Automated Readability Index (ARI)
- **Diff detection** — Unified diff blocks via `difflib.SequenceMatcher`
- **Tone consistency** — Similarity score between draft and published tone
- **Faithfulness** — Vocabulary overlap between draft and source material
- **LLM judge** — Optional LLM-based coherence/persuasiveness/clarity scoring

```python
from app.services.analytics.validation_analyzer import ValidationAnalyzer

analyzer = ValidationAnalyzer(llm_router=None)

# Full validation pipeline
report = await analyzer.validate(
    draft="AI generated blog post draft...",
    published="Human published version...",
    source_material="Original source article...",
    run_llm_judge=True,
)
# → {
#     "quality_delta": 0.15,
#     "readability": {"flesch_kincaid": 12.5, "dale_chall": 8.2, "ari": 14.1},
#     "diff_blocks": [{"type": "replace", "content": "...", "original": "..."}],
#     "faithfulness": {"faithfulness": 0.72, "score": 0.72},
#     "llm_judge": {"coherence": 0.85, "persuasiveness": 0.75, "clarity": 0.90},
# }

# Standalone readability
readability = analyzer.compute_readability_scores(
    "The quick brown fox jumps over the lazy dog."
)
# → {"flesch_kincaid": 3.9, "dale_chall": 1.8, "ari": 3.3}

# Standalone diff
blocks = analyzer.compute_diff_blocks(
    draft="Hello world version A",
    published="Hello world version B",
)
# → [{"type": "replace", "content": "version B", "original": "version A"}]

# Tone consistency
tone = await analyzer.compute_tone_consistency(
    draft="...",
    published="...",
    brand_voice_exemplar="professional",
)
# → {"similarity": 0.85}

# Faithfulness
faith = await analyzer.compute_faithfulness(
    draft="AI content...",
    source_material="Original source...",
)
# → {"faithfulness": 0.72, "score": 0.72}

# LLM judge
judge = await analyzer.compute_llm_judge(
    draft="...",
    published="...",
)
# → {"coherence": 0.85, "persuasiveness": 0.75, "clarity": 0.90}
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

Generates CSV strings and PDF file path stubs from analytics data, with in-memory schedule management.

```python
from app.services.analytics.export_service import ExportService

svc = ExportService(data_store=None)

# CSV export
csv_content = await svc.export_csv(
    metric_selection=["engagement_rate", "reach"],
    date_range=("2026-01-01", "2026-01-31"),
    platform_filter="linkedin",  # optional
)
# → "date,engagement_rate,reach\n2026-01-01,0,0\n"

# PDF export (stub — returns dummy file path)
pdf_path = await svc.export_pdf(
    metric_selection=["engagement_rate"],
    date_range=("2026-01-01", "2026-01-31"),
    brand_config={"theme": "dark", "logo_url": "..."},
)
# → "/tmp/report_export_1.pdf"

# Check export status
status = await svc.get_export_status(export_id="export_1")
# → {"status": "completed", "id": "export_1"}

# Schedule management
schedule_id = await svc.create_schedule(
    export_type="csv",
    cadence="daily",
    metric_selection=["engagement_rate", "reach", "follower_growth"],
)

schedules = await svc.list_schedules()
# → [{"id": "...", "export_type": "csv", "cadence": "daily", "metric_selection": [...]}]

await svc.delete_schedule(schedule_id=schedule_id)
```

| Method | Description |
|--------|-------------|
| `export_csv(metric_selection, date_range, platform_filter)` | Generate CSV with headers and data rows |
| `export_pdf(metric_selection, date_range, brand_config)` | Generate PDF (stub — returns `/tmp/report_*.pdf`) |
| `get_export_status(export_id)` | Check if an export is completed or not found |
| `create_schedule(export_type, cadence, metric_selection)` | Create recurring export schedule |
| `delete_schedule(schedule_id)` | Remove an export schedule |
| `list_schedules()` | List all active export schedules |

---

## P2.2 — Trend Visualization

**File**: `src/app/services/analytics/trend_service.py`
**Models**: DataPoint, TrendData (`src/app/models/analytics.py`)

### TrendService

Computes time-series data with period-over-period deltas and top-content ranking.

```python
from app.services.analytics.trend_service import TrendService

svc = TrendService(data_store=None)

# Get trend for a metric
trend = await svc.get_trend(
    metric="engagement_rate",
    granularity="daily",
    from_date="2026-01-01",
    to_date="2026-01-31",
)
# → {
#     "metric": "engagement_rate",
#     "granularity": "daily",
#     "points": [
#         {"date": "2026-07-01", "value": 100.0},
#         {"date": "2026-07-02", "value": 110.0},
#         {"date": "2026-07-03", "value": 105.0},
#     ],
#     "period_over_period_delta": 7.33,
# }

# Get aggregated summary
summary = await svc.get_summary(
    from_date="2026-01-01",
    to_date="2026-01-31",
)
# → {"total_posts": 42, "total_reach": 15000, "avg_engagement_rate": 0.045, "top_platform": "linkedin"}

# Get top content
top = await svc.get_top_content(
    metric="engagement_rate",
    limit=5,
    from_date="2026-01-01",
    to_date="2026-01-31",
)
# → [{"post_id": "post_1", "engagement_rate": 100.0}, ...]

# Standalone period-over-period delta
delta = svc.compute_period_delta(
    current=[100.0, 110.0, 105.0],
    previous=[95.0, 98.0, 100.0],
)
# → 7.33 (mean(current) − mean(previous))
```

### TrendData & DataPoint Models

```python
from app.models.analytics import DataPoint, TrendData

point = DataPoint(date="2026-07-01", value=100.0)

trend = TrendData(
    points=[point],
    period_over_period_delta=7.33,
    metric="engagement_rate",
    granularity="daily",
)
```

---

## API Reference

All analytics endpoints produce JSON. No authentication required (open endpoints for the dashboard scaffold).

### List Posts

```
GET /api/v1/analytics/posts
```

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/analytics/posts
```

Response: `[PostMetrics]` array.

### Get Post

```
GET /api/v1/analytics/posts/{post_id}
```

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/analytics/posts/post_123
```

Response: `PostMetrics` object.

### Aggregate Summary

```
GET /api/v1/analytics/summary
```

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/analytics/summary
```

Response: `AnalyticsSummary` object.

### Calculate Optimization Score

```
POST /api/v1/analytics/optimization-score/calculate
```

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/analytics/optimization-score/calculate
```

Response: `OptimizationScore` object.

### Get Optimization Score

```
GET /api/v1/analytics/optimization-score/{post_id}
```

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/analytics/optimization-score/post_123
```

Response: `OptimizationScore` object.

### Validate Content

```
POST /api/v1/analytics/validate
```

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/analytics/validate
```

Response: `ValidationReport` object.

### Get Validation Report

```
GET /api/v1/analytics/validation/{job_id}
```

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/analytics/validation/val_001
```

Response: `ValidationReport` object.

### Export to CSV

```
POST /api/v1/analytics/export/csv
```

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/analytics/export/csv
```

Response: `{"export_id": "csv_...", "status": "completed"}`

### Export to PDF

```
POST /api/v1/analytics/export/pdf
```

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/analytics/export/pdf
```

Response: `{"export_id": "pdf_...", "status": "completed"}`

### Create Export Schedule

```
POST /api/v1/analytics/export/schedule
```

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/analytics/export/schedule
```

Response: `{"schedule_id": "schedule_...", "status": "active"}`

### Delete Export Schedule

```
DELETE /api/v1/analytics/export/schedule/{schedule_id}
```

```bash
curl -X DELETE \
  https://repurposeai-production-d688.up.railway.app/api/v1/analytics/export/schedule/schedule_new
```

Response: `{"schedule_id": "...", "status": "deleted"}`

### Get Export Status

```
GET /api/v1/analytics/export/{export_id}
```

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/analytics/export/export_1
```

Response: `{"export_id": "...", "status": "completed"}`

### Get Trend Data

```
GET /api/v1/analytics/trends/{metric}
```

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/analytics/trends/engagement_rate
```

Response: `TrendData` object.

### Trends Summary

```
GET /api/v1/analytics/trends/summary
```

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/analytics/trends/summary
```

Response: `{"total_posts": 42, "total_reach": 15000, "avg_engagement_rate": 0.045}`

### Top Content

```
GET /api/v1/analytics/trends/top-content
```

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/analytics/trends/top-content
```

Response: `[{"post_id": "post_1", "metric_value": 100.0}, ...]`

---

## Running Tests

```bash
# All analytics tests (1,670 individual test cases)
.venv/bin/python -m pytest tests/test_analytics_*.py -v

# Single module
.venv/bin/python -m pytest tests/test_analytics_scoring.py -v

# Specific test
.venv/bin/python -m pytest tests/test_analytics_scoring.py::test_calculate_returns_expected_range -v
```

| Test File | Tests | Module |
|-----------|-------|--------|
| `test_analytics_data_store.py` | 318 | P0.1 Data Store |
| `test_analytics_models.py` | 268 | Pydantic models |
| `test_analytics_scoring.py` | 145 | P1.1 Score Calculator |
| `test_analytics_validation.py` | 268 | P1.2 Validation Analyzer |
| `test_analytics_export.py` | 226 | P1.3/P2.1 CSV & PDF Export |
| `test_analytics_trends.py` | 233 | P2.2 Trend Service |
| `test_analytics_performance.py` | 212 | P0.2 Performance Tracking |

---

## Known Limitations

- All repositories use **in-memory storage** (data is lost on service restart)
- PDF export returns a **file path stub** only — no actual PDF generation
- Metrics collection returns **mock data** in scaffold — needs platform adapter implementations
- Trend data returns **sample points** — requires real metrics repository binding
- DatabaseConnection `execute`/`fetch` are **no-op stubs** — wiring to real SQLite/PostgreSQL pending
- No authentication on analytics endpoints (visible to all API consumers)
