# Features Done (this pass)

## Features Done (this pass)
- multi-language-repurposing: Optional `target_languages` (ISO 639-1 codes) on `POST /api/v1/repurpose` and per-job on `POST /api/v1/repurpose/batch`; when non-empty every format's `repurposed` value becomes a `{lang_code: content}` mapping generated natively in each language via the existing LLM router (no external translation APIs); an empty list preserves the legacy single-language `{format: content}` shape; unsupported codes return 422 on the single endpoint and mark the batch job failed.
- languages-registry-api: `GET /api/v1/languages` returns the 14 supported target languages as `{id, name, native_name}` with ISO 639-1 ids.
- language-aware-token-estimation: `estimate_multilang_tokens` scales the per-request LLM token estimate with the number of target languages and feeds the chunking decision.
- multi-language-repurpose-ui: `/repurpose` page language multi-select populated from the registry (native name/name, empty-state + retry on failure), `target_languages` included in the submit payload only when selected, and per-format per-language output tabs with the legacy single-language view preserved.

## Sources
- CHANGELOG.md section this maps to: [Unreleased] - 2026-08-04
