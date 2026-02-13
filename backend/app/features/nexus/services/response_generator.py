"""
Stage 3: LLM Response Generator

Generates NEXUS responses using the graph-aware context.
Supports both blocking and streaming modes.
"""

import logging
from typing import Generator, Optional

from features.rag_chat.services.ollama_client import (
    call_ollama_generate,
    call_ollama_stream,
)
from features.rag_chat.services.prompts import extract_confidence_signals
from features.rag_chat.services.context_builder import extract_citations_from_response
from .prompts import (
    NEXUS_SYSTEM_PROMPT,
    NEXUS_SYSTEM_PROMPT_CONCISE,
    format_nexus_user_message,
)
from .context_builder import NexusAssembledContext

logger = logging.getLogger(__name__)


def generate_nexus_response(
    query: str,
    context: NexusAssembledContext,
    model: str,
    conversation_history: str = "",
    fallback_model: str = None,
) -> dict:
    """
    Generate a complete NEXUS response (blocking) with model fallback.
    """
    if not context.rich_citations:
        system_prompt = NEXUS_SYSTEM_PROMPT_CONCISE
        user_message = query
    else:
        system_prompt = NEXUS_SYSTEM_PROMPT
        user_message = format_nexus_user_message(
            query=query,
            context=context.formatted_context,
            conversation_history=conversation_history,
        )

    try:
        answer = call_ollama_generate(
            prompt=user_message, system_prompt=system_prompt, model=model,
        )
    except Exception:
        if fallback_model and fallback_model != model:
            logger.warning(f"Model {model} failed, falling back to {fallback_model}")
            answer = call_ollama_generate(
                prompt=user_message, system_prompt=system_prompt,
                model=fallback_model,
            )
        else:
            raise

    confidence = extract_confidence_signals(answer)
    used_indices = extract_citations_from_response(
        answer,
        [_citation_to_source(c) for c in context.rich_citations],
    )

    return {
        "answer": answer,
        "confidence": confidence,
        "used_indices": used_indices,
    }


def stream_nexus_response(
    query: str,
    context: NexusAssembledContext,
    model: str,
    conversation_history: str = "",
    fallback_model: str = None,
) -> Generator[str, None, None]:
    """
    Stream NEXUS response tokens with automatic model fallback.

    If the primary model fails (e.g. Ollama 500), retries with fallback_model.
    """
    if not context.rich_citations:
        system_prompt = NEXUS_SYSTEM_PROMPT_CONCISE
        user_message = query
    else:
        system_prompt = NEXUS_SYSTEM_PROMPT
        user_message = format_nexus_user_message(
            query=query,
            context=context.formatted_context,
            conversation_history=conversation_history,
        )

    # Try primary model, detect errors, and fallback if needed
    for token in call_ollama_stream(
        prompt=user_message, system_prompt=system_prompt, model=model,
    ):
        if token.startswith("[ERROR:") and fallback_model and fallback_model != model:
            logger.warning(f"Model {model} failed, falling back to {fallback_model}")
            yield from call_ollama_stream(
                prompt=user_message, system_prompt=system_prompt,
                model=fallback_model,
            )
            return
        yield token


def _citation_to_source(citation):
    """Convert NexusRichCitation to a duck-typed object with .index."""
    class _Source:
        def __init__(self, index):
            self.index = index
    return _Source(citation.index)
