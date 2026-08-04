"""Multi-language content repurposing support.

Provides the supported-language registry and the helpers that power the
multi-language repurposing feature (analyst spec t_758a9a4e):

- ``SUPPORTED_LANGUAGES`` — the 14 ISO 639-1 codes the product supports for
  translated output, with English and native display names.
- ``validate_languages`` — reject unsupported codes before any generation.
- ``build_per_language_output`` — expand the legacy single-language output
  shape into the per-language shape used when translations are requested.
- ``estimate_multilang_tokens`` — token estimate that scales with the number
  of target languages.
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
    when any code is not in the registry. Duplicate codes and lists longer
    than the registry are rejected too: every entry maps to its own LLM
    generation, so duplicates would amplify LLM calls without adding output
    (OWASP LLM10 — unbounded consumption). Returns ``None`` when all codes are
    supported (an empty list is valid — it preserves the legacy single-language
    behavior).
    """
    unsupported = sorted({code for code in target_languages if code not in SUPPORTED_LANGUAGES})
    if unsupported:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
        raise ValueError(
            f"Unsupported language code(s): {', '.join(unsupported)}. "
            f"Supported languages: {supported}"
        )
    seen: set[str] = set()
    duplicates: set[str] = set()
    for code in target_languages:
        if code in seen:
            duplicates.add(code)
        seen.add(code)
    if duplicates:
        raise ValueError(
            f"Duplicate language code(s): {', '.join(sorted(duplicates))}. "
            "Each language may be requested at most once."
        )
    if len(target_languages) > len(SUPPORTED_LANGUAGES):
        raise ValueError(
            f"Too many target languages: {len(target_languages)} "
            f"(maximum {len(SUPPORTED_LANGUAGES)}). "
            "Each language may be requested at most once."
        )


def build_per_language_output(
    repurposed: dict[str, str], target_languages: list[str]
) -> dict[str, dict[str, str]]:
    """Expand a single-language ``{format: content}`` mapping into the
    multi-language shape ``{format: {lang_code: content}}``.

    ``repurposed`` is the legacy single-language output keyed by format id.
    When ``target_languages`` is empty the mapping is returned unchanged
    (legacy passthrough).
    """
    if not target_languages:
        return repurposed  # type: ignore[return-value]  # legacy passthrough
    return {
        fmt: {lang: content for lang in target_languages}
        for fmt, content in repurposed.items()
    }


def estimate_multilang_tokens(text: str, target_languages: list[str]) -> int:
    """Estimate total LLM tokens for generating ``text`` in every target language.

    Accounts for each target language: the estimate grows with the number of
    languages (per-language generation cost). With an empty language list it
    matches the legacy single-language estimate (roughly 4 chars per token).
    """
    base = max(1, len(text) // 4)
    if not target_languages:
        return base
    return base * len(target_languages)
