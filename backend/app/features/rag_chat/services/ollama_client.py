"""
Ollama API client functions for RAG text generation.

Provides synchronous and streaming interfaces via the LLM provider abstraction.
"""

import logging
from typing import Generator

from fastapi import HTTPException
import requests

from core import config
from core.llm import get_default_provider, LLMMessage, ProviderType

logger = logging.getLogger(__name__)

# Ollama configuration
RAG_MODEL = config.RAG_MODEL
RAG_TIMEOUT = config.RAG_TIMEOUT
RAG_TEMPERATURE = config.RAG_TEMPERATURE


def call_ollama_generate(
    prompt: str,
    system_prompt: str,
    model: str = None,
    timeout: int = None
) -> str:
    """
    Call LLM provider for text generation.

    Args:
        prompt: User prompt with context
        system_prompt: System instructions
        model: Model name to use (defaults to RAG_MODEL)
        timeout: Request timeout (defaults to RAG_TIMEOUT)

    Returns:
        Generated response text

    Raises:
        HTTPException: If LLM call fails
    """
    model = model or RAG_MODEL
    timeout = timeout or RAG_TIMEOUT

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=prompt),
    ]

    try:
        provider = get_default_provider()
        response = provider.generate(
            messages=messages,
            model=model,
            temperature=RAG_TEMPERATURE,
            max_tokens=1024,
            timeout=timeout,
        )
        return response.content

    except requests.exceptions.Timeout:
        logger.error(f"LLM timeout after {timeout}s")
        raise HTTPException(503, "AI service timeout. Please try again.")
    except Exception as e:
        logger.error(f"LLM request failed: {e}")
        raise HTTPException(503, "AI service unavailable. Please try again later.")


def call_ollama_stream(
    prompt: str,
    system_prompt: str,
    model: str = None,
    timeout: int = None
) -> Generator[str, None, None]:
    """
    Stream tokens from LLM provider.

    Args:
        prompt: User prompt with context
        system_prompt: System instructions
        model: Model name to use (defaults to RAG_MODEL)
        timeout: Request timeout (defaults to RAG_TIMEOUT)

    Yields:
        Token strings as they're generated
    """
    model = model or RAG_MODEL
    timeout = timeout or RAG_TIMEOUT

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=prompt),
    ]

    try:
        provider = get_default_provider()
        for chunk in provider.stream(
            messages=messages,
            model=model,
            temperature=RAG_TEMPERATURE,
            max_tokens=1024,
            timeout=timeout,
        ):
            if chunk.content:
                yield chunk.content
            if chunk.done:
                break

    except Exception as e:
        logger.error(f"LLM streaming failed: {e}")
        yield "[ERROR: AI service unavailable]"


def check_ollama_health() -> dict:
    """
    Check LLM service health and model availability.

    Returns:
        Dict with health status, available models, and connectivity info
    """
    try:
        provider = get_default_provider()
        health = provider.health_check()

        models = health.get("available_models", [])
        has_rag_model = any(RAG_MODEL in m for m in models)
        has_embedding_model = any("nomic-embed" in m for m in models)

        return {
            "connected": health.get("connected", False),
            "rag_model": RAG_MODEL,
            "rag_model_available": has_rag_model,
            "embedding_model_available": has_embedding_model,
            "available_models": models,
            "healthy": health.get("connected", False) and has_rag_model and has_embedding_model,
        }

    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "healthy": False,
        }
