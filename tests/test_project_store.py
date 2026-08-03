"""Regression tests: UPDATE column names in ProjectStore are allowlisted.

Security-gate finding: project_store.py previously built UPDATE statements by
string-interpolating caller-supplied dict keys (``f"{key} = ?"``). While today's
callers pass Pydantic models (keys are whitelisted field names), any future caller
passing a user-derived dict could inject column names into the SQL. These tests pin
the hardened behavior: unknown keys raise ValueError instead of being interpolated.
"""
from __future__ import annotations

import pytest

from app.models.project import ProjectCreate, ProjectUpdate, RecipeCreate
from app.services.project_store import (
    PROJECT_UPDATE_COLUMNS,
    RECIPE_UPDATE_COLUMNS,
    ProjectStore,
    _update_assignments,
)

# ─── allowlist helper ───────────────────────────────────────────────────────────

def test_update_assignments_builds_parameterized_clause_from_known_columns():
    clause = _update_assignments({"title": "x", "status": "draft"}, PROJECT_UPDATE_COLUMNS)
    assert clause == "title = ?, status = ?"


def test_update_assignments_rejects_unknown_column_for_projects():
    with pytest.raises(ValueError, match="unknown column"):
        _update_assignments({"evil_column": 1}, PROJECT_UPDATE_COLUMNS)


def test_update_assignments_rejects_sql_injection_shaped_column_name():
    # An injection-shaped key must raise, never be interpolated into the SET clause.
    with pytest.raises(ValueError, match="unknown column"):
        _update_assignments({"title = 'x' --": "boom"}, PROJECT_UPDATE_COLUMNS)


def test_update_assignments_rejects_unknown_column_for_recipes():
    with pytest.raises(ValueError, match="unknown column"):
        _update_assignments({"owner_id": "attacker"}, RECIPE_UPDATE_COLUMNS)


# ─── end-to-end via the store ───────────────────────────────────────────────────

def test_update_still_works_for_known_columns(tmp_path):
    store = ProjectStore(tmp_path)
    project = store.create(
        "owner-1",
        ProjectCreate(
            title="Weekly update",
            body="A durable source item.",
            target_formats=["linkedin_post", "twitter_thread"],
        ),
    )
    updated = store.update(
        "owner-1", project.id, ProjectUpdate(title="Edited", status="ready")
    )
    assert updated.title == "Edited"
    assert updated.status == "ready"


def test_update_recipe_still_works_for_known_columns(tmp_path):
    store = ProjectStore(tmp_path)
    recipe = store.create_recipe(
        "owner-1",
        RecipeCreate(name="Weekly digest", target_formats=["linkedin_post"]),
    )
    assert recipe.name == "Weekly digest"
