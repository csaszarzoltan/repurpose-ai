"""Pre-dev tests for analytics data store (P0.1).

Source of truth: analysis/analysis-brief.md §4 P0.1 — repository, connection, migrations.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

# ── Module availability guards ──────────────────────────────────────────────

try:
    from app.services.analytics.db.connection import DatabaseConnection
    HAS_CONNECTION = True
except (ImportError, ModuleNotFoundError):
    HAS_CONNECTION = False

try:
    from app.services.analytics.db.repository import MetricsRepository, ScoreRepository, ValidationRepository
    HAS_REPOSITORY = True
except (ImportError, ModuleNotFoundError):
    HAS_REPOSITORY = False

try:
    from app.services.analytics.db.migrations import Migration, Migrator
    HAS_MIGRATIONS = True
except (ImportError, ModuleNotFoundError):
    HAS_MIGRATIONS = False


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — DatabaseConnection
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_CONNECTION, reason="connection.py not implemented yet")
class TestDatabaseConnectionInterface:
    """Interface: DatabaseConnection is importable and has expected API."""

    def test_importable(self):
        assert DatabaseConnection is not None

    def test_is_class(self):
        assert isinstance(DatabaseConnection, type)

    def test_init_accepts_connection_string(self):
        conn = DatabaseConnection(connection_string="sqlite:///test.db")
        assert conn is not None

    def test_has_connect_method(self):
        import inspect
        assert hasattr(DatabaseConnection, "connect")
        assert inspect.iscoroutinefunction(DatabaseConnection.connect)

    def test_has_disconnect_method(self):
        import inspect
        assert hasattr(DatabaseConnection, "disconnect")
        assert inspect.iscoroutinefunction(DatabaseConnection.disconnect)

    def test_has_execute_method(self):
        import inspect
        assert hasattr(DatabaseConnection, "execute")
        assert inspect.iscoroutinefunction(DatabaseConnection.execute)

    def test_has_fetch_method(self):
        import inspect
        assert hasattr(DatabaseConnection, "fetch")
        assert inspect.iscoroutinefunction(DatabaseConnection.fetch)

    def test_has_is_connected_property(self):
        assert hasattr(DatabaseConnection, "is_connected")


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Repositories
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_REPOSITORY, reason="repository.py not implemented yet")
class TestMetricsRepositoryInterface:
    """Interface: MetricsRepository is importable and has expected API."""

    def test_importable(self):
        assert MetricsRepository is not None

    def test_is_class(self):
        assert isinstance(MetricsRepository, type)

    def test_has_store_metrics_method(self):
        import inspect
        assert hasattr(MetricsRepository, "store_metrics")
        assert inspect.iscoroutinefunction(MetricsRepository.store_metrics)

    def test_has_query_metrics_method(self):
        import inspect
        assert hasattr(MetricsRepository, "query_metrics")
        assert inspect.iscoroutinefunction(MetricsRepository.query_metrics)

    def test_query_metrics_accepts_granularity(self):
        import inspect
        sig = inspect.signature(MetricsRepository.query_metrics)
        params = list(sig.parameters.keys())
        assert "granularity" in params
        assert "from_date" in params
        assert "to_date" in params


@pytest.mark.xfail(not HAS_REPOSITORY, reason="repository.py not implemented yet")
class TestValidationRepositoryInterface:
    """Interface: ValidationRepository is importable and has expected API."""

    def test_importable(self):
        assert ValidationRepository is not None

    def test_has_store_validation_method(self):
        import inspect
        assert hasattr(ValidationRepository, "store_validation")
        assert inspect.iscoroutinefunction(ValidationRepository.store_validation)

    def test_has_query_validation_method(self):
        import inspect
        assert hasattr(ValidationRepository, "query_validation")
        assert inspect.iscoroutinefunction(ValidationRepository.query_validation)


@pytest.mark.xfail(not HAS_REPOSITORY, reason="repository.py not implemented yet")
class TestScoreRepositoryInterface:
    """Interface: ScoreRepository is importable and has expected API."""

    def test_importable(self):
        assert ScoreRepository is not None

    def test_has_store_score_method(self):
        import inspect
        assert hasattr(ScoreRepository, "store_score")
        assert inspect.iscoroutinefunction(ScoreRepository.store_score)

    def test_has_query_score_method(self):
        import inspect
        assert hasattr(ScoreRepository, "query_score")
        assert inspect.iscoroutinefunction(ScoreRepository.query_score)


# ═══════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — Migrations
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_MIGRATIONS, reason="migrations.py not implemented yet")
class TestMigrationInterface:
    """Interface: Migration class is importable."""

    def test_importable(self):
        assert Migration is not None

    def test_is_class(self):
        assert isinstance(Migration, type)

    def test_init_accepts_version_desc_sql(self):
        m = Migration(version=1, description="initial", sql_up="CREATE TABLE ...", sql_down="DROP TABLE ...")
        assert m is not None


@pytest.mark.xfail(not HAS_MIGRATIONS, reason="migrations.py not implemented yet")
class TestMigratorInterface:
    """Interface: Migrator class is importable and has expected API."""

    def test_importable(self):
        assert Migrator is not None

    def test_is_class(self):
        assert isinstance(Migrator, type)

    def test_has_apply_method(self):
        import inspect
        assert hasattr(Migrator, "apply")
        assert inspect.iscoroutinefunction(Migrator.apply)

    def test_has_rollback_method(self):
        import inspect
        assert hasattr(Migrator, "rollback")
        assert inspect.iscoroutinefunction(Migrator.rollback)

    def test_has_current_version_method(self):
        import inspect
        assert hasattr(Migrator, "current_version")
        assert inspect.iscoroutinefunction(Migrator.current_version)

    def test_has_pending_migrations_method(self):
        import inspect
        assert hasattr(Migrator, "pending_migrations")
        assert inspect.iscoroutinefunction(Migrator.pending_migrations)


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — DatabaseConnection
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_CONNECTION, reason="connection.py not implemented yet")
class TestDatabaseConnectionBehavior:
    """Behavioral: DatabaseConnection lifecycle."""

    async def test_connect_changes_state(self):
        conn = DatabaseConnection("sqlite:///:memory:")
        assert conn.is_connected is False
        await conn.connect()
        assert conn.is_connected is True

    async def test_disconnect_changes_state(self):
        conn = DatabaseConnection("sqlite:///:memory:")
        await conn.connect()
        await conn.disconnect()
        assert conn.is_connected is False

    async def test_execute_accepts_query(self):
        conn = DatabaseConnection("sqlite:///:memory:")
        await conn.connect()
        await conn.execute("SELECT 1")


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — MetricsRepository
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_REPOSITORY, reason="repository.py not implemented yet")
class TestMetricsRepositoryBehavior:
    """Behavioral: MetricsRepository CRUD operations."""

    async def test_store_and_query_metrics(self):
        repo = MetricsRepository()
        metrics = {"reach": 100, "impressions": 200}
        post_id = await repo.store_metrics("linkedin", "post_123", metrics)
        assert post_id is not None

        results = await repo.query_metrics(
            "linkedin",
            from_date=datetime(2026, 1, 1, tzinfo=UTC),
            to_date=datetime(2026, 12, 31, tzinfo=UTC),
            granularity="daily",
        )
        assert len(results) > 0

    async def test_query_with_different_granularity(self):
        repo = MetricsRepository()
        results = await repo.query_metrics(
            "twitter",
            from_date=datetime(2026, 6, 1, tzinfo=UTC),
            to_date=datetime(2026, 6, 30, tzinfo=UTC),
            granularity="weekly",
        )
        assert isinstance(results, list)


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — ValidationRepository
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_REPOSITORY, reason="repository.py not implemented yet")
class TestValidationRepositoryBehavior:
    """Behavioral: ValidationRepository CRUD."""

    async def test_store_validation_returns_job_id(self):
        repo = ValidationRepository()
        job_id = await repo.store_validation("job_1", "draft text", "published text", {"quality_delta": 0.05})
        assert job_id is not None

    async def test_query_validation_returns_report(self):
        repo = ValidationRepository()
        report = await repo.query_validation("job_1")
        assert isinstance(report, dict)


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — ScoreRepository
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_REPOSITORY, reason="repository.py not implemented yet")
class TestScoreRepositoryBehavior:
    """Behavioral: ScoreRepository CRUD."""

    async def test_store_and_query_score(self):
        repo = ScoreRepository()
        score_id = await repo.store_score("post_1", "linkedin", 85.0, {"dwell_time": 0.9})
        assert score_id is not None

        result = await repo.query_score("post_1", "linkedin")
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — Migrations
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(not HAS_MIGRATIONS, reason="migrations.py not implemented yet")
class TestMigratorBehavior:
    """Behavioral: Migrator apply/rollback lifecycle."""

    async def test_apply_migrations(self):
        migrator = Migrator()
        version = await migrator.apply()
        assert version > 0

    async def test_rollback_migrations(self):
        migrator = Migrator()
        version = await migrator.rollback(target_version=0)
        assert version == 0

    async def test_current_version_returns_int(self):
        migrator = Migrator()
        version = await migrator.current_version()
        assert isinstance(version, int)
