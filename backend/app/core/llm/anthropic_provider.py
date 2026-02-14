"""
Anthropic LLM Provider - Claude API integration.

Implements the LLMProvider interface for Anthropic's Messages API.
"""

import logging
import time
from typing import List, Generator

from core.llm.base import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMStreamChunk,
    ProviderType,
)

logger = logging.getLogger(__name__)

ANTHROPIC_MODELS = [
    {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "context": 200000},
    {"id": "claude-opus-4-0520", "name": "Claude Opus 4", "context": 200000},
    {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5", "context": 200000},
    {"id": "claude-sonnet-4-5-20250929", "name": "Claude Sonnet 4.5", "context": 200000},
]


class AnthropicProvider(LLMProvider):
    """LLM provider for Anthropic Claude models."""

    provider_type = ProviderType.ANTHROPIC

    def __init__(self, api_key: str):
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package required: pip install anthropic")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.api_key = api_key

    def generate(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> LLMResponse:
        """Non-streaming generation via Anthropic Messages API."""
        system_prompt, api_messages = self._prepare_messages(messages)

        try:
            params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": api_messages,
            }
            if system_prompt:
                params["system"] = system_prompt

            response = self.client.messages.create(**params)

            content = ""
            for block in response.content:
                if block.type == "text":
                    content += block.text

            return LLMResponse(
                content=content,
                model=model,
                provider=ProviderType.ANTHROPIC,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

        except Exception as e:
            logger.error(f"Anthropic generate failed: {e}")
            raise

    def stream(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> Generator[LLMStreamChunk, None, None]:
        """Streaming generation via Anthropic Messages API."""
        system_prompt, api_messages = self._prepare_messages(messages)

        try:
            params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": api_messages,
            }
            if system_prompt:
                params["system"] = system_prompt

            with self.client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield LLMStreamChunk(content=text, done=False)

                final = stream.get_final_message()
                yield LLMStreamChunk(
                    content="",
                    done=True,
                    input_tokens=final.usage.input_tokens,
                    output_tokens=final.usage.output_tokens,
                )

        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            yield LLMStreamChunk(content=f"[ERROR: {e}]", done=True)

    def health_check(self) -> dict:
        """Verify Anthropic API key is valid."""
        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return {
                "provider": "anthropic",
                "connected": True,
                "healthy": True,
            }
        except Exception as e:
            return {
                "provider": "anthropic",
                "connected": False,
                "error": str(e),
                "healthy": False,
            }

    def list_models(self) -> List[dict]:
        """Return static list of Anthropic models."""
        return [
            {**m, "provider": "anthropic"}
            for m in ANTHROPIC_MODELS
        ]

    @staticmethod
    def _prepare_messages(messages: List[LLMMessage]):
        """Extract system prompt and convert to Anthropic format."""
        system_prompt = ""
        api_messages = []

        for msg in messages:
            if msg.role == "system":
                system_prompt += msg.content + "\n"
            else:
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        # Ensure at least one user message
        if not api_messages:
            api_messages.append({"role": "user", "content": "Hello"})

        return system_prompt.strip(), api_messages
