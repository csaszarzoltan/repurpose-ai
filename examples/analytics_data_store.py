"""Example: P0.1 — Data Store usage.

Demonstrates DatabaseConnection lifecycle, CRUD repositories, and schema migrations.
"""

import asyncio

from app.services.analytics.db.connection import DatabaseConnection
from app.services.analytics.db.migrations import Migration, Migrator
from app.services.analytics.db.repository import (
    MetricsRepository,
    ScoreRepository,
    ValidationRepository,
)


async def main() -> None:
    # ── DatabaseConnection lifecycle ──
    db = DatabaseConnection(connection_string="sqlite:///analytics.db")
    await db.connect()
    assert db.is_connected is True
    print(f"Connected: {db.is_connected}")

    await db.execute("CREATE TABLE IF NOT EXISTS metrics (id INTEGER PRIMARY KEY)")
    rows = await db.fetch("SELECT * FROM metrics")
    print(f"Query rows: {rows}")

    await db.disconnect()
    assert db.is_connected is False
    print(f"Disconnected: {not db.is_connected}")

    # ── MetricsRepository ──
    mrepo = MetricsRepository()
    post_id = await mrepo.store_metrics(
        platform="linkedin",
        post_id="post_123",
        metrics={"engagement_rate": 0.05, "reach": 1000},
    )
    print(f"Stored post: {post_id}")

    results = await mrepo.query_metrics(
        platform="linkedin", from_date=None, to_date=None
    )
    print(f"Queried metrics: {results}")

    # ── ValidationRepository ──
    vrepo = ValidationRepository()
    job_id = await vrepo.store_validation(
        job_id="val_001",
        draft="AI draft content",
        published="Published content",
        scores={"quality_delta": 0.15},
    )
    print(f"Validation job: {job_id}")

    report = await vrepo.query_validation(job_id="val_001")
    print(f"Validation report: {report}")

    # ── ScoreRepository ──
    srepo = ScoreRepository()
    score_id = await srepo.store_score(
        post_id="post_123",
        platform="linkedin",
        overall_score=78.5,
        signals={"engagement_rate": 0.05},
    )
    print(f"Score ID: {score_id}")

    score = await srepo.query_score(post_id="post_123", platform="linkedin")
    print(f"Retrieved score: {score}")

    # ── Migrations ──
    migration = Migration(
        version=1,
        description="Create metrics table",
        sql_up="CREATE TABLE metrics (...)",
        sql_down="DROP TABLE metrics",
    )
    print(f"Migration v{migration.version}: {migration.description}")

    migrator = Migrator(connection_string="sqlite:///analytics.db")
    current = await migrator.apply(target_version=1)
    print(f"Migrated to version: {current}")

    rollback = await migrator.rollback(target_version=0)
    print(f"Rolled back to version: {rollback}")

    version = await migrator.current_version()
    print(f"Current version: {version}")

    pending = await migrator.pending_migrations()
    print(f"Pending migrations: {len(pending)}")


if __name__ == "__main__":
    asyncio.run(main())
