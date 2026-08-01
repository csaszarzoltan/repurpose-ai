"""Acceptance tests for the user-facing content workspace (TDD specification)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from app.main import create_app

if TYPE_CHECKING:
    from pathlib import Path


def _client(tmp_path: Path, monkeypatch) -> TestClient:
    monkeypatch.setenv("REPURPOSEAI_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ENVIRONMENT", "test")
    return TestClient(create_app())


def test_workspace_is_accessible_and_semantic(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert '<main id="main-content"' in html
    assert 'aria-label="Primary navigation"' in html
    assert 'aria-live="polite"' in html
    assert 'Create content' in html
    assert 'Skip to content' in html


def test_create_list_update_and_archive_project(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    created = client.post(
        "/api/v1/projects",
        json={
            "title": "Weekly product update",
            "body": "A durable source item that can be resumed later.",
            "source_format": "blog_post",
            "target_formats": ["linkedin_post", "twitter_thread"],
            "brand_voice": "professional",
        },
    )
    assert created.status_code == 201, created.text
    project = created.json()
    assert project["status"] == "draft"
    assert project["target_formats"] == ["linkedin_post", "twitter_thread"]

    listed = client.get("/api/v1/projects").json()
    assert [item["id"] for item in listed] == [project["id"]]

    updated = client.patch(
        f'/api/v1/projects/{project["id"]}',
        json={"title": "Edited weekly update", "status": "ready"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Edited weekly update"
    assert updated.json()["status"] == "ready"

    archived = client.delete(f'/api/v1/projects/{project["id"]}')
    assert archived.status_code == 204
    assert client.get("/api/v1/projects").json() == []
    assert len(client.get("/api/v1/projects?include_archived=true").json()) == 1


def test_project_validation_preserves_clear_field_errors(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    response = client.post(
        "/api/v1/projects",
        json={"title": "", "body": "", "source_format": "blog_post", "target_formats": []},
    )
    assert response.status_code == 422
    fields = {tuple(item["loc"])[-1] for item in response.json()["detail"]}
    assert {"title", "body", "target_formats"}.issubset(fields)


def test_privacy_safe_telemetry_accepts_known_event_and_rejects_content(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    accepted = client.post(
        "/api/v1/telemetry/events",
        json={"event_name": "project_created", "properties": {"format_count": 2}},
    )
    assert accepted.status_code == 202

    rejected = client.post(
        "/api/v1/telemetry/events",
        json={"event_name": "project_created", "properties": {"content": "private draft"}},
    )
    assert rejected.status_code == 422


def test_health_exposes_capabilities_without_claiming_stubs(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    data = client.get("/health").json()
    assert data["status"] == "ok"
    assert data["capabilities"]["content_workspace"] == "available"
    assert data["capabilities"]["pdf_export"] == "scaffold"


def test_production_workspace_requires_authentication(tmp_path, monkeypatch):
    monkeypatch.setenv("REPURPOSEAI_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ENVIRONMENT", "production")
    client = TestClient(create_app())
    response = client.get("/api/v1/projects")
    assert response.status_code == 401
