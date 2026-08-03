"""CRUD repository — analytics data store backed by SQLite.

Source of truth: analysis/analysis-brief.md §4 P0.1.

Each repository owns a SQLite connection. The default connection is an
in-memory database (``:memory:``), which gives every repository instance an
isolated store — this is what the test suite relies on. Pass a
``connection_string`` (a file path or ``sqlite:///`` URI) to persist across
process restarts in production.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any
from uuid import uuid4


def _json_default(obj: Any) -> str:
    """JSON encoder fallback: serialise datetimes to ISO 8601 strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _json_dumps(value: dict) -> str:
    return json.dumps(value, default=_json_default, ensure_ascii=False)


def _restore_datetime(value: Any) -> Any:
    """Best-effort: parse ISO datetime strings back into datetime objects."""
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return value
    return value


def _iso(value: Any) -> str | None:
    """Normalise a date-like value to an ISO 8601 string for SQLite storage."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _connect(connection_string: str) -> sqlite3.Connection:
    conn = sqlite3.connect(connection_string or ":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


class MetricsRepository:
    """Time-series metrics storage and retrieval, persisted in SQLite."""

    def __init__(self, connection_string: str = "") -> None:
        self._connection_string = connection_string or ":memory:"
        self._conn = _connect(self._connection_string)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS analytics_metrics ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " platform TEXT NOT NULL,"
            " post_id TEXT NOT NULL,"
            " post_date TEXT,"
            " data_json TEXT NOT NULL,"
            " UNIQUE (platform, post_id))"
        )
        self._conn.commit()

    async def store_metrics(
        self,
        platform: str,
        post_id: str,
        metrics: dict,
    ) -> str:
        """Store metrics and return a post ID."""
        payload = dict(metrics)
        post_date = _iso(payload.get("post_date"))
        self._conn.execute(
            "INSERT INTO analytics_metrics (platform, post_id, post_date, data_json)"
            " VALUES (?, ?, ?, ?)"
            " ON CONFLICT(platform, post_id) DO UPDATE SET"
            " post_date=excluded.post_date, data_json=excluded.data_json",
            (platform, post_id, post_date, _json_dumps(payload)),
        )
        self._conn.commit()
        return post_id

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        result = json.loads(row["data_json"])
        result["platform"] = row["platform"]
        result["post_id"] = row["post_id"]
        if "post_date" in result:
            result["post_date"] = _restore_datetime(result["post_date"])
        return result

    async def query_metrics(
        self,
        platform: str,
        from_date: object,
        to_date: object,
        granularity: str = "daily",
    ) -> list[dict]:
        """Query stored metrics for a platform, optionally within a date range.

        Posts without a recorded ``post_date`` are always included so that
        partial ingestion is never hidden by a date filter.
        """
        sql = "SELECT * FROM analytics_metrics WHERE platform = ?"
        params: list[Any] = [platform]
        clauses: list[str] = []
        if from_date is not None:
            clauses.append("post_date >= ?")
            params.append(_iso(from_date))
        if to_date is not None:
            clauses.append("post_date <= ?")
            params.append(_iso(to_date))
        if clauses:
            sql += " AND (post_date IS NULL OR (" + " AND ".join(clauses) + "))"
        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def list_all(self) -> list[dict]:
        """Return every stored metrics row (all platforms)."""
        rows = self._conn.execute(
            "SELECT * FROM analytics_metrics ORDER BY id"
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    async def get_by_post_id(self, post_id: str) -> dict | None:
        """Return the metrics row for a single post, or None if unknown."""
        row = self._conn.execute(
            "SELECT * FROM analytics_metrics WHERE post_id = ?", (post_id,)
        ).fetchone()
        return self._row_to_dict(row) if row is not None else None


class ValidationRepository:
    """Validation report storage and retrieval, persisted in SQLite."""

    def __init__(self, connection_string: str = "") -> None:
        self._connection_string = connection_string or ":memory:"
        self._conn = _connect(self._connection_string)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS analytics_validations ("
            " job_id TEXT PRIMARY KEY,"
            " draft TEXT NOT NULL,"
            " published TEXT NOT NULL,"
            " report_json TEXT NOT NULL)"
        )
        self._conn.commit()

    async def store_validation(
        self,
        job_id: str,
        draft: str,
        published: str,
        scores: dict,
    ) -> str:
        """Store a validation result and return the job ID."""
        self._conn.execute(
            "INSERT INTO analytics_validations (job_id, draft, published, report_json)"
            " VALUES (?, ?, ?, ?)"
            " ON CONFLICT(job_id) DO UPDATE SET"
            " draft=excluded.draft, published=excluded.published, report_json=excluded.report_json",
            (job_id, draft, published, _json_dumps(scores)),
        )
        self._conn.commit()
        return job_id

    async def query_validation(self, job_id: str) -> dict:
        """Retrieve a validation report by job ID ({} if unknown)."""
        row = self._conn.execute(
            "SELECT * FROM analytics_validations WHERE job_id = ?", (job_id,)
        ).fetchone()
        if row is None:
            return {}
        report = json.loads(row["report_json"])
        report["job_id"] = row["job_id"]
        report["draft"] = row["draft"]
        report["published"] = row["published"]
        return report


class ScoreRepository:
    """Optimization score storage and retrieval, persisted in SQLite."""

    def __init__(self, connection_string: str = "") -> None:
        self._connection_string = connection_string or ":memory:"
        self._conn = _connect(self._connection_string)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS analytics_scores ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " score_id TEXT NOT NULL,"
            " post_id TEXT NOT NULL,"
            " platform TEXT NOT NULL,"
            " overall_score REAL NOT NULL,"
            " signals_json TEXT NOT NULL)"
        )
        self._conn.commit()

    async def store_score(
        self,
        post_id: str,
        platform: str,
        overall_score: float,
        signals: dict[str, float],
    ) -> str:
        """Store a score and return a unique ID."""
        score_id = str(uuid4())
        self._conn.execute(
            "INSERT INTO analytics_scores"
            " (score_id, post_id, platform, overall_score, signals_json)"
            " VALUES (?, ?, ?, ?, ?)",
            (score_id, post_id, platform, float(overall_score), json.dumps(signals or {})),
        )
        self._conn.commit()
        return score_id

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        return {
            "id": row["score_id"],
            "post_id": row["post_id"],
            "platform": row["platform"],
            "overall_score": row["overall_score"],
            "signals": json.loads(row["signals_json"]),
        }

    async def query_score(self, post_id: str, platform: str) -> dict:
        """Retrieve the latest score by post ID and platform ({} if unknown)."""
        row = self._conn.execute(
            "SELECT * FROM analytics_scores WHERE post_id = ? AND platform = ?"
            " ORDER BY id DESC LIMIT 1",
            (post_id, platform),
        ).fetchone()
        return self._row_to_dict(row) if row is not None else {}

    async def query_score_by_post(self, post_id: str) -> dict:
        """Retrieve the latest score for a post across any platform ({} if unknown)."""
        row = self._conn.execute(
            "SELECT * FROM analytics_scores WHERE post_id = ?"
            " ORDER BY id DESC LIMIT 1",
            (post_id,),
        ).fetchone()
        return self._row_to_dict(row) if row is not None else {}
