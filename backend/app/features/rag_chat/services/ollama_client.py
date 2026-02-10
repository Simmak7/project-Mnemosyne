"""
Ollama API client functions for RAG text generation.

Provides synchronous and streaming interfaces to the Ollama API.
"""

import json
import logging
from typing import Generator

import requests
from fastapi import HTTPException

from core import config

logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_HOST = config.OLLAMA_HOST
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
    Call Ollama API for text generation.

    Args:
        prompt: User prompt with context
        system_prompt: System instructions
        model: Model name to use (defaults to RAG_MODEL)
        timeout: Request timeout (defaults to RAG_TIMEOUT)

    Returns:
        Generated response text

    Raises:
        HTTPException: If Ollama call fails
    """
    model = model or RAG_MODEL
    timeout = timeout or RAG_TIMEOUT

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "think": False,
                "options": {
                    "temperature": RAG_TEMPERATURE,
                    "num_predict": 1024,
                }
            },
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    except requests.exceptions.Timeout:
        logger.error(f"Ollama timeout after {timeout}s")
        raise HTTPException(503, "AI service timeout. Please try again.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama request failed: {e}")
        raise HTTPException(503, "AI service unavailable. Please try again later.")


def call_ollama_stream(
    prompt: str,
    system_prompt: str,
    model: str = None,
    timeout: int = None
) -> Generator[str, None, None]:
    """
    Stream tokens from Ollama API.

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

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": True,
                "think": False,
                "options": {
                    "temperature": RAG_TEMPERATURE,
                    "num_predict": 1024,
                }
            },
            stream=True,
            timeout=timeout
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue

    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama streaming failed: {e}")
        yield "[ERROR: AI service unavailable]"


def check_ollama_health() -> dict:
    """
    Check Ollama service health and model availability.

    Returns:
        Dict with health status, available models, and connectivity info
    """
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        ollama_healthy = response.status_code == 200

        models = []
        if ollama_healthy:
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]

        has_rag_model = any(RAG_MODEL in m for m in models)
        has_embedding_model = any("nomic-embed" in m for m in models)

        return {
            "connected": ollama_healthy,
            "rag_model": RAG_MODEL,
            "rag_model_available": has_rag_model,
            "embedding_model_available": has_embedding_model,
            "available_models": models,
            "healthy": ollama_healthy and has_rag_model and has_embedding_model
        }

    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "healthy": False
        }
