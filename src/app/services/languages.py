"""Multi-language content repurposing support.

Pre-dev stubs for the multi-language feature (analyst spec t_758a9a4e):

- ``SUPPORTED_LANGUAGES`` registry — real contract data (14 ISO 639-1 codes
  with display names), so the interface tests can verify the registry shape.
- ``validate_languages``, ``build_per_language_output`` and
  ``estimate_multilang_tokens`` — behavioral stubs that raise
  ``NotImplementedError`` until the feature is implemented.
"""

from __future__ import annotations

SUPPORTED_LANGUAGES: dict[str, dict[str, str]] = {
    "es": {"id": "es", "name": "Spanish", "native_name": "Español"},
    "de": {"id": "de", "name": "German", "native_name": "Deutsch"},
    "fr": {"id": "fr", "name": "French", "native_name": "Français"},
    "pt": {"id": "pt", "name": "Portuguese", "native_name": "Português"},
    "it": {"id": "it", "name": "Italian", "native_name": "Italiano"},
    "nl": {"id": "nl", "name": "Dutch", "native_name": "Nederlands"},
    "ja": {"id": "ja", "name": "Japanese", "native_name": "日本語"},
    "ko": {"id": "ko", "name": "Korean", "native_name": "한국어"},
    "zh": {"id": "zh", "name": "Chinese", "native_name": "中文"},
    "hi": {"id": "hi", "name": "Hindi", "native_name": "हिन्दी"},
    "ar": {"id": "ar", "name": "Arabic", "native_name": "العربية"},
    "ru": {"id": "ru", "name": "Russian", "native_name": "Русский"},
    "pl": {"id": "pl", "name": "Polish", "native_name": "Polski"},
    "tr": {"id": "tr", "name": "Turkish", "native_name": "Türkçe"},
}


def validate_languages(target_languages: list[str]) -> None:
    """Validate target language codes against ``SUPPORTED_LANGUAGES``.

    Raises ``ValueError`` with a message listing the supported language codes
    when any code is not in the registry. Returns ``None`` when all codes are
    supported (an empty list is valid — it preserves the legacy single-language
    behavior).
    """
    raise NotImplementedError("Multi-language validation is not implemented yet")


def build_per_language_output(
    repurposed: dict[str, str], target_languages: list[str]
) -> dict[str, dict[str, str]]:
    """Expand a single-language ``{format: content}`` mapping into the
    multi-language shape ``{format: {lang_code: content}}``.

    ``repurposed`` is the legacy single-language output keyed by format id.
    """
    raise NotImplementedError("Per-language output expansion is not implemented yet")


def estimate_multilang_tokens(text: str, target_languages: list[str]) -> int:
    """Estimate total LLM tokens for generating ``text`` in every target language.

    Accounts for each target language: the estimate grows with the number of
    languages (per-language generation cost). With an empty language list it
    must match the legacy single-language estimate.
    """
    raise NotImplementedError("Multi-language token estimation is not implemented yet")
