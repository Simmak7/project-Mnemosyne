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


def call_ollama_generate(prompt: str, system_prompt: str, model: str = None) -> str:
    """Non-streaming Ollama call for brain."""
    if model is None:
        model = getattr(config, "BRAIN_MODEL", "llama3.2:3b")
    temperature = getattr(config, "BRAIN_TEMPERATURE", 0.7)

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "think": False,
                "options": {"temperature": temperature, "num_predict": 1024},
            },
            timeout=180,
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        logger.error(f"Ollama brain generate failed: {e}")
        return f"I'm sorry, I couldn't process that right now. ({e})"


def call_ollama_stream(prompt: str, system_prompt: str, model: str = None):
    """Streaming Ollama call for brain."""
    if model is None:
        model = getattr(config, "BRAIN_MODEL", "llama3.2:3b")
    temperature = getattr(config, "BRAIN_TEMPERATURE", 0.7)

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": True,
                "think": False,
                "options": {"temperature": temperature, "num_predict": 1024},
            },
            stream=True,
            timeout=180,
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
    except Exception as e:
        logger.error(f"Ollama brain stream failed: {e}")
        yield f"[ERROR: {e}]"
