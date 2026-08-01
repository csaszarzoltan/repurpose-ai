"""Build a generation service from explicitly configured LLM providers."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Literal

from app.services.formats.registry import FormatRegistry
from app.services.formats.templates import ALL_TEMPLATES
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.openrouter_provider import OpenRouterProvider
from app.services.llm.router import LLMRouter
from app.services.repurpose import RepurposeService

if TYPE_CHECKING:
    from app.models.auth import UserResponse

GenerationMode = Literal["llm", "template_fallback"]


def build_generation_service(
    user: UserResponse | None = None,
) -> tuple[RepurposeService, GenerationMode]:
    """Return an LLM-backed service when at least one provider is configured.

    Providers without an API key are not registered, preventing predictable
    network failures and keeping fallback behavior explicit to the caller.
    """
    router = LLMRouter()
    configured: list[tuple[str, object]] = []
    if key := os.getenv("OPENROUTER_API_KEY"):
        configured.append(("openrouter", OpenRouterProvider(api_key=key)))
    if key := os.getenv("OPENAI_API_KEY"):
        configured.append(("openai", OpenAIProvider(api_key=key)))
    if key := os.getenv("ANTHROPIC_API_KEY"):
        configured.append(("anthropic", AnthropicProvider(api_key=key)))

    if not configured:
        return RepurposeService(user=user), "template_fallback"

    for name, provider in configured:
        router.register_provider(name, provider)  # type: ignore[arg-type]

    registry = FormatRegistry()
    for template in ALL_TEMPLATES:
        registry.register(template)
    return RepurposeService(user=user, llm_router=router, format_registry=registry), "llm"
