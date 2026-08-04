"""Repurpose API endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Header, HTTPException

from app.dependencies import get_optional_user
from app.models.content import (
    RepurposeRequest,
    RepurposeResponse,
)
from app.services.languages import validate_languages
from app.services.repurpose import RepurposeService

if TYPE_CHECKING:
    from app.models.auth import UserResponse

router = APIRouter(prefix="/api/v1", tags=["repurpose"])


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
    return result
