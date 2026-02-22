"""
Ollama LLM Provider - Wraps local Ollama HTTP API.

Implements the LLMProvider interface for Ollama's /api/chat endpoint.
Includes a circuit breaker to fast-fail when Ollama is unreachable.
"""

import json
import logging
from typing import List, Generator, Optional

import requests

from core import config
from core.llm.base import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMStreamChunk,
    ProviderType,
    classify_llm_error,
)
from core.llm.circuit_breaker import CircuitBreaker, CircuitBreakerOpen

logger = logging.getLogger(__name__)

# Module-level singleton so all OllamaProvider instances share state
_ollama_circuit_breaker = CircuitBreaker(
    name="ollama",
    failure_threshold=3,
    recovery_timeout=30.0,
)


def get_ollama_circuit_breaker() -> CircuitBreaker:
    """Expose the circuit breaker for health-check reporting."""
    return _ollama_circuit_breaker


class OllamaProvider(LLMProvider):
    """LLM provider for local Ollama models."""

    provider_type = ProviderType.OLLAMA

    def __init__(self, host: Optional[str] = None) -> None:
        self.host: str = host or config.OLLAMA_HOST
        self._breaker: CircuitBreaker = _ollama_circuit_breaker

    def generate(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> LLMResponse:
        """Non-streaming generation via Ollama /api/chat."""
        self._breaker.pre_request()

        ollama_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        options = {"temperature": temperature, "num_predict": max_tokens}
        if kwargs.get("context_window"):
            options["num_ctx"] = kwargs["context_window"]

        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": model,
                    "messages": ollama_messages,
                    "stream": False,
                    "think": False,
                    "options": options,
                },
                timeout=kwargs.get("timeout", 180),
            )
            response.raise_for_status()
            data = response.json()

            self._breaker.record_success()

            return LLMResponse(
                content=data.get("message", {}).get("content", ""),
                model=model,
                provider=ProviderType.OLLAMA,
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
            )

        except CircuitBreakerOpen:
            raise
        except requests.exceptions.Timeout:
            logger.error(f"Ollama timeout for model {model}")
            self._breaker.record_failure()
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            self._breaker.record_failure()
            raise

    def stream(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> Generator[LLMStreamChunk, None, None]:
        """Streaming generation via Ollama /api/chat."""
        self._breaker.pre_request()

        ollama_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        options = {"temperature": temperature, "num_predict": max_tokens}
        if kwargs.get("context_window"):
            options["num_ctx"] = kwargs["context_window"]

        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": model,
                    "messages": ollama_messages,
                    "stream": True,
                    "think": False,
                    "options": options,
                },
                stream=True,
                timeout=kwargs.get("timeout", 180),
            )
            response.raise_for_status()

            self._breaker.record_success()

            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    done = data.get("done", False)
                    yield LLMStreamChunk(
                        content=token,
                        done=done,
                        input_tokens=(
                            data.get("prompt_eval_count", 0) if done else 0
                        ),
                        output_tokens=(
                            data.get("eval_count", 0) if done else 0
                        ),
                    )
                    if done:
                        break
                except json.JSONDecodeError:
                    continue

        except CircuitBreakerOpen:
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama streaming failed: {e}")
            self._breaker.record_failure()
            error_type, user_msg = classify_llm_error(e)
            yield LLMStreamChunk(
                content=user_msg, done=True,
                is_error=True, error_type=error_type,
            )

    def health_check(self) -> dict:
        """Check Ollama connectivity and circuit breaker state."""
        breaker_status = self._breaker.get_status()

        try:
            response = requests.get(
                f"{self.host}/api/tags", timeout=5
            )
            healthy = response.status_code == 200
            models: List[str] = []
            if healthy:
                data = response.json()
                models = [
                    m.get("name", "") for m in data.get("models", [])
                ]
                self._breaker.record_success()

            return {
                "provider": "ollama",
                "connected": healthy,
                "available_models": models,
                "healthy": healthy,
                "circuit_breaker": breaker_status,
            }
        except Exception as e:
            self._breaker.record_failure()
            return {
                "provider": "ollama",
                "connected": False,
                "error": str(e),
                "healthy": False,
                "circuit_breaker": self._breaker.get_status(),
            }

    def list_models(self) -> List[dict]:
        """List models available in Ollama."""
        try:
            response = requests.get(
                f"{self.host}/api/tags", timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return [
                {
                    "id": m.get("name", ""),
                    "name": m.get("name", ""),
                    "provider": "ollama",
                    "size": m.get("size", 0),
                }
                for m in data.get("models", [])
            ]
        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")
            return []
