"""Anthropic LLM provider implementation.

Uses the anthropic SDK for API calls.
"""

from __future__ import annotations

import logging
import os

from app.services.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)

# Known context window sizes for Anthropic models (in tokens).
ANTHROPIC_CONTEXT_WINDOWS: dict[str, int] = {
    "claude-3-opus": 200_000,
    "claude-3-sonnet": 200_000,
    "claude-3-haiku": 200_000,
    "claude-3.5-sonnet": 200_000,
    "claude-3.5-haiku": 200_000,
    "claude-opus-4": 200_000,
    "claude-sonnet-4": 200_000,
    "claude-haiku": 200_000,
    "claude-sonnet": 200_000,
}

DEFAULT_CLAUDE_MODEL = "claude-sonnet-4"


class AnthropicProvider(BaseLLMProvider):
    """Provider that uses the Anthropic API.

    Expects ANTHROPIC_API_KEY env var, or pass api_key directly.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY is not set — API calls will fail")

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a completion via the Anthropic API."""
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key)

        kwargs: dict = {
            "model": model or DEFAULT_CLAUDE_MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        response = await client.messages.create(**kwargs)

        # Extract text content from the response
        text_parts = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)

        return LLMResponse(
            text="".join(text_parts),
            model=response.model,
            provider="anthropic",
            input_tokens=response.usage.input_tokens if response.usage else 0,
            output_tokens=response.usage.output_tokens if response.usage else 0,
        )

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken, falling back to heuristic."""
        try:
            import tiktoken

            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            logger.debug("tiktoken not available, using heuristic fallback")
            if not text:
                return 0
            return max(1, len(text) // 4)

    def get_context_window(self, model: str | None = None) -> int:
        """Return the context window for the given model."""
        return ANTHROPIC_CONTEXT_WINDOWS.get(
            model or DEFAULT_CLAUDE_MODEL, 200_000
        )
