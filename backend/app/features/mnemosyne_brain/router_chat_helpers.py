"""
Mnemosyne Brain Chat - Helper Functions.

Shared utilities for brain chat endpoints.
"""

import json
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core import config
from core.llm import get_default_provider, LLMMessage
from features.mnemosyne_brain.models.brain_file import BrainFile
from features.mnemosyne_brain.models.brain_conversation import (
    BrainConversation,
    BrainMessage,
)

logger = logging.getLogger(__name__)


def generate_conversation_title(query: str, max_length: int = 50) -> str:
    """Generate a conversation title from the query."""
    title = query.strip()
    prefixes = [
        "what do i know about ", "what do you know about ",
        "tell me about ", "can you tell me about ",
        "explain ", "describe ", "how does ", "what is ",
    ]
    lower = title.lower()
    for prefix in prefixes:
        if lower.startswith(prefix):
            title = title[len(prefix):]
            break
    title = title.strip().rstrip("?!.")
    if len(title) > max_length:
        cut = title[:max_length].rfind(" ")
        title = title[:cut] + "..." if cut > 10 else title[:max_length] + "..."
    return title.capitalize() if title else "Brain Chat"


def check_brain_ready(db: Session, user_id: int):
    """Verify the brain has been built."""
    core_count = (
        db.query(BrainFile)
        .filter(
            BrainFile.owner_id == user_id,
            BrainFile.file_type == "core",
        )
        .count()
    )
    if core_count < 2:
        raise HTTPException(
            status_code=400,
            detail="Brain not built yet. Use POST /mnemosyne/build first.",
        )


def is_brain_stale(db: Session, user_id: int) -> bool:
    """Check if any brain files are marked as stale."""
    stale_count = (
        db.query(BrainFile)
        .filter(
            BrainFile.owner_id == user_id,
            BrainFile.is_stale == True,
        )
        .count()
    )
    return stale_count > 0


def get_query_embedding(query: str):
    """Generate query embedding, return None on failure."""
    try:
        from embeddings import generate_embedding
        return generate_embedding(query)
    except Exception:
        return None


def call_ollama_generate(
    prompt: str, system_prompt: str, model: str = None, context_window: int = None,
) -> str:
    """Non-streaming LLM call for brain using provider abstraction."""
    if model is None:
        model = getattr(config, "BRAIN_MODEL", "llama3.2:3b")
    temperature = getattr(config, "BRAIN_TEMPERATURE", 0.7)

    logger.info(
        f"Brain generate: model={model}, "
        f"system_prompt_len={len(system_prompt)}, prompt_len={len(prompt)}"
    )

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=prompt),
    ]

    try:
        provider = get_default_provider()
        response = provider.generate(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=2048,
            context_window=context_window,
            timeout=180,
        )
        return response.content
    except Exception as e:
        logger.error(f"Brain generate failed: {e}")
        return f"I'm sorry, I couldn't process that right now. ({e})"


def call_ollama_stream(
    prompt: str, system_prompt: str, model: str = None, context_window: int = None,
):
    """Streaming LLM call for brain using provider abstraction."""
    if model is None:
        model = getattr(config, "BRAIN_MODEL", "llama3.2:3b")
    temperature = getattr(config, "BRAIN_TEMPERATURE", 0.7)

    logger.info(
        f"Brain stream: model={model}, "
        f"system_prompt_len={len(system_prompt)}, prompt_len={len(prompt)}"
    )

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=prompt),
    ]

    try:
        provider = get_default_provider()
        for chunk in provider.stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=2048,
            context_window=context_window,
            timeout=180,
        ):
            if chunk.content:
                yield chunk.content
            if chunk.done:
                break
    except Exception as e:
        logger.error(f"Brain stream failed: {e}")
        yield f"[ERROR: {e}]"


def get_previous_topics(db: Session, user_id: int, conversation_id) -> list:
    """Extract topic file keys from the last assistant message in a conversation."""
    if not conversation_id:
        return []
    last_msg = (
        db.query(BrainMessage)
        .join(BrainConversation)
        .filter(
            BrainMessage.conversation_id == conversation_id,
            BrainConversation.owner_id == user_id,
            BrainMessage.role == "assistant",
            BrainMessage.brain_files_loaded.isnot(None),
        )
        .order_by(BrainMessage.created_at.desc())
        .first()
    )
    if not last_msg or not last_msg.brain_files_loaded:
        return []
    return [k for k in last_msg.brain_files_loaded if k.startswith("topic_")]
