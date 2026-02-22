"""
LLM Provider Abstraction Layer.

Provides a unified interface for Ollama, Anthropic, OpenAI,
and custom OpenAI-compatible LLM providers.
"""

from core.llm.base import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMStreamChunk,
    ProviderType,
)
from core.llm.registry import (
    get_provider,
    get_default_provider,
    register_provider,
    create_cloud_provider,
    register_cloud_provider,
    has_provider,
    initialize_providers,
)
