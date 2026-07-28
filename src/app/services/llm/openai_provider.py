"""OpenAI LLM provider implementation.

Uses the openai SDK for API calls and tiktoken for accurate token counting.
"""

from __future__ import annotations

import logging
import os

from app.services.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)

# Known context window sizes for OpenAI models (in tokens).
OPENAI_CONTEXT_WINDOWS: dict[str, int] = {
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4": 8_192,
    "gpt-4-32k": 32_768,
    "gpt-3.5-turbo": 16_385,
    "gpt-3.5-turbo-16k": 16_385,
}

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class OpenAIProvider(BaseLLMProvider):
    """Provider that uses the OpenAI API.

    Expects OPENAI_API_KEY env var, or pass api_key directly.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY is not set — API calls will fail")

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a completion via the OpenAI API."""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=model or DEFAULT_OPENAI_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        choice = response.choices[0]
        return LLMResponse(
            text=choice.message.content or "",
            model=response.model,
            provider="openai",
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
        """Return the context window for the given model."""
        return OPENAI_CONTEXT_WINDOWS.get(
            model or DEFAULT_OPENAI_MODEL,
            OPENAI_CONTEXT_WINDOWS.get(model or DEFAULT_OPENAI_MODEL, 128_000),
        )
