"""LLM Router — strategy-based dispatch across multiple providers.

Strategies:
- FASTEST_CHEAPEST: picks the first available provider in fallback order.
- SPECIFIC_PROVIDER: routes to a named provider.
- AUTO_FALLBACK: tries providers in order, falling back on failure.
"""

from __future__ import annotations

import enum
import logging

from app.services.llm.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class RouterStrategy(enum.StrEnum):
    """Routing strategy for LLM requests."""

    FASTEST_CHEAPEST = "fastest_cheapest"
    SPECIFIC_PROVIDER = "specific_provider"
    AUTO_FALLBACK = "auto_fallback"


# Default order in which providers are tried during fallback.
DEFAULT_FALLBACK_ORDER = ["openrouter", "openai", "anthropic"]


class LLMRouter:
    """Routes LLM requests to registered providers based on strategy."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseLLMProvider] = {}
        self._fallback_order: list[str] = list(DEFAULT_FALLBACK_ORDER)

    @property
    def providers(self) -> dict[str, BaseLLMProvider]:
        return self._providers

    @property
    def fallback_order(self) -> list[str]:
        return self._fallback_order

    def register_provider(self, name: str, provider: BaseLLMProvider) -> None:
        """Register a provider under a logical name."""
        self._providers[name] = provider

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        strategy: RouterStrategy = RouterStrategy.AUTO_FALLBACK,
        preferred_provider: str | None = None,
        preferred_model: str | None = None,
    ) -> LLMResponse:
        """Generate a completion using the selected strategy.

        Args:
            prompt: The user prompt.
            system: Optional system instruction.
            strategy: Routing strategy (default: AUTO_FALLBACK).
            preferred_provider: Provider name for SPECIFIC_PROVIDER.
            preferred_model: Model override for any provider.

        Returns:
            LLMResponse from the selected provider.

        Raises:
            ValueError: If strategy is unknown or no providers are registered.
        """
        if not self._providers:
            raise ValueError(
                "No providers registered — call register_provider first"
            )

        if strategy == RouterStrategy.FASTEST_CHEAPEST:
            return await self._dispatch_fastest_cheapest(prompt, system, preferred_model)
        elif strategy == RouterStrategy.SPECIFIC_PROVIDER:
            return await self._dispatch_specific(
                prompt, system, preferred_provider, preferred_model
            )
        elif strategy == RouterStrategy.AUTO_FALLBACK:
            return await self._dispatch_auto_fallback(
                prompt, system, preferred_model
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    async def _dispatch_fastest_cheapest(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
    ) -> LLMResponse:
        """Pick the first available provider in fallback order."""
        errors: list[tuple[str, str]] = []
        for name in self._fallback_order:
            provider = self._providers.get(name)
            if provider is None:
                continue
            try:
                return await provider.generate(
                    prompt=prompt, system=system, model=model
                )
            except Exception as exc:
                errors.append((name, str(exc)))
                logger.warning("Fastest/cheapest: %s failed: %s", name, exc)
                continue

        raise RuntimeError(
            f"No provider available. Errors: {errors}"
        )

    async def _dispatch_specific(
        self,
        prompt: str,
        system: str | None = None,
        provider_name: str | None = None,
        model: str | None = None,
    ) -> LLMResponse:
        """Route to a specific named provider."""
        if provider_name is None:
            raise ValueError(
                "preferred_provider is required for SPECIFIC_PROVIDER strategy"
            )
        provider = self._providers.get(provider_name)
        if provider is None:
            raise ValueError(
                f"Provider '{provider_name}' is not registered"
            )
        return await provider.generate(
            prompt=prompt, system=system, model=model
        )

    async def _dispatch_auto_fallback(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
    ) -> LLMResponse:
        """Try providers in fallback order, moving to the next on failure."""
        errors: list[tuple[str, str]] = []
        for name in self._fallback_order:
            provider = self._providers.get(name)
            if provider is None:
                continue
            try:
                return await provider.generate(
                    prompt=prompt, system=system, model=model
                )
            except Exception as exc:
                errors.append((name, str(exc)))
                logger.warning("Fallback: %s failed: %s", name, exc)
                continue

        raise RuntimeError(
            f"All providers exhausted. Errors: {errors}"
        )
