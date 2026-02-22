"""
OpenAI LLM Provider - ChatGPT API integration.

Implements the LLMProvider interface for OpenAI's Chat Completions API.
Also serves as the base for custom OpenAI-compatible endpoints.
"""

import logging
from typing import List, Generator, Optional

from core.llm.base import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMStreamChunk,
    ProviderType,
    classify_llm_error,
)

logger = logging.getLogger(__name__)

OPENAI_MODELS = [
    {"id": "gpt-4o", "name": "GPT-4o", "context": 128000},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context": 128000},
    {"id": "o1", "name": "o1", "context": 200000},
    {"id": "o3-mini", "name": "o3-mini", "context": 200000},
    {"id": "gpt-4.1", "name": "GPT-4.1", "context": 1000000},
    {"id": "gpt-4.1-mini", "name": "GPT-4.1 Mini", "context": 1000000},
]


class OpenAIProvider(LLMProvider):
    """LLM provider for OpenAI ChatGPT models."""

    provider_type = ProviderType.OPENAI

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        try:
            import openai
        except ImportError:
            raise ImportError("openai package required: pip install openai")
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = openai.OpenAI(**kwargs)
        self.api_key = api_key
        self.base_url = base_url

    def generate(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> LLMResponse:
        """Non-streaming generation via OpenAI Chat Completions."""
        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            choice = response.choices[0]
            usage = response.usage

            return LLMResponse(
                content=choice.message.content or "",
                model=model,
                provider=self.provider_type,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            )

        except Exception as e:
            logger.error(f"OpenAI generate failed: {e}")
            raise

    def stream(
        self,
        messages: List[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> Generator[LLMStreamChunk, None, None]:
        """Streaming generation via OpenAI Chat Completions."""
        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                stream_options={"include_usage": True},
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield LLMStreamChunk(
                        content=chunk.choices[0].delta.content,
                        done=False,
                    )
                # Final chunk with usage info
                if chunk.usage:
                    yield LLMStreamChunk(
                        content="",
                        done=True,
                        input_tokens=chunk.usage.prompt_tokens,
                        output_tokens=chunk.usage.completion_tokens,
                    )

        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            error_type, user_msg = classify_llm_error(e)
            yield LLMStreamChunk(
                content=user_msg, done=True,
                is_error=True, error_type=error_type,
            )

    def health_check(self) -> dict:
        """Verify OpenAI API key is valid."""
        try:
            self.client.models.list()
            return {
                "provider": "openai",
                "connected": True,
                "healthy": True,
            }
        except Exception as e:
            return {
                "provider": "openai",
                "connected": False,
                "error": str(e),
                "healthy": False,
            }

    def list_models(self) -> List[dict]:
        """Return static list of OpenAI models."""
        return [
            {**m, "provider": "openai"}
            for m in OPENAI_MODELS
        ]
