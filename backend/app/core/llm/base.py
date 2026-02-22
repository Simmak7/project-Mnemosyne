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
    is_error: bool = False
    error_type: Optional[str] = None


# User-friendly error messages by error type
ERROR_MESSAGES = {
    "connection": "AI service is temporarily unavailable. Please try again in a moment.",
    "timeout": "The AI took too long to respond. Try a shorter question or try again.",
    "model_unavailable": "The selected AI model is not available. Check Settings > AI Models.",
    "cloud_fallback": "Cloud AI unavailable, using local AI instead.",
    "unknown": "Something went wrong with the AI service. Please try again.",
}


def classify_llm_error(error: Exception) -> tuple[str, str]:
    """Classify an LLM exception into (error_type, user_message)."""
    import requests

    error_str = str(error).lower()

    if isinstance(error, requests.exceptions.Timeout):
        return "timeout", ERROR_MESSAGES["timeout"]
    if isinstance(error, requests.exceptions.ConnectionError):
        return "connection", ERROR_MESSAGES["connection"]
    if "connection" in error_str or "refused" in error_str:
        return "connection", ERROR_MESSAGES["connection"]
    if "timeout" in error_str or "timed out" in error_str:
        return "timeout", ERROR_MESSAGES["timeout"]
    if "not found" in error_str or "does not exist" in error_str:
        return "model_unavailable", ERROR_MESSAGES["model_unavailable"]

    return "unknown", ERROR_MESSAGES["unknown"]


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
