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


def _create_project(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/projects",
        json={
            "title": "Generate me",
            "body": "A release note with clear user value.",
            "source_format": "blog_post",
            "target_formats": ["linkedin_post", "twitter_thread"],
            "brand_voice": "friendly",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_generate_project_persists_format_variants_and_versions(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = _create_project(client)

    generated = client.post(f'/api/v1/projects/{project["id"]}/generate')
    assert generated.status_code == 201, generated.text
    result = generated.json()
    assert result["generation_mode"] == "template_fallback"
    assert result["warning"]
    assert {item["format"] for item in result["variants"]} == {"linkedin_post", "twitter_thread"}
    assert all(item["version"] == 1 for item in result["variants"])

    second = client.post(f'/api/v1/projects/{project["id"]}/generate').json()
    assert all(item["version"] == 2 for item in second["variants"])

    latest = client.get(f'/api/v1/projects/{project["id"]}/variants').json()
    assert len(latest) == 2
    assert all(item["version"] == 2 for item in latest)

    history = client.get(f'/api/v1/projects/{project["id"]}/variants?include_history=true').json()
    assert len(history) == 4


def test_update_variant_creates_new_version_without_overwriting_prior_work(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = _create_project(client)
    variant = client.post(f'/api/v1/projects/{project["id"]}/generate').json()["variants"][0]

    changed = client.patch(
        f'/api/v1/projects/{project["id"]}/variants/{variant["id"]}',
        json={"content": "A manually reviewed and approved draft.", "status": "approved"},
    )
    assert changed.status_code == 200
    assert changed.json()["version"] == 2
    assert changed.json()["status"] == "approved"

    history = client.get(
        f'/api/v1/projects/{project["id"]}/variants?include_history=true'
    ).json()
    same_format = [item for item in history if item["format"] == variant["format"]]
    assert [item["version"] for item in same_format] == [2, 1]
    assert same_format[1]["content"] != same_format[0]["content"]


def test_workspace_exposes_generation_and_variant_feedback(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    html = client.get("/").text
    assert "Generate drafts" in html
    assert 'id="variants"' in html
    assert "Generated drafts use template fallback" in html
