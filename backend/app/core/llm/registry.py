"""
LLM Provider Registry - Singleton registry for provider instances.

Manages initialization and access to LLM providers.
"""

import logging
from typing import Dict, Optional

from core.llm.base import LLMProvider, ProviderType

logger = logging.getLogger(__name__)

_providers: Dict[ProviderType, LLMProvider] = {}


def register_provider(provider: LLMProvider) -> None:
    """Register an LLM provider instance."""
    _providers[provider.provider_type] = provider
    logger.info(f"Registered LLM provider: {provider.provider_type.value}")


def get_provider(provider_type: ProviderType) -> Optional[LLMProvider]:
    """Get a registered provider by type."""
    return _providers.get(provider_type)


def get_default_provider() -> LLMProvider:
    """Get the default (Ollama) provider. Raises if not initialized."""
    provider = _providers.get(ProviderType.OLLAMA)
    if not provider:
        raise RuntimeError("Default LLM provider (Ollama) not initialized")
    return provider


def has_provider(provider_type: ProviderType) -> bool:
    """Check if a provider is registered."""
    return provider_type in _providers


def register_cloud_provider(
    provider_type: ProviderType,
    api_key: str,
    base_url: str = None,
) -> LLMProvider:
    """
    Register a cloud LLM provider with an API key.

    Args:
        provider_type: ANTHROPIC, OPENAI, or CUSTOM
        api_key: API key for the provider
        base_url: Optional custom endpoint URL (for CUSTOM type)

    Returns:
        The registered provider instance
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

    register_provider(provider)
    return provider


def initialize_providers() -> None:
    """Initialize default providers at startup."""
    from core.llm.ollama_provider import OllamaProvider

    ollama = OllamaProvider()
    register_provider(ollama)
    logger.info("LLM provider registry initialized (Ollama)")
