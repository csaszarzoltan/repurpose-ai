"""Brand voice customization service."""

from __future__ import annotations

from typing import Optional

from app.models.content import BrandVoice


class BrandVoiceConfig:
    """Configuration for brand voice customization."""

    DEFAULT_CONFIGS: dict[BrandVoice, dict[str, str]] = {
        BrandVoice.PROFESSIONAL: {
            "tone": "formal",
            "style": "business",
            "vocabulary": "standard",
        },
        BrandVoice.CASUAL: {
            "tone": "informal",
            "style": "conversational",
            "vocabulary": "everyday",
        },
        BrandVoice.HUMOROUS: {
            "tone": "playful",
            "style": "entertaining",
            "vocabulary": "creative",
        },
    }

    def __init__(self, voice: BrandVoice = BrandVoice.PROFESSIONAL) -> None:
        raise NotImplementedError

    def get_prompt_prefix(self) -> str:
        """Get the prompt prefix for this voice."""
        raise NotImplementedError

    def get_style_guide(self) -> dict[str, str]:
        """Return style guide dict for this voice."""
        raise NotImplementedError

    def adapt_text(self, text: str) -> str:
        """Adapt text to match the brand voice."""
        raise NotImplementedError

    def validate_tone(self, text: str) -> tuple[bool, list[str]]:
        """Validate if text matches the brand voice. Returns (is_valid, issues)."""
        raise NotImplementedError

    def merge_custom(self, custom: dict[str, str]) -> None:
        """Merge custom overrides into the current config."""
        raise NotImplementedError
