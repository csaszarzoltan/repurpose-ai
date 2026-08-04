"""Regression tests for tech-lead review findings on multi-language repurposing.

Review task t_51987893 comment #1130 → fix task t_06c42d65:

- F1: the chunk decision must use the SINGLE-call context estimate (one
  language instruction per call), not the full-language-list estimate —
  large content + many languages must NOT chunk when each per-call prompt
  fits the window.
- F2: validate_languages rejects duplicate and over-long lists (OWASP LLM10
  unbounded consumption), enforced at both API boundaries AND inside
  RepurposeService.repurpose().
- F3: per-language LLM calls run in parallel with bounded concurrency and
  per-language error isolation.
"""

from __future__ import annotations

import asyncio
import re

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.content import ContentFormat, ContentItem
from app.services.formats.registry import FormatRegistry, FormatTemplate
from app.services.languages import SUPPORTED_LANGUAGES, validate_languages
from app.services.llm.base import LLMResponse
from app.services.llm.router import RouterStrategy
from app.services.repurpose import RepurposeService

SUPPORTED_CODES = list(SUPPORTED_LANGUAGES)
SAMPLE_CONTENT = {
    "title": "AI in Healthcare",
    "body": "Artificial intelligence is transforming healthcare diagnostics.",
    "source_format": "blog_post",
    "tags": ["ai", "healthcare"],
}

# Matches the language instruction emitted by
# RepurposeService._language_instruction, e.g. "... in Spanish (es)."
_LANG_MARKER = re.compile(r"Write the output natively in [^(]+ \(([a-z]{2})\)\.")


def _make_request_body(**overrides) -> dict:
    body: dict = {
        "content": SAMPLE_CONTENT,
        "target_formats": ["twitter_thread"],
        "brand_voice": "professional",
    }
    body.update(overrides)
    return body


def _make_batch_job(**overrides) -> dict:
    job: dict = {
        "content": SAMPLE_CONTENT,
        "target_formats": ["twitter_thread"],
    }
    job.update(overrides)
    return job


def _make_registry() -> FormatRegistry:
    registry = FormatRegistry()
    registry.register(
        FormatTemplate(
            format_id=ContentFormat.TWITTER_THREAD,
            name="Twitter Thread",
            description="Thread of tweets",
            max_length=280 * 20,
            supports_images=False,
            supports_links=True,
            tone_guidance="Concise, engaging",
            structure_hints="One idea per tweet",
            target_audience="Twitter users",
            system_prompt="You are a social media expert.",
            user_prompt_template=(
                "Content: {content}\nBrand: {brand_voice}\n"
                "Instructions: {custom_instructions}"
            ),
        )
    )
    return registry


class _MockRouter:
    """Duck-typed LLMRouter for service-level tests.

    Records the language of every issued call, tracks the observed
    concurrency, and can simulate per-language failures.
    """

    def __init__(self, fail_langs: set[str] | None = None) -> None:
        self.calls: list[str] = []  # lang code per issued LLM call
        self.fail_langs = fail_langs or set()
        self.active = 0
        self.max_active = 0

    def _detect_lang(self, prompt: str) -> str:
        match = _LANG_MARKER.search(prompt)
        return match.group(1) if match else "?"

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        strategy: RouterStrategy = RouterStrategy.AUTO_FALLBACK,
        preferred_provider: str | None = None,
        preferred_model: str | None = None,
    ) -> LLMResponse:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            await asyncio.sleep(0.02)  # yield so sibling calls can overlap
            lang = self._detect_lang(prompt)
            self.calls.append(lang)
            if lang in self.fail_langs:
                raise RuntimeError(f"simulated failure for language '{lang}'")
            return LLMResponse(
                text=f"[generated-{lang}]",
                model="mock",
                provider="mock",
                input_tokens=0,
                output_tokens=0,
            )
        finally:
            self.active -= 1


class TestChunkDecisionUsesSingleCallEstimate:
    """F1: chunk only when a SINGLE (format, lang) call exceeds the window."""

    async def test_large_content_many_languages_does_not_chunk(self):
        router = _MockRouter()
        svc = RepurposeService(llm_router=router, format_registry=_make_registry())
        # ~100k chars → ~25k tokens per call (fits the 128k window); × 14
        # languages ≈ 350k tokens — the old full-list estimate chunked this.
        item = ContentItem(
            title="T",
            body="word " * 20000,
            source_format=ContentFormat.BLOG_POST,
        )
        result = await svc.repurpose(
            content=item,
            target_formats=[ContentFormat.TWITTER_THREAD],
            target_languages=SUPPORTED_CODES,
        )
        # Exactly one call per language — no chunk path (chunking would have
        # issued one call per ~8000-token chunk, far more than 14).
        assert len(router.calls) == len(SUPPORTED_CODES)
        assert sorted(router.calls) == sorted(SUPPORTED_CODES)
        assert not any("chunk" in w.lower() for w in result.warnings)
        per_lang = result.repurposed[ContentFormat.TWITTER_THREAD]
        assert set(per_lang) == set(SUPPORTED_CODES)
        for lang in SUPPORTED_CODES:
            assert per_lang[lang] == f"[generated-{lang}]"

    async def test_single_call_exceeding_window_still_chunks(self):
        router = _MockRouter()
        svc = RepurposeService(llm_router=router, format_registry=_make_registry())
        # ~550k chars → ~137k tokens in ONE call > 128k window → must chunk.
        item = ContentItem(
            title="T",
            body="word " * 110000,
            source_format=ContentFormat.BLOG_POST,
        )
        result = await svc.repurpose(
            content=item,
            target_formats=[ContentFormat.TWITTER_THREAD],
            target_languages=["es"],
        )
        assert any("chunk" in w.lower() for w in result.warnings)
        assert len(router.calls) > 1  # split into multiple chunk calls


