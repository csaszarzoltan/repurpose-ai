"""Schema migration — analytics data store.

Source of truth: analysis/analysis-brief.md §4 P0.1.
"""

from __future__ import annotations


class Migration:
    """A single schema migration step."""

    def __init__(self, version: int, description: str, sql_up: str, sql_down: str) -> None:
        self.version = version
        self.description = description
        self.sql_up = sql_up
        self.sql_down = sql_down


class Migrator:
    """Manages database schema migrations for analytics."""

    def __init__(self, connection_string: str = "") -> None:
        self._connection_string = connection_string

    async def apply(self, target_version: int | None = None) -> int:
        """Apply pending migrations and return current version."""
        return target_version if target_version is not None else 1

    async def rollback(self, target_version: int | None = None) -> int:
        """Roll back migrations to target version."""
        return target_version if target_version is not None else 0

    async def current_version(self) -> int:
        """Return the current schema version."""
        return 0

    async def pending_migrations(self) -> list[Migration]:
        """Return list of pending migrations (empty in stub)."""
        return []
