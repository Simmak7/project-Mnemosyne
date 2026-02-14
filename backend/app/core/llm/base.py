"""
LLM Provider Abstraction Layer - Base types and interfaces.

Defines the contract all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Generator, Any


class ProviderType(str, Enum):
    """Supported LLM provider types."""
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    CUSTOM = "custom"


@dataclass
class LLMMessage:
    """A single message in a conversation."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Non-streaming response from an LLM provider."""
    content: str
    model: str
    provider: ProviderType
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class LLMStreamChunk:
    """A single chunk from a streaming LLM response."""
    content: str
    done: bool = False
    input_tokens: int = 0
    output_tokens: int = 0


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    provider_type: ProviderType

    @abstractmethod
    def generate(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> LLMResponse:
        """Generate a complete response (non-streaming)."""
        ...

    @abstractmethod
    def stream(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> Generator[LLMStreamChunk, None, None]:
        """Stream response chunks."""
        ...

    @abstractmethod
    def health_check(self) -> dict:
        """Check provider connectivity and return status."""
        ...

    @abstractmethod
    def list_models(self) -> List[dict]:
        """List available models from this provider."""
        ...
