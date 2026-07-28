"""Content repurposing service."""

from __future__ import annotations

import contextlib
import logging

from app.models.auth import UserResponse
from app.models.content import (
    BrandVoice,
    ContentFormat,
    ContentItem,
    RepurposeResponse,
)
from app.services.auth import get_user_brand_voice
from app.services.brand_voice import BrandVoiceConfig
from app.services.formats.registry import FormatRegistry
from app.services.llm.router import LLMRouter, RouterStrategy

logger = logging.getLogger(__name__)


class RepurposeService:
    """Core service for repurposing content across formats.

    If a user is provided, their personal brand voice configuration
    is applied automatically.

    When llm_router and format_registry are both provided, repurpose()
    uses the LLM layer to generate content for each target format.
    Otherwise it falls back to the original string-concatenation behavior.
    """

    def __init__(
        self,
        api_key: str | None = None,
        user: UserResponse | None = None,
        llm_router: LLMRouter | None = None,
        format_registry: FormatRegistry | None = None,
    ) -> None:
        self.api_key = api_key
        self.user = user
        self.llm_router = llm_router
        self.format_registry = format_registry

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

    async def repurpose(
        self,
        content: ContentItem,
        target_formats: list[ContentFormat],
        brand_voice: BrandVoice = BrandVoice.PROFESSIONAL,
        custom_instructions: str | None = None,
        llm_strategy: str | None = None,
        preferred_provider: str | None = None,
        preferred_model: str | None = None,
    ) -> RepurposeResponse:
        """Repurpose content into target formats.

        When both llm_router and format_registry are configured, generates
        content via the LLM layer with token-aware dispatch. Otherwise falls
        back to string concatenation (backward compatible).
        """
        resolved_voice, resolved_custom = self._resolve_brand_voice(
            brand_voice, custom_instructions
        )
        voice_config = BrandVoiceConfig(voice=resolved_voice)
        repurposed: dict[ContentFormat, str] = {}
        warnings: list[str] = []

        use_llm = self.llm_router is not None and self.format_registry is not None

        if use_llm:
            strategy = self._resolve_strategy(llm_strategy)

            for fmt in target_formats:
                result = await self._generate_with_llm(
                    fmt=fmt,
                    content=content,
                    resolved_voice=resolved_voice,
                    resolved_custom=resolved_custom,
                    voice_config=voice_config,
                    strategy=strategy,
                    preferred_provider=preferred_provider,
                    preferred_model=preferred_model,
                    warnings=warnings,
                )
                repurposed[fmt] = result
        else:
            # Backward-compatible string concatenation
            for fmt in target_formats:
                prefix = voice_config.get_prompt_prefix()
                body = content.body
                if resolved_custom:
                    body += f"\n\nInstructions: {resolved_custom}"
                repurposed[fmt] = f"{prefix}\n\n{body}"

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
    ) -> str:
        """Generate content for a single format using the LLM layer."""
        try:
            template = self.format_registry.get(fmt)  # type: ignore[union-attr]
        except KeyError:
            warnings.append(f"No format template for '{fmt}', using fallback")
            prefix = voice_config.get_prompt_prefix()
            body = content.body
            if resolved_custom:
                body += f"\n\nInstructions: {resolved_custom}"
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

        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        estimated_tokens = self.estimate_tokens(full_prompt)

        # Token-aware dispatch: if the prompt is very large, chunk it
        context_window_estimate = 128000

        if estimated_tokens > context_window_estimate:
            warnings.append(
                f"Content for '{fmt}' (~{estimated_tokens} tokens) exceeds typical "
                f"context window ({context_window_estimate}). Chunking content."
            )
            return await self._dispatch_chunked(
                fmt=fmt, template=template, content=content,
                resolved_custom=resolved_custom, resolved_voice=resolved_voice,
                system_prompt=system_prompt, strategy=strategy,
                preferred_provider=preferred_provider,
                preferred_model=preferred_model,
                warnings=warnings,
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
            return f"{prefix}\n\n{content.body}"

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