class TestLanguageDedupAndCap:
    """F2: duplicate / over-long target_languages rejected (OWASP LLM10)."""

    async def test_duplicate_languages_rejected_via_api(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=_make_request_body(target_languages=["es", "es"]),
            )
        assert response.status_code == 422
        assert "duplicate" in response.text.lower()

    async def test_many_duplicate_languages_rejected_via_api(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=_make_request_body(target_languages=["es"] * 1000),
            )
        assert response.status_code == 422
        assert "duplicate" in response.text.lower()

    async def test_duplicate_languages_fail_batch_job(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose/batch",
                json={
                    "jobs": [_make_batch_job(target_languages=["es", "es"])],
                    "concurrency": 1,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["failed"] == 1
        assert "duplicate" in " ".join(data["errors"]).lower()

    async def test_many_duplicate_languages_fail_batch_job(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose/batch",
                json={
                    "jobs": [_make_batch_job(target_languages=["es"] * 1000)],
                    "concurrency": 1,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["failed"] == 1
        assert "duplicate" in " ".join(data["errors"]).lower()

    async def test_unique_languages_still_accepted_via_api(self):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/repurpose",
                json=_make_request_body(target_languages=["es", "de"]),
            )
        assert response.status_code == 200

    def test_helper_rejects_duplicates(self):
        with pytest.raises(ValueError, match="(?i)duplicate"):
            validate_languages(["es", "es"])

    def test_helper_rejects_over_cap(self):
        with pytest.raises(ValueError, match="(?i)duplicate|too many"):
            validate_languages(["es"] * 1000)

    def test_helper_accepts_unique_supported(self):
        assert validate_languages(["es", "de"]) is None

    async def test_service_level_rejection(self):
        """repurpose() validates even when called outside the API layer."""
        svc = RepurposeService()
        item = ContentItem(
            title="T", body="B", source_format=ContentFormat.BLOG_POST
        )
        with pytest.raises(ValueError, match="(?i)duplicate"):
            await svc.repurpose(
                content=item,
                target_formats=[ContentFormat.TWITTER_THREAD],
                target_languages=["es", "es"],
            )


class TestParallelPerLanguageCalls:
    """F3: per-language LLM calls run concurrently with error isolation."""

    async def test_exactly_one_call_per_unique_language_issued(self):
        router = _MockRouter()
        svc = RepurposeService(llm_router=router, format_registry=_make_registry())
        item = ContentItem(
            title="T", body="Hello world", source_format=ContentFormat.BLOG_POST
        )
        langs = ["es", "de", "fr"]
        result = await svc.repurpose(
            content=item,
            target_formats=[ContentFormat.TWITTER_THREAD],
            target_languages=langs,
        )
        assert len(router.calls) == len(langs)  # exactly one call per language
        assert sorted(router.calls) == sorted(langs)
        assert router.max_active >= 2  # calls overlapped → parallel, not serial
        per_lang = result.repurposed[ContentFormat.TWITTER_THREAD]
        assert list(per_lang) == langs  # requested order preserved
        for lang in langs:
            assert per_lang[lang] == f"[generated-{lang}]"

    async def test_failing_language_falls_back_others_succeed(self):
        router = _MockRouter(fail_langs={"de"})
        svc = RepurposeService(llm_router=router, format_registry=_make_registry())
        item = ContentItem(
            title="T", body="Hello world", source_format=ContentFormat.BLOG_POST
        )
        langs = ["es", "de", "fr"]
        result = await svc.repurpose(
            content=item,
            target_formats=[ContentFormat.TWITTER_THREAD],
            target_languages=langs,
        )
        per_lang = result.repurposed[ContentFormat.TWITTER_THREAD]
        assert set(per_lang) == set(langs)  # error isolation: all languages present
        assert per_lang["es"] == "[generated-es]"
        assert per_lang["fr"] == "[generated-fr]"
        assert per_lang["de"] != "[generated-de]"  # fell back individually
        assert "Hello world" in per_lang["de"]  # fallback = prefix + body
        assert any("failed" in w.lower() for w in result.warnings)

    async def test_concurrency_bounded_by_semaphore(self):
        router = _MockRouter()
        svc = RepurposeService(
            llm_router=router,
            format_registry=_make_registry(),
            max_concurrent_languages=2,
        )
        item = ContentItem(
            title="T", body="Hello world", source_format=ContentFormat.BLOG_POST
        )
        await svc.repurpose(
            content=item,
            target_formats=[ContentFormat.TWITTER_THREAD],
            target_languages=["es", "de", "fr", "pt"],
        )
        assert router.max_active <= 2  # bounded by the semaphore
