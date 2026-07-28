"""Base LLM provider abstraction.

Defines the LLMResponse model and the abstract BaseLLMProvider interface
that all LLM providers must implement.
"""

from __future__ import annotations

import abc

from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Standardised response from any LLM provider."""

    text: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int


class BaseLLMProvider(abc.ABC):
    """Abstract base class for all LLM providers.

    Subclasses must implement: generate, count_tokens, get_context_window.
    """

    @abc.abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a completion from the LLM.

        Args:
            prompt: The user prompt / message text.
            system: Optional system instruction.
            model: Model identifier (None = provider default).
            max_tokens: Maximum tokens in the response (default 2048).
            temperature: Sampling temperature (default 0.7).

        Returns:
            LLMResponse with the generated text and usage metadata.
        """
        ...

    @abc.abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Args:
            text: The input text.

        Returns:
            Token count as int.
        """
        ...

    @abc.abstractmethod
    def get_context_window(self, model: str) -> int:
        """Return the context window size for a given model.

        Args:
            model: Model identifier.

        Returns:
            Maximum context size in tokens.
        """
        ...
