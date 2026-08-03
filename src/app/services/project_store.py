"""Small durable SQLite repository for content projects and privacy-safe events."""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.models.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectStatus,
    ProjectUpdate,
    RecipeCreate,
    RecipeResponse,
    RecipeUpdate,
    TelemetryEvent,
    VariantResponse,
    VariantStatus,
    WorkspaceSummary,
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


# Allowlisted columns for UPDATE statements. Keys are NEVER taken from caller
# data: anything not in this set raises ValueError instead of being interpolated
# into the SQL text (security-gate finding — column-name injection hardening).
PROJECT_UPDATE_COLUMNS = frozenset({
    "title",
    "body",
    "source_format",
    "target_formats",
    "brand_voice",
    "custom_instructions",
    "status",
    "updated_at",
})
RECIPE_UPDATE_COLUMNS = frozenset({
    "name",
    "target_formats",
    "brand_voice",
    "custom_instructions",
    "updated_at",
})


def _update_assignments(changes: dict, allowed_columns: frozenset[str]) -> str:
    """Build a parameterized ``SET`` clause from an allowlist of columns.

    Unknown keys raise ValueError — column names are never interpolated from
    caller-supplied data.
    """
    unknown = sorted(set(changes) - allowed_columns)
    if unknown:
        raise ValueError(f"unknown column(s) for update: {', '.join(unknown)}")
    return ", ".join(f"{key} = ?" for key in changes)


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
                CREATE TABLE IF NOT EXISTS content_variants (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    format TEXT NOT NULL,
                    content TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    generation_mode TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES content_projects(id)
                );
                CREATE UNIQUE INDEX IF NOT EXISTS ux_variant_version
                    ON content_variants(project_id, format, version);
                CREATE INDEX IF NOT EXISTS ix_variants_project_created
                    ON content_variants(owner_id, project_id, created_at DESC);
                CREATE TABLE IF NOT EXISTS generation_recipes (
                    id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    target_formats TEXT NOT NULL,
                    brand_voice TEXT NOT NULL,
                    custom_instructions TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_recipes_owner_updated
                    ON generation_recipes(owner_id, updated_at DESC);
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
        assignments = _update_assignments(changes, PROJECT_UPDATE_COLUMNS)
        values = list(changes.values()) + [owner_id, project_id]
        sql = "UPDATE content_projects SET " + assignments + " WHERE owner_id = ? AND id = ?"
        with self._connect() as db:
            result = db.execute(sql, values)
            if result.rowcount == 0:
                raise KeyError(project_id)
        return self.get(owner_id, project_id)

    def duplicate(self, owner_id: str, project_id: str, title: str | None = None) -> ProjectResponse:
        """Copy reusable project inputs while deliberately excluding variants and status."""
        source = self.get(owner_id, project_id)
        return self.create(
            owner_id,
            ProjectCreate(
                title=title or f"{source.title} copy",
                body=source.body,
                source_format=source.source_format,
                target_formats=source.target_formats,
                brand_voice=source.brand_voice,
                custom_instructions=source.custom_instructions,
            ),
        )

    def archive(self, owner_id: str, project_id: str) -> None:
        self.update(owner_id, project_id, ProjectUpdate(status=ProjectStatus.ARCHIVED))

    def restore_project(self, owner_id: str, project_id: str) -> ProjectResponse:
        """Restore an archived project without touching its immutable variant history."""
        project = self.get(owner_id, project_id)
        if project.status != ProjectStatus.ARCHIVED:
            return project
        return self.update(owner_id, project_id, ProjectUpdate(status=ProjectStatus.DRAFT))

    def workspace_summary(self, owner_id: str) -> WorkspaceSummary:
        """Return bounded attention counts based only on each format's latest version."""
        with self._connect() as db:
            active_projects = db.execute(
                "SELECT COUNT(*) FROM content_projects WHERE owner_id = ? AND status != ?",
                (owner_id, ProjectStatus.ARCHIVED.value),
            ).fetchone()[0]
            projects_without_drafts = db.execute(
                """SELECT COUNT(*) FROM content_projects p
                WHERE p.owner_id = ? AND p.status != ? AND NOT EXISTS (
                    SELECT 1 FROM content_variants v
                    WHERE v.owner_id = p.owner_id AND v.project_id = p.id
                )""",
                (owner_id, ProjectStatus.ARCHIVED.value),
            ).fetchone()[0]
            rows = db.execute(
                """WITH latest AS (
                    SELECT project_id, format, MAX(version) AS version
                    FROM content_variants WHERE owner_id = ? GROUP BY project_id, format
                )
                SELECT v.status, v.generation_mode, COUNT(*) AS count
                FROM content_variants v JOIN latest l
                  ON l.project_id = v.project_id AND l.format = v.format AND l.version = v.version
                JOIN content_projects p ON p.id = v.project_id
                WHERE v.owner_id = ? AND p.status != ?
                GROUP BY v.status, v.generation_mode""",
                (owner_id, owner_id, ProjectStatus.ARCHIVED.value),
            ).fetchall()
        draft = approved = fallback = 0
        for row in rows:
            count = int(row["count"])
            if row["status"] == VariantStatus.DRAFT.value:
                draft += count
                if row["generation_mode"] in {"template_fallback", "llm_fallback"}:
                    fallback += count
            elif row["status"] == VariantStatus.APPROVED.value:
                approved += count
        return WorkspaceSummary(
            active_projects=active_projects,
            projects_without_drafts=projects_without_drafts,
            draft_variants=draft,
            approved_variants=approved,
            fallback_variants_needing_review=fallback,
        )

    def record_event(self, owner_id: str, event: TelemetryEvent) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO telemetry_events VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), owner_id, event.event_name, json.dumps(event.properties), event.occurred_at.isoformat()),
            )


    @staticmethod
    def _variant_row(row: sqlite3.Row) -> VariantResponse:
        return VariantResponse.model_validate(dict(row))

    def create_variant(
        self,
        owner_id: str,
        project_id: str,
        format_id: str,
        content: str,
        generation_mode: str,
        status: VariantStatus = VariantStatus.DRAFT,
    ) -> VariantResponse:
        self.get(owner_id, project_id)
        with self._connect() as db:
            current = db.execute(
                "SELECT COALESCE(MAX(version), 0) FROM content_variants "
                "WHERE owner_id = ? AND project_id = ? AND format = ?",
                (owner_id, project_id, format_id),
            ).fetchone()[0]
            variant_id, created_at = str(uuid.uuid4()), _now()
            db.execute(
                """INSERT INTO content_variants
                (id, project_id, owner_id, format, content, version, status, generation_mode, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    variant_id, project_id, owner_id, format_id, content,
                    current + 1, status.value, generation_mode, created_at,
                ),
            )
            row = db.execute("SELECT * FROM content_variants WHERE id = ?", (variant_id,)).fetchone()
        return self._variant_row(row)

    def get_variant(self, owner_id: str, project_id: str, variant_id: str) -> VariantResponse:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM content_variants WHERE owner_id = ? AND project_id = ? AND id = ?",
                (owner_id, project_id, variant_id),
            ).fetchone()
        if row is None:
            raise KeyError(variant_id)
        return self._variant_row(row)

    def list_variants(
        self, owner_id: str, project_id: str, include_history: bool = False
    ) -> list[VariantResponse]:
        self.get(owner_id, project_id)
        if include_history:
            sql = (
                "SELECT * FROM content_variants WHERE owner_id = ? AND project_id = ? "
                "ORDER BY format, version DESC"
            )
            params = (owner_id, project_id)
        else:
            sql = """SELECT v.* FROM content_variants v
                JOIN (
                    SELECT format, MAX(version) AS version FROM content_variants
                    WHERE owner_id = ? AND project_id = ? GROUP BY format
                ) latest ON latest.format = v.format AND latest.version = v.version
                WHERE v.owner_id = ? AND v.project_id = ? ORDER BY v.format"""
            params = (owner_id, project_id, owner_id, project_id)
        with self._connect() as db:
            return [self._variant_row(row) for row in db.execute(sql, params).fetchall()]

    def restore_variant(
        self, owner_id: str, project_id: str, variant_id: str
    ) -> VariantResponse:
        """Restore historical content as a new draft version, preserving all history."""
        historical = self.get_variant(owner_id, project_id, variant_id)
        return self.create_variant(
            owner_id=owner_id,
            project_id=project_id,
            format_id=historical.format.value,
            content=historical.content,
            generation_mode="history_restore",
            status=VariantStatus.DRAFT,
        )

    def revise_variant(
        self,
        owner_id: str,
        project_id: str,
        variant_id: str,
        content: str,
        status: VariantStatus,
    ) -> VariantResponse:
        previous = self.get_variant(owner_id, project_id, variant_id)
        return self.create_variant(
            owner_id=owner_id,
            project_id=project_id,
            format_id=previous.format.value,
            content=content,
            generation_mode="manual_edit",
            status=status,
        )


    @staticmethod
    def _recipe_row(row: sqlite3.Row) -> RecipeResponse:
        data = dict(row)
        data["target_formats"] = json.loads(data["target_formats"])
        return RecipeResponse.model_validate(data)

    def create_recipe(self, owner_id: str, payload: RecipeCreate) -> RecipeResponse:
        recipe_id, timestamp = str(uuid.uuid4()), _now()
        with self._connect() as db:
            db.execute(
                """INSERT INTO generation_recipes
                (id, owner_id, name, target_formats, brand_voice, custom_instructions,
                 created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    recipe_id,
                    owner_id,
                    payload.name,
                    json.dumps([item.value for item in payload.target_formats]),
                    payload.brand_voice.value,
                    payload.custom_instructions,
                    timestamp,
                    timestamp,
                ),
            )
        return self.get_recipe(owner_id, recipe_id)

    def list_recipes(self, owner_id: str) -> list[RecipeResponse]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM generation_recipes WHERE owner_id = ? "
                "ORDER BY updated_at DESC LIMIT 100",
                (owner_id,),
            ).fetchall()
        return [self._recipe_row(row) for row in rows]

    def get_recipe(self, owner_id: str, recipe_id: str) -> RecipeResponse:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM generation_recipes WHERE owner_id = ? AND id = ?",
                (owner_id, recipe_id),
            ).fetchone()
        if row is None:
            raise KeyError(recipe_id)
        return self._recipe_row(row)

    def update_recipe(
        self, owner_id: str, recipe_id: str, payload: RecipeUpdate
    ) -> RecipeResponse:
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return self.get_recipe(owner_id, recipe_id)
        if "target_formats" in changes:
            changes["target_formats"] = json.dumps(
                [item.value for item in changes["target_formats"]]
            )
        if "brand_voice" in changes and changes["brand_voice"] is not None:
            changes["brand_voice"] = changes["brand_voice"].value
        changes["updated_at"] = _now()
        assignments = _update_assignments(changes, RECIPE_UPDATE_COLUMNS)
        values = list(changes.values()) + [owner_id, recipe_id]
        sql = "UPDATE generation_recipes SET " + assignments + " WHERE owner_id = ? AND id = ?"
        with self._connect() as db:
            result = db.execute(sql, values)
            if result.rowcount == 0:
                raise KeyError(recipe_id)
        return self.get_recipe(owner_id, recipe_id)

    def delete_recipe(self, owner_id: str, recipe_id: str) -> None:
        with self._connect() as db:
            result = db.execute(
                "DELETE FROM generation_recipes WHERE owner_id = ? AND id = ?",
                (owner_id, recipe_id),
            )
            if result.rowcount == 0:
                raise KeyError(recipe_id)
