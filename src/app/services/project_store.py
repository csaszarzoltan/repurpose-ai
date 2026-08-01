"""Small durable SQLite repository for content projects and privacy-safe events."""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.models.project import ProjectCreate, ProjectResponse, ProjectStatus, ProjectUpdate, TelemetryEvent


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ProjectStore:
    def __init__(self, data_dir: str | Path | None = None) -> None:
        root = Path(data_dir or os.getenv("REPURPOSEAI_DATA_DIR", "./data"))
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / "repurposeai.sqlite3"
        self._migrate()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _migrate(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS content_projects (
                    id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    source_format TEXT NOT NULL,
                    target_formats TEXT NOT NULL,
                    brand_voice TEXT NOT NULL,
                    custom_instructions TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_projects_owner_updated
                    ON content_projects(owner_id, updated_at DESC);
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    event_name TEXT NOT NULL,
                    properties TEXT NOT NULL,
                    occurred_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _row(row: sqlite3.Row) -> ProjectResponse:
        data = dict(row)
        data["target_formats"] = json.loads(data["target_formats"])
        return ProjectResponse.model_validate(data)

    def create(self, owner_id: str, payload: ProjectCreate) -> ProjectResponse:
        project_id, timestamp = str(uuid.uuid4()), _now()
        with self._connect() as db:
            db.execute(
                """INSERT INTO content_projects
                (id, owner_id, title, body, source_format, target_formats, brand_voice,
                 custom_instructions, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    project_id, owner_id, payload.title, payload.body, payload.source_format.value,
                    json.dumps([item.value for item in payload.target_formats]), payload.brand_voice.value,
                    payload.custom_instructions, ProjectStatus.DRAFT.value, timestamp, timestamp,
                ),
            )
        return self.get(owner_id, project_id)

    def list(self, owner_id: str, include_archived: bool = False, query: str | None = None) -> list[ProjectResponse]:
        sql = "SELECT * FROM content_projects WHERE owner_id = ?"
        params: list[str] = [owner_id]
        if not include_archived:
            sql += " AND status != ?"
            params.append(ProjectStatus.ARCHIVED.value)
        if query:
            sql += " AND (title LIKE ? OR body LIKE ?)"
            term = f"%{query[:100]}%"
            params.extend([term, term])
        sql += " ORDER BY updated_at DESC LIMIT 100"
        with self._connect() as db:
            return [self._row(row) for row in db.execute(sql, params).fetchall()]

    def get(self, owner_id: str, project_id: str) -> ProjectResponse:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM content_projects WHERE owner_id = ? AND id = ?", (owner_id, project_id)
            ).fetchone()
        if row is None:
            raise KeyError(project_id)
        return self._row(row)

    def update(self, owner_id: str, project_id: str, payload: ProjectUpdate) -> ProjectResponse:
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return self.get(owner_id, project_id)
        if "target_formats" in changes:
            changes["target_formats"] = json.dumps([item.value for item in changes["target_formats"]])
        for key in ("brand_voice", "status"):
            if key in changes and changes[key] is not None:
                changes[key] = changes[key].value
        changes["updated_at"] = _now()
        assignments = ", ".join(f"{key} = ?" for key in changes)
        values = list(changes.values()) + [owner_id, project_id]
        with self._connect() as db:
            result = db.execute(
                f"UPDATE content_projects SET {assignments} WHERE owner_id = ? AND id = ?", values
            )
            if result.rowcount == 0:
                raise KeyError(project_id)
        return self.get(owner_id, project_id)

    def archive(self, owner_id: str, project_id: str) -> None:
        self.update(owner_id, project_id, ProjectUpdate(status=ProjectStatus.ARCHIVED))

    def record_event(self, owner_id: str, event: TelemetryEvent) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO telemetry_events VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), owner_id, event.event_name, json.dumps(event.properties), event.occurred_at.isoformat()),
            )
