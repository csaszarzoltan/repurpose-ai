"""Content repurposing service."""

from __future__ import annotations

from typing import Optional

from app.models.content import (
    BrandVoice,
    ContentFormat,
    ContentItem,
    RepurposeResponse,
)


class RepurposeService:
    """Core service for repurposing content across formats."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        raise NotImplementedError

    async def repurpose(
        self,
        content: ContentItem,
        target_formats: list[ContentFormat],
        brand_voice: BrandVoice = BrandVoice.PROFESSIONAL,
        custom_instructions: Optional[str] = None,
    ) -> RepurposeResponse:
        """Repurpose content into target formats."""
        raise NotImplementedError

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        raise NotImplementedError

    def chunk_content(self, text: str, max_tokens: int = 4000) -> list[str]:
        """Split content into token-limited chunks."""
        raise NotImplementedError

    def get_supported_formats(self) -> list[ContentFormat]:
        """Return list of supported output formats."""
        raise NotImplementedError

    async def analyze_content(self, content: ContentItem) -> dict:
        """Analyze content and return metadata (sentiment, topics, etc.)."""
        raise NotImplementedError
