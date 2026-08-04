"""Pre-dev tests for multi-language content repurposing.

Source of truth: analyst task t_758a9a4e (multi-language content repurposing —
per-language output, validation & UI selector).

Interface tests  → MUST PASS immediately (schema field added, stubs exist).
Behavioral tests → MUST FAIL with NotImplementedError until implementation.

Contracts under test:
- ``RepurposeRequest.target_languages: list[str]`` defaults to ``[]`` (legacy
  single-language behavior preserved when empty).
- ``validate_languages`` rejects unsupported ISO 639-1 codes (422 + error
  listing supported languages); empty list and all 14 supported codes allowed.
- ``POST /api/v1/repurpose`` and ``POST /api/v1/repurpose/batch`` return
  ``{format: {lang_code: content}}`` per-language shape when
  ``target_languages`` is set; legacy single-language shape when empty.
- ``GET /api/v1/languages`` returns the supported-language registry with
  ``id``, ``name`` and ``native_name`` per entry.
- Token estimation accounts for each target language.
"""

from __future__ import annotations

import inspect

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.languages import router as languages_router
from app.main import app
from app.models.content import RepurposeRequest
from app.services.languages import (
    SUPPORTED_LANGUAGES,
    build_per_language_output,
    estimate_multilang_tokens,
    validate_languages,
)

# The 14 supported ISO 639-1 codes from the analyst spec.
SUPPORTED_CODES = [
    "es", "de", "fr", "pt", "it", "nl",
    "ja", "ko", "zh", "hi", "ar", "ru", "pl", "tr",
]

SAMPLE_CONTENT = {
    "title": "AI in Healthcare",
    "body": "Artificial intelligence is transforming healthcare diagnostics.",
    "source_format": "blog_post",
    "tags": ["ai", "healthcare"],
}


def _make_request_body(**overrides) -> dict:
    """Build a valid repurpose request body, applying overrides."""
    body: dict = {
        "content": SAMPLE_CONTENT,
        "target_formats": ["twitter_thread"],
        "brand_voice": "professional",
    }
    body.update(overrides)
    return body


def _make_batch_job(**overrides) -> dict:
    """Build a valid batch job dict, applying overrides."""
    job: dict = {
        "content": SAMPLE_CONTENT,
        "target_formats": ["twitter_thread"],
    }
    job.update(overrides)
    return job


# ════════════════════════════════════════════════════════════════════════════════
# INTERFACE TESTS — must pass immediately
# ════════════════════════════════════════════════════════════════════════════════


class TestRepurposeRequestTargetLanguages:
    """Interface: RepurposeRequest gains optional target_languages field."""

    def test_target_languages_field_exists(self):
        assert "target_languages" in RepurposeRequest.model_fields

    def test_target_languages_is_list_of_str(self):
        field = RepurposeRequest.model_fields["target_languages"]
        ann = str(field.annotation).lower()
        assert "list" in ann
        assert "str" in ann

    def test_target_languages_is_optional(self):
        """Field may be omitted — defaults to empty list (no breaking change)."""
        field = RepurposeRequest.model_fields["target_languages"]
        assert field.default == [] or field.default_factory is list

    def test_construct_without_target_languages_defaults_empty(self):
        req = RepurposeRequest(
            content=SAMPLE_CONTENT,
            target_formats=["twitter_thread"],
        )
        assert req.target_languages == []

    def test_construct_with_explicit_empty_list(self):
        req = RepurposeRequest(
            content=SAMPLE_CONTENT,
            target_formats=["twitter_thread"],
            target_languages=[],
        )
        assert req.target_languages == []

    def test_construct_with_language_codes(self):
        req = RepurposeRequest(
            content=SAMPLE_CONTENT,
            target_formats=["twitter_thread"],
            target_languages=["es", "de"],
        )
        assert req.target_languages == ["es", "de"]

    def test_construct_with_all_supported_codes(self):
        req = RepurposeRequest(
            content=SAMPLE_CONTENT,
            target_formats=["twitter_thread"],
            target_languages=SUPPORTED_CODES,
        )
        assert req.target_languages == SUPPORTED_CODES


