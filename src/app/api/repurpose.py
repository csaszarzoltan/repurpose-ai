"""Repurpose API endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Header, HTTPException

from app.dependencies import get_optional_user
from app.models.content import (
    ContentFormat,
    RepurposeRequest,
    RepurposeResponse,
)
from app.services.languages import validate_languages
from app.services.repurpose import RepurposeService

if TYPE_CHECKING:
    from app.models.auth import UserResponse

router = APIRouter(prefix="/api/v1", tags=["repurpose"])


def _primary_repurposed_text(
    repurposed: dict[ContentFormat, str | dict[str, str]],
) -> str:
    """Extract a single publishable text from the repurposed output.

    Picks the first entry in request order (the first target format). For
    multi-language output the first language's text is used — the publish
    step publishes the primary (source) language variant.
    """
    if not repurposed:
        raise ValueError("No repurposed content to publish")

    first_value = next(iter(repurposed.values()))
    if isinstance(first_value, dict):
        if not first_value:
            raise ValueError("No repurposed content to publish")
        return next(iter(first_value.values()))
    return first_value


@router.post("/repurpose", response_model=RepurposeResponse)
async def repurpose_content(
    request: RepurposeRequest,
    current_user: UserResponse | None = Depends(get_optional_user),
    x_llm_provider: str | None = Header(None),
    x_llm_model: str | None = Header(None),
) -> RepurposeResponse:
    """Repurpose content into one or more target formats.

    If the user is authenticated, their personal brand voice configuration
    is applied automatically (overriding the request's brand_voice).

    Optional body field:
    - target_languages: list of ISO 639-1 codes (e.g. ["es", "de"]) — when
      non-empty, every format's output becomes a {lang_code: content} mapping
      generated natively in each requested language. Unsupported codes are
      rejected with 422. An empty list preserves the legacy single-language
      output shape.

    Optional headers:
    - X-LLM-Provider: preferred LLM provider ("openai", "anthropic", "openrouter")
    - X-LLM-Model: preferred model name (e.g. "gpt-4o-mini", "claude-haiku")
    Optional body field:
    - llm_strategy: routing strategy ("fastest_cheapest", "specific_provider", "auto_fallback")
    """
    try:
        validate_languages(request.target_languages)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

    svc = RepurposeService(user=current_user)
    result = await svc.repurpose(
        content=request.content,
        target_formats=request.target_formats,
        brand_voice=request.brand_voice,
        custom_instructions=request.custom_instructions,
        llm_strategy=request.llm_strategy,
        preferred_provider=x_llm_provider,
        preferred_model=x_llm_model,
        target_languages=request.target_languages,
    )

    # Publish destinations: after a successful repurpose, dispatch the
    # primary output to each requested platform. Unknown platforms → 422;
    # missing credentials / publish failures → warning entries, the
    # repurpose result itself is never failed.
    if request.destinations:
        # Reuse the publish API's module-level service instances so the
        # credential store is SHARED with the OAuth connect flow and the
        # publish endpoint (a separate instance would see no credentials).
        from app.api.publish import (
            _auth_service as publish_auth_service,
        )
        from app.api.publish import (
            _publish_service as publish_service,
        )
        from app.services.publish_destinations import (
            publish_to_destinations,
            summarize_publish_results,
        )

        try:
            primary_text = _primary_repurposed_text(result.repurposed)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None

        try:
            published, destination_warnings = await publish_to_destinations(
                request.destinations,
                primary_text,
                title=request.content.title,
                publish_service=publish_service,
                auth_service=publish_auth_service,
                # The repurpose payload has no top-level media field today;
                # forward the source content's media URL when present so
                # image-driven destinations (Instagram) can publish.
                media_urls=(
                    [request.content.media_url]
                    if getattr(request.content, "media_url", None)
                    else None
                ),
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None

        result.warnings.extend(destination_warnings)
        result.warnings.extend(summarize_publish_results(published))

    return result
