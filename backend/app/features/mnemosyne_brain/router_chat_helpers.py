"""
Mnemosyne Brain Chat - Helper Functions.

Shared utilities for brain chat endpoints.
"""

import json
import logging

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core import config
from features.mnemosyne_brain.models.brain_file import BrainFile
from features.mnemosyne_brain.models.brain_conversation import (
    BrainConversation,
    BrainMessage,
)

logger = logging.getLogger(__name__)

OLLAMA_HOST = config.OLLAMA_HOST


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
    """Non-streaming Ollama call for brain using /api/chat."""
    if model is None:
        model = getattr(config, "BRAIN_MODEL", "llama3.2:3b")
    temperature = getattr(config, "BRAIN_TEMPERATURE", 0.7)

    logger.info(
        f"Brain generate: model={model}, "
        f"system_prompt_len={len(system_prompt)}, prompt_len={len(prompt)}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    options = {"temperature": temperature, "num_predict": 2048}
    if context_window:
        options["num_ctx"] = context_window

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "think": False,
                "options": options,
            },
            timeout=180,
        )
        response.raise_for_status()
        msg = response.json().get("message", {})
        return msg.get("content", "")
    except Exception as e:
        logger.error(f"Ollama brain generate failed: {e}")
        return f"I'm sorry, I couldn't process that right now. ({e})"


def call_ollama_stream(
    prompt: str, system_prompt: str, model: str = None, context_window: int = None,
):
    """Streaming Ollama call for brain using /api/chat."""
    if model is None:
        model = getattr(config, "BRAIN_MODEL", "llama3.2:3b")
    temperature = getattr(config, "BRAIN_TEMPERATURE", 0.7)

    logger.info(
        f"Brain stream: model={model}, "
        f"system_prompt_len={len(system_prompt)}, prompt_len={len(prompt)}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    options = {"temperature": temperature, "num_predict": 2048}
    if context_window:
        options["num_ctx"] = context_window

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": True,
                "think": False,
                "options": options,
            },
            stream=True,
            timeout=180,
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    msg = data.get("message", {})
                    token = msg.get("content", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Ollama brain stream failed: {e}")
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