class TestLanguagesRouterInterface:
    """Interface: languages router exists with a GET /languages route."""

    def test_router_importable(self):
        assert languages_router is not None

    def test_has_get_languages_route(self):
        routes = [r for r in languages_router.routes if hasattr(r, "methods")]
        get_routes = [r for r in routes if "GET" in r.methods]
        assert len(get_routes) >= 1
        assert any("languages" in getattr(r, "path", "") for r in get_routes)

    def test_router_has_v1_prefix(self):
        assert hasattr(languages_router, "prefix")
        assert "v1" in languages_router.prefix

    def test_app_registers_languages_route(self):
        """Route wired into the FastAPI app (openapi paths)."""
        paths = app.openapi().get("paths", {})
        assert "/api/v1/languages" in paths

    def test_languages_route_is_get_only(self):
        schema = app.openapi().get("paths", {}).get("/api/v1/languages", {})
        assert "get" in schema


class TestLanguagesHelpersInterface:
    """Interface: language helpers importable with expected signatures."""

    def test_validate_languages_importable(self):
        assert callable(validate_languages)

    def test_validate_languages_signature(self):
        sig = inspect.signature(validate_languages)
        assert list(sig.parameters) == ["target_languages"]
        assert str(sig.parameters["target_languages"].annotation) == "list[str]"
        ret = sig.return_annotation
        assert ret is None or str(ret) == "None"

    def test_build_per_language_output_importable(self):
        assert callable(build_per_language_output)

    def test_build_per_language_output_signature(self):
        sig = inspect.signature(build_per_language_output)
        assert list(sig.parameters) == ["repurposed", "target_languages"]
        assert str(sig.parameters["repurposed"].annotation) == "dict[str, str]"
        assert str(sig.parameters["target_languages"].annotation) == "list[str]"
        ret = str(sig.return_annotation)
        assert "dict" in ret and "str" in ret

    def test_estimate_multilang_tokens_importable(self):
        assert callable(estimate_multilang_tokens)

    def test_estimate_multilang_tokens_signature(self):
        sig = inspect.signature(estimate_multilang_tokens)
        assert list(sig.parameters) == ["text", "target_languages"]
        assert str(sig.parameters["text"].annotation) == "str"
        assert str(sig.parameters["target_languages"].annotation) == "list[str]"
        ret = sig.return_annotation
        assert ret is int or str(ret) == "int"


class TestSupportedLanguagesRegistry:
    """Interface: SUPPORTED_LANGUAGES registry matches the spec."""

    def test_registry_is_dict(self):
        assert isinstance(SUPPORTED_LANGUAGES, dict)

    def test_registry_has_14_languages(self):
        assert len(SUPPORTED_LANGUAGES) == 14

    def test_registry_codes_match_spec(self):
        assert set(SUPPORTED_LANGUAGES) == set(SUPPORTED_CODES)

    def test_each_entry_has_id_name_native_name(self):
        for code, entry in SUPPORTED_LANGUAGES.items():
            assert isinstance(entry, dict), code
            assert "id" in entry, code
            assert "name" in entry, code
            assert "native_name" in entry, code

    def test_entry_id_matches_key(self):
        for code, entry in SUPPORTED_LANGUAGES.items():
            assert entry["id"] == code

    def test_entry_values_are_non_empty_strings(self):
        for code, entry in SUPPORTED_LANGUAGES.items():
            for key in ("id", "name", "native_name"):
                assert isinstance(entry[key], str), f"{code}.{key}"
                assert entry[key].strip(), f"{code}.{key}"


# ════════════════════════════════════════════════════════════════════════════════
# BEHAVIORAL TESTS — must fail with NotImplementedError until implementation
# ════════════════════════════════════════════════════════════════════════════════


