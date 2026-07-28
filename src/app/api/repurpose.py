"""Repurpose API endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from app.dependencies import get_optional_user
from app.models.auth import UserResponse
from app.models.content import (
    RepurposeRequest,
    RepurposeResponse,
)
from app.services.repurpose import RepurposeService

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

    Optional headers:
    - X-LLM-Provider: preferred LLM provider ("openai", "anthropic", "openrouter")
    - X-LLM-Model: preferred model name (e.g. "gpt-4o-mini", "claude-haiku")
    Optional body field:
    - llm_strategy: routing strategy ("fastest_cheapest", "specific_provider", "auto_fallback")
    """
    svc = RepurposeService(user=current_user)
    result = await svc.repurpose(
        content=request.content,
        target_formats=request.target_formats,
        brand_voice=request.brand_voice,
        custom_instructions=request.custom_instructions,
        llm_strategy=request.llm_strategy,
        preferred_provider=x_llm_provider,
        preferred_model=x_llm_model,
    )
    return result
