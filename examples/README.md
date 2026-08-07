# Examples

Working Python scripts demonstrating analytics modules and platform publishing. Run from the repo root.

## Prerequisites

```bash
cd repurpose-ai
.venv/bin/pip install -e ".[dev]"  # ensure dependencies installed
```

## Scripts

| Script | Module | Description |
|--------|--------|-------------|
| `publish_wordpress.py` | Publish | WordPress REST API publisher: create_post, payload, excerpt derivation, site routing |
| `publish_ghost.py` | Publish | Ghost Admin API publisher: create_post, payload, JWT auth, tag mapping |
| `analytics_data_store.py` | P0.1 | DatabaseConnection, MetricsRepository, ValidationRepository, ScoreRepository, Migrator |
| `analytics_performance.py` | P0.2 | MetricsCollector, PostMetrics, AnalyticsSummary |
| `analytics_scoring.py` | P1.1 | ScoreCalculator, OptimizationScore |
| `analytics_validation.py` | P1.2 | ValidationAnalyzer, ValidationReport |
| `analytics_export.py` | P1.3/P2.1 | ExportService CSV/PDF, schedule management |
| `analytics_trends.py` | P2.2 | TrendService, TrendData, DataPoint |
| `run_all.py` | All | Runs all analytics examples in sequence |

## Run

```bash
# Single example
.venv/bin/python examples/analytics_data_store.py

# All examples
.venv/bin/python examples/run_all.py
```

All scripts use async/await and import from `app.*` — run them from the repo root so the Python path resolves correctly.
