"""Tests for content repurposing service."""

import pytest

from app.models.content import (
    BrandVoice,
    ContentFormat,
    ContentItem,
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
        assert callable(getattr(RepurposeService, "repurpose"))

    def test_has_estimate_tokens(self):
        assert hasattr(RepurposeService, "estimate_tokens")
        assert callable(getattr(RepurposeService, "estimate_tokens"))

    def test_has_chunk_content(self):
        assert hasattr(RepurposeService, "chunk_content")
        assert callable(getattr(RepurposeService, "chunk_content"))

    def test_has_get_supported_formats(self):
        assert hasattr(RepurposeService, "get_supported_formats")
        assert callable(getattr(RepurposeService, "get_supported_formats"))

    def test_has_analyze_content(self):
        assert hasattr(RepurposeService, "analyze_content")
        assert callable(getattr(RepurposeService, "analyze_content"))

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
