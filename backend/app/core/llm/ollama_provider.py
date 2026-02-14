"""
Ollama LLM Provider - Wraps local Ollama HTTP API.

Implements the LLMProvider interface for Ollama's /api/chat endpoint.
"""

import json
import logging
from typing import List, Generator

import requests

from core import config
from core.llm.base import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMStreamChunk,
    ProviderType,
)

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """LLM provider for local Ollama models."""

    provider_type = ProviderType.OLLAMA

    def __init__(self, host: str = None):
        self.host = host or config.OLLAMA_HOST

    def generate(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> LLMResponse:
        """Non-streaming generation via Ollama /api/chat."""
        ollama_messages = [{"role": m.role, "content": m.content} for m in messages]

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

            content = data.get("message", {}).get("content", "")
            input_tokens = data.get("prompt_eval_count", 0)
            output_tokens = data.get("eval_count", 0)

            return LLMResponse(
                content=content,
                model=model,
                provider=ProviderType.OLLAMA,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

        except requests.exceptions.Timeout:
            logger.error(f"Ollama timeout for model {model}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
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
        ollama_messages = [{"role": m.role, "content": m.content} for m in messages]

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
                        input_tokens=data.get("prompt_eval_count", 0) if done else 0,
                        output_tokens=data.get("eval_count", 0) if done else 0,
                    )
                    if done:
                        break
                except json.JSONDecodeError:
                    continue

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama streaming failed: {e}")
            yield LLMStreamChunk(content=f"[ERROR: {e}]", done=True)

    def health_check(self) -> dict:
        """Check Ollama connectivity and available models."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            healthy = response.status_code == 200
            models = []
            if healthy:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]

            return {
                "provider": "ollama",
                "connected": healthy,
                "available_models": models,
                "healthy": healthy,
            }
        except Exception as e:
            return {
                "provider": "ollama",
                "connected": False,
                "error": str(e),
                "healthy": False,
            }

    def list_models(self) -> List[dict]:
        """List models available in Ollama."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
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
