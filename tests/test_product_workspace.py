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


def test_llm_factory_registers_only_configured_providers(monkeypatch):
    from app.services.generation_factory import build_generation_service

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    service, mode = build_generation_service()
    assert mode == "template_fallback"
    assert service.llm_router is None

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    service, mode = build_generation_service()
    assert mode == "llm"
    assert list(service.llm_router.providers) == ["openai"]
    assert len(service.format_registry.list_all()) == 20


def test_generation_endpoint_uses_injected_llm_service(tmp_path, monkeypatch):
    from app.api import projects as projects_api
    from app.models.content import RepurposeResponse

    class FakeGenerationService:
        llm_router = object()
        format_registry = object()

        async def repurpose(self, content, target_formats, **kwargs):
            return RepurposeResponse(
                original_id=content.id or "",
                repurposed={item: f"LLM result for {item.value}" for item in target_formats},
            )

    monkeypatch.setattr(
        projects_api,
        "build_generation_service",
        lambda user=None: (FakeGenerationService(), "llm"),
    )
    client = _client(tmp_path, monkeypatch)
    project = _create_project(client)
    response = client.post(f'/api/v1/projects/{project["id"]}/generate')
    assert response.status_code == 201
    data = response.json()
    assert data["generation_mode"] == "llm"
    assert data["warning"] is None
    assert all(item["generation_mode"] == "llm" for item in data["variants"])


def test_generation_reports_llm_failure_fallback_honestly(tmp_path, monkeypatch):
    from app.api import projects as projects_api
    from app.models.content import RepurposeResponse

    class FailingProviderService:
        async def repurpose(self, content, target_formats, **kwargs):
            return RepurposeResponse(
                original_id=content.id or "",
                repurposed={item: content.body for item in target_formats},
                warnings=["LLM generation failed for 'linkedin_post': provider unavailable"],
            )

    monkeypatch.setattr(
        projects_api,
        "build_generation_service",
        lambda user=None: (FailingProviderService(), "llm"),
    )
    client = _client(tmp_path, monkeypatch)
    project = _create_project(client)
    data = client.post(f'/api/v1/projects/{project["id"]}/generate').json()
    assert data["generation_mode"] == "llm_fallback"
    assert "provider unavailable" in data["warning"]
    assert all(item["generation_mode"] == "llm_fallback" for item in data["variants"])



def _recipe_payload() -> dict:
    return {
        "name": "Weekly social pack",
        "target_formats": ["linkedin_post", "twitter_thread"],
        "brand_voice": "friendly",
        "custom_instructions": "Lead with the most useful customer outcome.",
    }


def test_recipe_crud_is_persistent_and_owner_scoped(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    created = client.post("/api/v1/recipes", json=_recipe_payload())
    assert created.status_code == 201, created.text
    recipe = created.json()
    assert recipe["name"] == "Weekly social pack"
    assert recipe["target_formats"] == ["linkedin_post", "twitter_thread"]

    listed = client.get("/api/v1/recipes").json()
    assert [item["id"] for item in listed] == [recipe["id"]]

    changed = client.patch(
        f'/api/v1/recipes/{recipe["id"]}',
        json={"name": "Updated social pack", "brand_voice": "professional"},
    )
    assert changed.status_code == 200
    assert changed.json()["name"] == "Updated social pack"
    assert changed.json()["brand_voice"] == "professional"

    other = client.get("/api/v1/recipes", headers={"X-Workspace-ID": "other-workspace"})
    assert other.json() == []

    deleted = client.delete(f'/api/v1/recipes/{recipe["id"]}')
    assert deleted.status_code == 204
    assert client.get("/api/v1/recipes").json() == []


def test_create_project_from_recipe_reuses_daily_defaults(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    recipe = client.post("/api/v1/recipes", json=_recipe_payload()).json()
    response = client.post(
        f'/api/v1/recipes/{recipe["id"]}/projects',
        json={"title": "August release", "body": "The release reduces setup time."},
    )
    assert response.status_code == 201, response.text
    project = response.json()
    assert project["title"] == "August release"
    assert project["target_formats"] == recipe["target_formats"]
    assert project["brand_voice"] == recipe["brand_voice"]
    assert project["custom_instructions"] == recipe["custom_instructions"]


def test_recipe_validation_rejects_blank_name_and_duplicate_formats(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    payload = _recipe_payload()
    payload["name"] = "  "
    payload["target_formats"] = ["linkedin_post", "linkedin_post"]
    response = client.post("/api/v1/recipes", json=payload)
    assert response.status_code == 422


def test_workspace_exposes_saved_recipe_controls(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    html = client.get("/").text
    assert "Saved recipes" in html
    assert 'id="recipe-select"' in html
    assert "Save as recipe" in html


def test_workspace_summary_prioritizes_daily_attention(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    project = _create_project(client)
    summary = client.get('/api/v1/workspace/summary')
    assert summary.status_code == 200
    assert summary.json() == {
        'active_projects': 1,
        'projects_without_drafts': 1,
        'draft_variants': 0,
        'approved_variants': 0,
        'fallback_variants_needing_review': 0,
    }

    generated = client.post(f'/api/v1/projects/{project["id"]}/generate').json()
    variant = generated['variants'][0]
    summary = client.get('/api/v1/workspace/summary').json()
    assert summary['projects_without_drafts'] == 0
    assert summary['draft_variants'] == 2
    assert summary['fallback_variants_needing_review'] == 2

    client.patch(
        f'/api/v1/projects/{project["id"]}/variants/{variant["id"]}',
        json={'content': 'Reviewed copy.', 'status': 'approved'},
    )
    summary = client.get('/api/v1/workspace/summary').json()
    assert summary['draft_variants'] == 1
    assert summary['approved_variants'] == 1
    assert summary['fallback_variants_needing_review'] == 1


def test_workspace_ui_exposes_search_attention_autosave_and_history(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    html = client.get('/').text
    script = client.get('/assets/app.js').text
    assert 'id="workspace-summary"' in html
    assert 'id="project-search"' in html
    assert 'id="draft-state"' in html
    assert 'View history' in script
    assert 'localStorage' in script
    assert '/api/v1/workspace/summary' in script
    assert 'aria-label="Search saved projects"' in html
