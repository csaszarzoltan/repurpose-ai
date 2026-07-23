"""Brand voice customization service."""

from __future__ import annotations

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
        self.voice = voice
        self._config = dict(self.DEFAULT_CONFIGS.get(voice, {}))

    def get_prompt_prefix(self) -> str:
        """Get the prompt prefix for this voice."""
        tone = self._config.get("tone", "neutral")
        return f"Write in a {tone} tone."

    def get_style_guide(self) -> dict[str, str]:
        """Return style guide dict for this voice."""
        return dict(self._config)

    def adapt_text(self, text: str) -> str:
        """Adapt text to match the brand voice."""
        tone = self._config.get("tone", "neutral")
        return f"[{tone}] {text}"

    def validate_tone(self, text: str) -> tuple[bool, list[str]]:
        """Validate if text matches the brand voice. Returns (is_valid, issues)."""
        issues: list[str] = []
        expected_tone = self._config.get("tone", "")
        if expected_tone and expected_tone not in text.lower():
            issues.append(f"Text does not match tone '{expected_tone}'")
        is_valid = len(issues) == 0
        return is_valid, issues

    def merge_custom(self, custom: dict[str, str]) -> None:
        """Merge custom overrides into the current config."""
        self._config.update(custom)