class TestLanguageValidationBehavior:
    """Behavioral: language validation rules via POST /api/v1/repurpose."""

    @pytest.mark.parametrize(
        "target_languages, expected_status",
        [
            ([], 200),                    # empty list = allowed (legacy)
            (SUPPORTED_CODES, 200),       # all 14 supported codes = allowed
            (["xx"], 422),                # unsupported code = rejected
            (["es", "xx"], 422),          # mixed supported/unsupported = rejected
        ],
        ids=[
            "empty_allowed",
            "all_supported_allowed",
            "unsupported_rejected",
            "mixed_rejected",
        ],
    )
    async def test_validation_rule(self, target_languages, expected_status):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=_make_request_body(target_languages=target_languages),
            )
        assert response.status_code == expected_status

    async def test_rejected_error_lists_supported_languages(self):
        """422 error body must mention supported language codes."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=_make_request_body(target_languages=["zz"]),
            )
        assert response.status_code == 422
        text = response.text.lower()
        assert "es" in text and "de" in text

    def test_validate_supported_languages_returns_none(self):
        """Helper accepts all supported codes (no exception)."""
        assert validate_languages(["es", "de"]) is None

    def test_validate_empty_list_returns_none(self):
        """Helper accepts an empty language list."""
        assert validate_languages([]) is None

    def test_validate_unsupported_raises_value_error(self):
        """Helper rejects an unsupported code with a ValueError."""
        with pytest.raises(ValueError):
            validate_languages(["xx"])

    def test_validate_mixed_raises_value_error(self):
        """Helper rejects a mixed supported/unsupported list."""
        with pytest.raises(ValueError):
            validate_languages(["es", "xx"])

    def test_validate_error_message_lists_supported_languages(self):
        """Helper error message lists supported language codes."""
        with pytest.raises(ValueError) as excinfo:
            validate_languages(["zz"])
        message = str(excinfo.value).lower()
        assert "es" in message and "de" in message


class TestPerLanguageOutputBehavior:
    """Behavioral: POST /api/v1/repurpose returns per-language output shape."""

    async def test_multilang_request_returns_per_language_shape(self):
        """{format: {lang: content}} when target_languages is set."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=_make_request_body(target_languages=["es", "de"]),
            )
        assert response.status_code == 200
        data = response.json()
        repurposed = data["repurposed"]
        assert isinstance(repurposed["twitter_thread"], dict)
        assert "es" in repurposed["twitter_thread"]
        assert "de" in repurposed["twitter_thread"]

    async def test_multilang_request_per_language_content_is_string(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=_make_request_body(target_languages=["es", "de"]),
            )
        data = response.json()
        content_es = data["repurposed"]["twitter_thread"]["es"]
        assert isinstance(content_es, str)
        assert content_es.strip()

    async def test_multilang_request_multiple_formats(self):
        """Every requested format gets per-language content."""
        body = _make_request_body(target_languages=["es", "de"])
        body["target_formats"] = ["twitter_thread", "linkedin_post"]
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/repurpose", json=body)
        assert response.status_code == 200
        repurposed = response.json()["repurposed"]
        assert isinstance(repurposed["twitter_thread"], dict)
        assert isinstance(repurposed["linkedin_post"], dict)
        assert "es" in repurposed["linkedin_post"]

    async def test_empty_target_languages_returns_legacy_shape(self):
        """Empty target_languages → legacy single-language {format: str}."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=_make_request_body(target_languages=[]),
            )
        assert response.status_code == 200
        repurposed = response.json()["repurposed"]
        assert isinstance(repurposed["twitter_thread"], str)

    async def test_missing_target_languages_returns_legacy_shape(self):
        """Field absent entirely → legacy single-language shape."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=_make_request_body(),
            )
        assert response.status_code == 200
        repurposed = response.json()["repurposed"]
        assert isinstance(repurposed["twitter_thread"], str)


