"""Content repurposing service."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING

from app.models.content import (
    BrandVoice,
    ContentFormat,
    ContentItem,
    RepurposeResponse,
)
from app.services.auth import get_user_brand_voice
from app.services.brand_voice import BrandVoiceConfig
from app.services.languages import (
    SUPPORTED_LANGUAGES,
    build_per_language_output,
    estimate_multilang_tokens,
    validate_languages,
)
from app.services.llm.router import LLMRouter, RouterStrategy

if TYPE_CHECKING:
    from app.models.auth import UserResponse
    from app.services.formats.registry import FormatRegistry

logger = logging.getLogger(__name__)


class RepurposeService:
    """Core service for repurposing content across formats.

    If a user is provided, their personal brand voice configuration
    is applied automatically.

    When llm_router and format_registry are both provided, repurpose()
    uses the LLM layer to generate content for each target format.
    Otherwise it falls back to the original string-concatenation behavior.

    When ``target_languages`` is non-empty, the repurposed output for every
    requested format is a ``{lang_code: content}`` mapping — each language is
    generated natively by the LLM in a single pass per format (or expanded
    from the legacy content in the string-concatenation fallback).
    """

    def __init__(
        self,
        api_key: str | None = None,
        user: UserResponse | None = None,
        llm_router: LLMRouter | None = None,
        format_registry: FormatRegistry | None = None,
        max_concurrent_languages: int = 5,
    ) -> None:
        self.api_key = api_key
        self.user = user
        self.llm_router = llm_router
        self.format_registry = format_registry
        self.max_concurrent_languages = max(1, max_concurrent_languages)

    def _resolve_brand_voice(
        self, requested_voice: BrandVoice, custom_instructions: str | None
    ) -> tuple[BrandVoice, str | None]:
        """Resolve the brand voice, checking user config first.

        Returns (resolved_voice, resolved_custom_instructions).
        """
        resolved_voice = requested_voice
        resolved_custom = custom_instructions

        if self.user is not None:
            user_config = get_user_brand_voice(self.user.user_id)
            if user_config is not None:
                # User has a personal brand voice config — use it
                user_voice = user_config.get("brand_voice")
                if user_voice:
                    with contextlib.suppress(ValueError):
                        resolved_voice = BrandVoice(user_voice)  # Fall back to requested voice if invalid

                user_instructions = user_config.get("custom_instructions")
                if user_instructions:
                    resolved_custom = (
                        f"{user_instructions}\n\n{custom_instructions}"
                        if custom_instructions
                        else user_instructions
                    )

        return resolved_voice, resolved_custom

    @staticmethod
    def _language_instruction(lang: str) -> str:
        """Build the prompt instruction for generating natively in ``lang``.

        Keeps tone/brand voice and platform conventions intact while
        localizing hashtags and keywords — no external translation APIs.
        """
        entry = SUPPORTED_LANGUAGES.get(lang)
        name = entry["name"] if entry else lang
        return (
            f"Write the output natively in {name} ({lang}). Preserve the tone and "
            "brand voice, follow the platform conventions for that language, and "
            "localize hashtags and keywords where appropriate. Do not translate "
            "brand names or product names."
        )

    async def repurpose(
        self,
        content: ContentItem,
        target_formats: list[ContentFormat],
        brand_voice: BrandVoice = BrandVoice.PROFESSIONAL,
        custom_instructions: str | None = None,
        llm_strategy: str | None = None,
        preferred_provider: str | None = None,
        preferred_model: str | None = None,
        target_languages: list[str] | None = None,
    ) -> RepurposeResponse:
        """Repurpose content into target formats.

        When both llm_router and format_registry are configured, generates
        content via the LLM layer with token-aware dispatch. Otherwise falls
        back to string concatenation (backward compatible).

        When ``target_languages`` is non-empty, each format's output becomes a
        ``{lang_code: content}`` mapping with one native-language generation
        per requested language; an empty list (the default) preserves the
        legacy single-language ``{format: content}`` shape.
        """
        # Defense-in-depth: reject unsupported / duplicate / over-long codes
        # here so every caller (API, batch, workflow, webhook) is covered even
        # if a boundary forgets to validate. ``_language_instruction``
        # interpolates the raw code into the LLM prompt, so it must never see
        # an unvalidated value.
        validate_languages(target_languages or [])
        resolved_voice, resolved_custom = self._resolve_brand_voice(
            brand_voice, custom_instructions
        )
        voice_config = BrandVoiceConfig(voice=resolved_voice)
        repurposed: dict[ContentFormat, str | dict[str, str]] = {}
        warnings: list[str] = []

        use_llm = self.llm_router is not None and self.format_registry is not None

        if use_llm:
            strategy = self._resolve_strategy(llm_strategy)

            for fmt in target_formats:
                repurposed[fmt] = await self._generate_with_llm(
                    fmt=fmt,
                    content=content,
                    resolved_voice=resolved_voice,
                    resolved_custom=resolved_custom,
                    voice_config=voice_config,
                    strategy=strategy,
                    preferred_provider=preferred_provider,
                    preferred_model=preferred_model,
                    warnings=warnings,
                    target_languages=target_languages,
                )
        else:
            # Backward-compatible string concatenation
            legacy_output: dict[str, str] = {}
            for fmt in target_formats:
                prefix = voice_config.get_prompt_prefix()
                body = content.body
                if resolved_custom:
                    body += f"\n\nInstructions: {resolved_custom}"
                legacy_output[fmt.value] = f"{prefix}\n\n{body}"
            expanded = build_per_language_output(legacy_output, target_languages or [])
            repurposed = {ContentFormat(fmt_key): value for fmt_key, value in expanded.items()}

        return RepurposeResponse(
            original_id=content.id or "",
            repurposed=repurposed,
            warnings=warnings,
        )

    def _resolve_strategy(self, llm_strategy: str | None) -> RouterStrategy:
        """Map an llm_strategy string to a RouterStrategy enum.

        Defaults to AUTO_FALLBACK when None or unknown.
        """
        strategy_map: dict[str | None, RouterStrategy] = {
            "fastest_cheapest": RouterStrategy.FASTEST_CHEAPEST,
            "specific_provider": RouterStrategy.SPECIFIC_PROVIDER,
            "auto_fallback": RouterStrategy.AUTO_FALLBACK,
        }
        return strategy_map.get(llm_strategy, RouterStrategy.AUTO_FALLBACK)

    async def _generate_with_llm(
        self,
        fmt: ContentFormat,
        content: ContentItem,
        resolved_voice: BrandVoice,
        resolved_custom: str | None,
        voice_config: BrandVoiceConfig,
        strategy: RouterStrategy,
        preferred_provider: str | None,
        preferred_model: str | None,
        warnings: list[str],
        target_languages: list[str] | None = None,
    ) -> str | dict[str, str]:
        """Generate content for a single format using the LLM layer.

        With ``target_languages`` set, returns a ``{lang_code: content}``
        mapping — one native-language LLM pass per requested language, run
        concurrently (bounded by ``max_concurrent_languages``) with per-language
        error isolation. Otherwise returns the legacy single-language ``str``.
        """
        if target_languages:
            semaphore = asyncio.Semaphore(self.max_concurrent_languages)

            async def _generate_one(lang: str) -> tuple[str, str]:
                async with semaphore:
                    text = await self._generate_single_language(
                        fmt=fmt,
                        content=content,
                        resolved_voice=resolved_voice,
                        resolved_custom=resolved_custom,
                        voice_config=voice_config,
                        strategy=strategy,
                        preferred_provider=preferred_provider,
                        preferred_model=preferred_model,
                        warnings=warnings,
                        target_language=lang,
                        target_languages=target_languages,
                    )
                    return lang, text

            # gather preserves input order, so the mapping keeps the requested
            # language order; a failing language falls back inside
            # _generate_single_language, so gather never raises for it.
            results = await asyncio.gather(
                *(_generate_one(lang) for lang in target_languages)
            )
            return dict(results)

        return await self._generate_single_language(
            fmt=fmt,
            content=content,
            resolved_voice=resolved_voice,
            resolved_custom=resolved_custom,
            voice_config=voice_config,
            strategy=strategy,
            preferred_provider=preferred_provider,
            preferred_model=preferred_model,
            warnings=warnings,
            target_language=None,
            target_languages=None,
        )

    async def _generate_single_language(
        self,
        fmt: ContentFormat,
        content: ContentItem,
        resolved_voice: BrandVoice,
        resolved_custom: str | None,
        voice_config: BrandVoiceConfig,
        strategy: RouterStrategy,
        preferred_provider: str | None,
        preferred_model: str | None,
        warnings: list[str],
        target_language: str | None,
        target_languages: list[str] | None,
    ) -> str:
        """Generate content for a single format/language pair via the LLM.

        ``target_language`` selects the native-language prompt instruction;
        ``target_languages`` is the full requested list, used for total cost
        estimation in warnings only — the chunk decision uses the single-call
        estimate.
        """
        try:
            template = self.format_registry.get(fmt)  # type: ignore[union-attr]
        except KeyError:
            warnings.append(f"No format template for '{fmt}', using fallback")
            prefix = voice_config.get_prompt_prefix()
            body = content.body
            if resolved_custom:
                body += f"\n\nInstructions: {resolved_custom}"
            if target_language:
                body += f"\n\nLanguage: {self._language_instruction(target_language)}"
            return f"{prefix}\n\n{body}"

        # Build the system prompt from template + brand voice + tone guidance
        system_prompt = (
            f"{template.system_prompt}\n\n"
            f"Tone: {template.tone_guidance}\n"
            f"Audience: {template.target_audience}"
        )

        # Fill in user prompt template with the source content
        user_prompt = template.user_prompt_template.format(
            content=content.body,
            custom_instructions=resolved_custom or "None",
            brand_voice=resolved_voice.value if resolved_voice else "professional",
        )
        if target_language:
            user_prompt += f"\n\nLanguage: {self._language_instruction(target_language)}"

        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Token-aware dispatch: the context-window check must reflect a SINGLE
        # (format, lang) call — each call carries exactly one language
        # instruction, so the per-call prompt is ``full_prompt``, not
        # full_prompt × N. The full-language-list estimate is used only for
        # cost reporting/warnings.
        single_call_estimate = estimate_multilang_tokens(
            full_prompt, [target_language] if target_language else []
        )
        total_estimate = estimate_multilang_tokens(
            full_prompt,
            target_languages or ([target_language] if target_language else []),
        )
        context_window_estimate = 128000

        if single_call_estimate > context_window_estimate:
            warnings.append(
                f"Content for '{fmt}' (~{total_estimate} tokens across "
                f"{len(target_languages or []) or 1} language(s)) exceeds typical "
                f"context window ({context_window_estimate}). Chunking content."
            )
            return await self._dispatch_chunked(
                fmt=fmt, template=template, content=content,
                resolved_custom=resolved_custom, resolved_voice=resolved_voice,
                system_prompt=system_prompt, strategy=strategy,
                preferred_provider=preferred_provider,
                preferred_model=preferred_model,
                warnings=warnings, target_language=target_language,
            )

        try:
            response = await self.llm_router.generate(  # type: ignore[union-attr]
                prompt=user_prompt,
                system=system_prompt,
                strategy=strategy,
                preferred_provider=preferred_provider,
                preferred_model=preferred_model,
            )
            return response.text
        except Exception as e:
            logger.warning("LLM generation failed for '%s': %s", fmt, e)
            warnings.append(f"LLM generation failed for '{fmt}': {e}")
            prefix = voice_config.get_prompt_prefix()
            body = content.body
            if target_language:
                body += f"\n\nLanguage: {self._language_instruction(target_language)}"
            return f"{prefix}\n\n{body}"

    async def _dispatch_chunked(
        self,
        fmt: ContentFormat,
        template: object,
        content: ContentItem,
        resolved_custom: str | None,
        resolved_voice: BrandVoice,
        system_prompt: str,
        strategy: RouterStrategy,
        preferred_provider: str | None,
        preferred_model: str | None,
        warnings: list[str],
        target_language: str | None = None,
    ) -> str:
        """Split content into chunks and dispatch each to the LLM."""
        chunks = self.chunk_content(content.body, max_tokens=8000)
        chunk_results: list[str] = []

        for chunk in chunks:
            chunk_prompt = template.user_prompt_template.format(  # type: ignore[union-attr]
                content=chunk,
                custom_instructions=resolved_custom or "None",
                brand_voice=resolved_voice.value if resolved_voice else "professional",
            )
            if target_language:
                chunk_prompt += f"\n\nLanguage: {self._language_instruction(target_language)}"
            try:
                response = await self.llm_router.generate(  # type: ignore[union-attr]
                    prompt=chunk_prompt,
                    system=system_prompt,
                    strategy=strategy,
                    preferred_provider=preferred_provider,
                    preferred_model=preferred_model,
                )
                chunk_results.append(response.text)
            except Exception as e:
                logger.warning("LLM chunk failed for '%s': %s", fmt, e)
                chunk_results.append(f"[Error generating chunk: {e}]")

        return "\n\n".join(chunk_results) if chunk_results else ""

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough: 4 chars per token)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def chunk_content(self, text: str, max_tokens: int = 4000) -> list[str]:
        """Split content into token-limited chunks."""
        chunks: list[str] = []
        words = text.split()
        current_chunk: list[str] = []
        current_token_count = 0

        for word in words:
            word_tokens = max(1, len(word) // 4)
            if current_token_count + word_tokens > max_tokens and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_token_count = word_tokens
            else:
                current_chunk.append(word)
                current_token_count += word_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks or [""]

    def get_supported_formats(self) -> list[ContentFormat]:
        """Return list of supported output formats."""
        return list(ContentFormat)

    async def analyze_content(self, content: ContentItem) -> dict:
        """Analyze content and return metadata (sentiment, topics, etc.)."""
        return {
            "title": content.title,
            "word_count": len(content.body.split()),
            "char_count": len(content.body),
            "tags": content.tags,
            "source_format": content.source_format,
        }
