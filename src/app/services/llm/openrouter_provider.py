"""OpenRouter LLM provider implementation.

Uses the OpenAI-compatible API (openai SDK pointed at OpenRouter's endpoint).
"""

from __future__ import annotations

import logging
import os

from app.services.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-4o-mini"

# Sensible default for OpenRouter — actual window depends on the routed model.
OPENROUTER_DEFAULT_CONTEXT_WINDOW = 128_000


class OpenRouterProvider(BaseLLMProvider):
    """Provider that uses the OpenRouter API (OpenAI-compatible).

    Expects OPENROUTER_API_KEY env var, or pass api_key directly.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL)
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY is not set — API calls will fail")

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a completion via the OpenRouter API."""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=model or DEFAULT_OPENROUTER_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        choice = response.choices[0]
        return LLMResponse(
            text=choice.message.content or "",
            model=response.model,
            provider="openrouter",
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken, falling back to heuristic."""
        try:
            import tiktoken

            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except ImportError:
            logger.debug("tiktoken not available, using heuristic fallback")
            if not text:
                return 0
            return max(1, len(text) // 4)

    def get_context_window(self, model: str | None = None) -> int:
        """Return the default context window for OpenRouter models."""
        return OPENROUTER_DEFAULT_CONTEXT_WINDOW