class TestBatchPerLanguageOutputBehavior:
    """Behavioral: POST /api/v1/repurpose/batch per-language output shape."""

    async def test_batch_multilang_returns_per_language_shape(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose/batch",
                json={
                    "jobs": [_make_batch_job(target_languages=["es", "de"])],
                    "concurrency": 1,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] == 1
        repurposed = data["results"][0]["repurposed"]
        assert isinstance(repurposed["twitter_thread"], dict)
        assert "es" in repurposed["twitter_thread"]
        assert "de" in repurposed["twitter_thread"]

    async def test_batch_empty_target_languages_returns_legacy_shape(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose/batch",
                json={
                    "jobs": [_make_batch_job(target_languages=[])],
                    "concurrency": 1,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] == 1
        repurposed = data["results"][0]["repurposed"]
        assert isinstance(repurposed["twitter_thread"], str)

    async def test_batch_unsupported_language_marks_job_failed(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose/batch",
                json={
                    "jobs": [_make_batch_job(target_languages=["xx"])],
                    "concurrency": 1,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["failed"] == 1
        assert data["errors"], "expected an error entry for the invalid job"


class TestLanguagesEndpointBehavior:
    """Behavioral: GET /api/v1/languages returns the supported registry."""

    async def test_get_languages_returns_200(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/languages")
        assert response.status_code == 200

    async def test_get_languages_returns_list(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/languages")
        data = response.json()
        assert isinstance(data, list)

    async def test_get_languages_has_14_entries(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/languages")
        data = response.json()
        assert len(data) == 14

    async def test_get_languages_entries_have_required_fields(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/languages")
        for entry in response.json():
            assert "id" in entry
            assert "name" in entry
            assert "native_name" in entry

    async def test_get_languages_contains_all_supported_codes(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/languages")
        ids = {entry["id"] for entry in response.json()}
        assert set(SUPPORTED_CODES) <= ids

    async def test_get_languages_entries_have_non_empty_names(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/languages")
        for entry in response.json():
            assert entry["name"].strip()
            assert entry["native_name"].strip()


class TestTokenEstimationBehavior:
    """Behavioral: token estimation accounts for each target language."""

    def test_estimate_multilang_returns_int(self):
        result = estimate_multilang_tokens("Hello world", ["es", "de"])
        assert isinstance(result, int)

    def test_estimate_multilang_grows_with_language_count(self):
        single = estimate_multilang_tokens("Hello world", ["es"])
        multi = estimate_multilang_tokens("Hello world", ["es", "de", "fr"])
        assert multi > single

    def test_estimate_multilang_monotonic_in_languages(self):
        base = estimate_multilang_tokens("Hello world", [])
        two = estimate_multilang_tokens("Hello world", ["es", "de"])
        assert two >= base

    def test_estimate_multilang_empty_returns_base_estimate(self):
        """Empty language list must not shrink the legacy estimate."""
        result = estimate_multilang_tokens("Hello world", [])
        assert result >= 1


class TestBuildPerLanguageOutputBehavior:
    """Behavioral: per-language output expansion helper."""

    def test_build_per_language_output_shape(self):
        legacy = {"twitter_thread": "Hello"}
        result = build_per_language_output(legacy, ["es", "de"])
        assert isinstance(result["twitter_thread"], dict)
        assert "es" in result["twitter_thread"]
        assert "de" in result["twitter_thread"]

    def test_build_per_language_output_preserves_content_per_lang(self):
        legacy = {"twitter_thread": "Hello"}
        result = build_per_language_output(legacy, ["es"])
        assert isinstance(result["twitter_thread"]["es"], str)
        assert result["twitter_thread"]["es"].strip()

    def test_build_per_language_output_empty_languages_passthrough(self):
        legacy = {"twitter_thread": "Hello"}
        result = build_per_language_output(legacy, [])
        assert result == legacy
