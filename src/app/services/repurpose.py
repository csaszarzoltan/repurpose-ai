"""Content repurposing service."""

from __future__ import annotations

from app.models.content import (
    BrandVoice,
    ContentFormat,
    ContentItem,
    RepurposeResponse,
)
from app.services.brand_voice import BrandVoiceConfig


class RepurposeService:
    """Core service for repurposing content across formats."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    async def repurpose(
        self,
        content: ContentItem,
        target_formats: list[ContentFormat],
        brand_voice: BrandVoice = BrandVoice.PROFESSIONAL,
        custom_instructions: str | None = None,
    ) -> RepurposeResponse:
        """Repurpose content into target formats."""
        voice_config = BrandVoiceConfig(voice=brand_voice)
        repurposed: dict[ContentFormat, str] = {}

        for fmt in target_formats:
            prefix = voice_config.get_prompt_prefix()
            body = content.body
            if custom_instructions:
                body += f"\n\nInstructions: {custom_instructions}"
            repurposed[fmt] = f"{prefix}\n\n{body}"

        return RepurposeResponse(
            original_id=content.id or "",
            repurposed=repurposed,
        )

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
