"""
LLM Provider Registry - Manages provider instances.

Ollama is a shared singleton (no per-user credentials).
Cloud providers (Anthropic, OpenAI, Custom) are created per-request
via factory to prevent credential leakage between users.
"""

import logging
from typing import Dict, Optional

from core.llm.base import LLMProvider, ProviderType

logger = logging.getLogger(__name__)

# Only Ollama lives here as a singleton; cloud providers are ephemeral
_providers: Dict[ProviderType, LLMProvider] = {}


def register_provider(provider: LLMProvider) -> None:
    """Register a singleton LLM provider (Ollama only)."""
    _providers[provider.provider_type] = provider
    logger.info(f"Registered LLM provider: {provider.provider_type.value}")


def get_provider(provider_type: ProviderType) -> Optional[LLMProvider]:
    """Get a registered singleton provider by type."""
    return _providers.get(provider_type)


def get_default_provider() -> LLMProvider:
    """Get the default (Ollama) provider. Raises if not initialized."""
    provider = _providers.get(ProviderType.OLLAMA)
    if not provider:
        raise RuntimeError("Default LLM provider (Ollama) not initialized")
    return provider


def has_provider(provider_type: ProviderType) -> bool:
    """Check if a singleton provider is registered."""
    return provider_type in _providers


def create_cloud_provider(
    provider_type: ProviderType,
    api_key: str,
    base_url: Optional[str] = None,
) -> LLMProvider:
    """
    Create a new cloud LLM provider instance (per-request).

    This intentionally does NOT store the instance in the global
    registry, so each user gets an isolated provider with their
    own API key. The instance is short-lived and garbage-collected
    after the request completes.

    Args:
        provider_type: ANTHROPIC, OPENAI, or CUSTOM
        api_key: API key for the provider
        base_url: Optional custom endpoint URL (for CUSTOM type)

    Returns:
        A fresh provider instance bound to the caller's API key
    """
    if provider_type == ProviderType.ANTHROPIC:
        from core.llm.anthropic_provider import AnthropicProvider
        provider = AnthropicProvider(api_key=api_key)
    elif provider_type == ProviderType.OPENAI:
        from core.llm.openai_provider import OpenAIProvider
        provider = OpenAIProvider(api_key=api_key)
    elif provider_type == ProviderType.CUSTOM:
        from core.llm.custom_provider import CustomProvider
        provider = CustomProvider(api_key=api_key, base_url=base_url)
    else:
        raise ValueError(f"Unsupported cloud provider: {provider_type}")

    logger.debug(
        f"Created ephemeral cloud provider: {provider_type.value}"
    )
    return provider


def register_cloud_provider(
    provider_type: ProviderType,
    api_key: str,
    base_url: Optional[str] = None,
) -> LLMProvider:
    """
    Backward-compatible wrapper around create_cloud_provider.

    DEPRECATED: Use create_cloud_provider() for new code.
    This no longer stores the provider in the global registry
    to prevent credential leakage between users.
    """
    return create_cloud_provider(provider_type, api_key, base_url)


def initialize_providers() -> None:
    """Initialize default providers at startup."""
    from core.llm.ollama_provider import OllamaProvider

    ollama = OllamaProvider()
    register_provider(ollama)
    logger.info("LLM provider registry initialized (Ollama)")
