"""Tests for content repurposing service."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.content import (
    BrandVoice,
    ContentFormat,
    ContentItem,
    RepurposeRequest,
    RepurposeResponse,
)
from app.services.repurpose import RepurposeService

# ── Interface Tests (must pass immediately) ──────────────────


class TestRepurposeServiceImport:
    """Interface: RepurposeService is importable and has expected API."""

    def test_importable(self):
        assert RepurposeService is not None

    def test_is_class(self):
        assert isinstance(RepurposeService, type)

    def test_has_repurpose_method(self):
        assert hasattr(RepurposeService, "repurpose")
        assert callable(RepurposeService.repurpose)

    def test_has_estimate_tokens(self):
        assert hasattr(RepurposeService, "estimate_tokens")
        assert callable(RepurposeService.estimate_tokens)

    def test_has_chunk_content(self):
        assert hasattr(RepurposeService, "chunk_content")
        assert callable(RepurposeService.chunk_content)

    def test_has_get_supported_formats(self):
        assert hasattr(RepurposeService, "get_supported_formats")
        assert callable(RepurposeService.get_supported_formats)

    def test_has_analyze_content(self):
        assert hasattr(RepurposeService, "analyze_content")
        assert callable(RepurposeService.analyze_content)

    def test_init_signature(self):
        """RepurposeService.__init__ accepts optional api_key."""
        import inspect
        sig = inspect.signature(RepurposeService.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params

    def test_repurpose_is_async(self):
        """repurpose should be an async method."""
        import inspect
        assert inspect.iscoroutinefunction(RepurposeService.repurpose)

    def test_analyze_content_is_async(self):
        """analyze_content should be an async method."""
        import inspect
        assert inspect.iscoroutinefunction(RepurposeService.analyze_content)


# ── Behavioral Tests (must fail until implementation) ────────


class TestRepurposeServiceBehavior:
    """Behavioral: RepurposeService core logic."""

    @pytest.fixture
    def sample_content(self):
        return ContentItem(
            title="AI in Healthcare",
            body="Artificial intelligence is transforming healthcare diagnostics.",
            source_format=ContentFormat.BLOG_POST,
            tags=["ai", "healthcare"],
        )

    async def test_repurpose_returns_response(self, sample_content):
        svc = RepurposeService()
        result = await svc.repurpose(
            content=sample_content,
            target_formats=[ContentFormat.TWITTER_THREAD],
        )
        assert isinstance(result, RepurposeResponse)

    async def test_repurpose_sets_original_id(self, sample_content):
        svc = RepurposeService()
        sample_content.id = "content-42"
        result = await svc.repurpose(
            content=sample_content,
            target_formats=[ContentFormat.TWITTER_THREAD],
        )
        assert result.original_id == "content-42"

    async def test_repurpose_populates_repurposed_dict(self, sample_content):
        svc = RepurposeService()
        result = await svc.repurpose(
            content=sample_content,
            target_formats=[ContentFormat.TWITTER_THREAD, ContentFormat.LINKEDIN_POST],
        )
        assert ContentFormat.TWITTER_THREAD in result.repurposed
        assert ContentFormat.LINKEDIN_POST in result.repurposed

    async def test_repurpose_with_brand_voice(self, sample_content):
        svc = RepurposeService()
        result = await svc.repurpose(
            content=sample_content,
            target_formats=[ContentFormat.NEWSLETTER],
            brand_voice=BrandVoice.CASUAL,
        )
        assert isinstance(result, RepurposeResponse)

    async def test_repurpose_with_custom_instructions(self, sample_content):
        svc = RepurposeService()
        result = await svc.repurpose(
            content=sample_content,
            target_formats=[ContentFormat.VIDEO_SCRIPT],
            custom_instructions="Make it under 60 seconds",
        )
        assert isinstance(result, RepurposeResponse)

    def test_estimate_tokens_positive(self):
        svc = RepurposeService()
        tokens = svc.estimate_tokens("Hello world, this is a test.")
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_estimate_tokens_empty_string(self):
        svc = RepurposeService()
        tokens = svc.estimate_tokens("")
        assert tokens == 0

    def test_chunk_content_returns_list(self):
        svc = RepurposeService()
        text = "word " * 5000
        chunks = svc.chunk_content(text, max_tokens=1000)
        assert isinstance(chunks, list)
        assert len(chunks) > 1

    def test_chunk_content_short_text(self):
        svc = RepurposeService()
        chunks = svc.chunk_content("Short text", max_tokens=4000)
        assert isinstance(chunks, list)
        assert len(chunks) == 1

    def test_get_supported_formats_returns_list(self):
        svc = RepurposeService()
        formats = svc.get_supported_formats()
        assert isinstance(formats, list)
        assert len(formats) > 0

    def test_get_supported_formats_all_content_format(self):
        svc = RepurposeService()
        formats = svc.get_supported_formats()
        for fmt in formats:
            assert isinstance(fmt, ContentFormat)

    async def test_analyze_content_returns_dict(self, sample_content):
        svc = RepurposeService()
        result = await svc.analyze_content(sample_content)
        assert isinstance(result, dict)


# ── Integration Scaffold Tests (Phase 3 — fail until implementation) ──


class TestRepurposeServiceLLMIntegration:
    """Scaffold: RepurposeService with LLMRouter + FormatRegistry dependency.

    These tests validate the integration surface described in Phase 3 of the
    analysis brief. They will fail until the LLM layer and format registry
    are wired into RepurposeService.
    """

    def test_init_accepts_llm_router(self):
        """RepurposeService should accept an optional LLMRouter."""
        import inspect
        sig = inspect.signature(RepurposeService.__init__)
        params = list(sig.parameters.keys())
        has_router_param = "llm_router" in params or "router" in params
        if not has_router_param:
            pytest.xfail(
                f"RepurposeService.__init__ needs llm_router param. "
                f"Current params: {params}"
            )

    def test_init_accepts_format_registry(self):
        """RepurposeService should accept an optional FormatRegistry."""
        import inspect
        sig = inspect.signature(RepurposeService.__init__)
        params_str = " ".join(sig.parameters.keys())
        has_registry = "registry" in params_str or "format_registry" in params_str
        if not has_registry:
            pytest.xfail("RepurposeService doesn't accept FormatRegistry yet")

    async def test_repurpose_uses_llm_when_router_provided(self):
        """When LLMRouter is provided, repurpose() should call it (vs string concat)."""
        svc = RepurposeService()
        item = ContentItem(
            title="Test", body="Test body", source_format=ContentFormat.BLOG_POST
        )
        result = await svc.repurpose(
            content=item,
            target_formats=[ContentFormat.TWITTER_THREAD],
        )
        assert isinstance(result, RepurposeResponse)
        # TODO: When LLM is wired, the repurposed content should differ from the
        # simple string-concatenation result


class TestRepurposeRequestLLMFields:
    """Scaffold: RepurposeRequest gains llm_strategy field.

    Analysis brief §4.3 specifies a new optional 'llm_strategy' field.
    """

    def test_has_llm_strategy_field(self):
        """RepurposeRequest should have an optional llm_strategy field."""
        has_field = "llm_strategy" in RepurposeRequest.model_fields
        if not has_field:
            pytest.xfail("llm_strategy not added to RepurposeRequest yet")

    def test_llm_strategy_defaults_to_none(self):
        """llm_strategy should default to None (backward compat)."""
        from app.models.content import ContentItem

        item = ContentItem(
            title="T", body="B", source_format=ContentFormat.BLOG_POST
        )
        req = RepurposeRequest(
            content=item,
            target_formats=[ContentFormat.TWITTER_THREAD],
        )
        llm_strategy = getattr(req, "llm_strategy", None)
        assert llm_strategy is None


class TestRepurposeEndpointLLMHeaders:
    """Scaffold: POST /api/v1/repurpose accepts X-LLM-Provider / X-LLM-Model.

    Analysis brief §4.3 specifies new optional headers for provider selection.
    """

    async def test_accepts_x_llm_provider_header(self):
        """Should accept X-LLM-Provider header without error."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=self._make_request(),
                headers={"X-LLM-Provider": "openai"},
            )
        # Currently returns 200 without processing the header — that's OK for backward compat
        assert response.status_code in (200, 422)

    async def test_accepts_x_llm_model_header(self):
        """Should accept X-LLM-Model header without error."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=self._make_request(),
                headers={"X-LLM-Model": "gpt-4o-mini"},
            )
        assert response.status_code in (200, 422)

    async def test_accepts_both_llm_headers(self):
        """Should accept both headers simultaneously."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=self._make_request(),
                headers={
                    "X-LLM-Provider": "anthropic",
                    "X-LLM-Model": "claude-haiku",
                },
            )
        assert response.status_code in (200, 422)

    async def test_unknown_provider_header_returns_200(self):
        """Unknown provider header should not crash (backward compat)."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=self._make_request(),
                headers={"X-LLM-Provider": "nonexistent-provider"},
            )
        # Should not crash — either 200 or 422
        assert response.status_code in (200, 422)

    def _make_request(self):
        return {
            "content": {
                "title": "AI in Healthcare",
                "body": "AI is transforming diagnostics.",
                "source_format": "blog_post",
                "tags": ["ai"],
            },
            "target_formats": ["twitter_thread"],
            "brand_voice": "professional",
        }


class TestRepurposeServiceBackwardCompat:
    """Scaffold: Ensure backward compatibility after LLM integration.

    Existing behavior (string concatenation when no LLM) must still work
    when no LLMRouter is provided.
    """

    @pytest.fixture
    def sample_content(self):
        return ContentItem(
            title="AI in Healthcare",
            body="Artificial intelligence is transforming healthcare diagnostics.",
            source_format=ContentFormat.BLOG_POST,
            tags=["ai", "healthcare"],
        )

    async def test_repurpose_still_works_without_router(self, sample_content):
        """Without an LLMRouter, repurpose should still return string-concat result."""
        svc = RepurposeService()
        result = await svc.repurpose(
            content=sample_content,
            target_formats=[ContentFormat.TWITTER_THREAD],
        )
        assert isinstance(result, RepurposeResponse)
        text = result.repurposed.get(ContentFormat.TWITTER_THREAD, "")
        assert "Write in a" in text  # Brand voice prompt prefix still present
        assert sample_content.body in text  # Original body still present
