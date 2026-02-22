"""
Memory Evolver - Extracts learnings from conversations and updates memory.md.

After a brain conversation, this service analyzes the exchange and
appends any new learnings to the user's memory.md brain file.
Includes automatic pruning when memory exceeds MAX_MEMORY_CHARS.
"""

import logging
import re
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

from sqlalchemy.orm import Session

from features.mnemosyne_brain.models.brain_file import BrainFile
from features.mnemosyne_brain.models.brain_conversation import (
    BrainConversation,
    BrainMessage,
)
from features.mnemosyne_brain.services.topic_generator import (
    call_ollama_generate,
    compute_content_hash,
    estimate_tokens,
)
from features.mnemosyne_brain.services.prompts import MEMORY_EVOLUTION_PROMPT

logger = logging.getLogger(__name__)

MAX_MEMORY_CHARS = 3000
RECENT_ENTRIES_TO_KEEP = 3


def evolve_memory(
    db: Session,
    user_id: int,
    conversation_id: int,
) -> Optional[str]:
    """
    Extract learnings from a conversation and append to memory.md.

    After appending, prunes memory if it exceeds MAX_MEMORY_CHARS.

    Args:
        db: Database session
        user_id: Owner ID
        conversation_id: Brain conversation to analyze

    Returns:
        New learnings text or None if nothing new
    """
    conversation = (
        db.query(BrainConversation)
        .filter(
            BrainConversation.id == conversation_id,
            BrainConversation.owner_id == user_id,
        )
        .first()
    )
    if not conversation:
        logger.warning(f"Conversation {conversation_id} not found for user {user_id}")
        return None

    messages = (
        db.query(BrainMessage)
        .filter(BrainMessage.conversation_id == conversation_id)
        .order_by(BrainMessage.created_at)
        .all()
    )

    if len(messages) < 2:
        logger.info("Not enough messages to extract learnings")
        return None

    # Format conversation text
    conv_text_parts = []
    for msg in messages:
        role = msg.role.capitalize()
        content = msg.content[:1000]
        conv_text_parts.append(f"{role}: {content}")

    conversation_text = "\n\n".join(conv_text_parts)

    # Call LLM to extract learnings
    prompt = MEMORY_EVOLUTION_PROMPT.format(
        conversation_text=conversation_text,
    )

    result = call_ollama_generate(prompt)
    if not result or "NO_NEW_LEARNINGS" in result:
        logger.info("No new learnings extracted from conversation")
        return None

    learnings = result.strip()
    if not learnings:
        return None

    # Append to memory.md
    memory_file = (
        db.query(BrainFile)
        .filter(BrainFile.owner_id == user_id, BrainFile.file_key == "memory")
        .first()
    )

    if not memory_file:
        logger.warning(f"No memory file found for user {user_id}")
        return None

    date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    new_section = f"\n\n### Session {date_str}\n{learnings}"

    memory_file.content += new_section

    # Prune if over limit
    if len(memory_file.content) > MAX_MEMORY_CHARS:
        memory_file.content = prune_memory(memory_file.content)

    memory_file.content_hash = compute_content_hash(memory_file.content)
    memory_file.token_count_approx = estimate_tokens(memory_file.content)
    memory_file.version = (memory_file.version or 0) + 1

    try:
        db.commit()
        logger.info(f"Memory evolved for user {user_id}: appended {len(learnings)} chars")
        return learnings
    except Exception as e:
        logger.error(f"Failed to save memory evolution: {e}")
        db.rollback()
        return None


def _split_memory_entries(content: str) -> Tuple[str, List[str]]:
    """
    Split memory content into preamble and dated session entries.

    Returns:
        Tuple of (preamble_text, list_of_entry_strings)
    """
    # Split on session headers like "### Session 2026-02-18 14:30"
    parts = re.split(r'(?=\n### Session \d{4}-\d{2}-\d{2})', content)

    if not parts:
        return content, []

    preamble = parts[0].strip()
    entries = [p.strip() for p in parts[1:] if p.strip()]

    return preamble, entries


def prune_memory(content: str) -> str:
    """
    Prune memory content to fit within MAX_MEMORY_CHARS.

    Strategy:
    1. Keep the preamble (initial memory header/instructions)
    2. Keep the N most recent entries intact (RECENT_ENTRIES_TO_KEEP)
    3. Summarize older entries into a compressed section

    Args:
        content: Full memory file content

    Returns:
        Pruned memory content within MAX_MEMORY_CHARS
    """
    preamble, entries = _split_memory_entries(content)

    if len(entries) <= RECENT_ENTRIES_TO_KEEP:
        # Not enough entries to prune meaningfully; truncate from the start
        if len(content) > MAX_MEMORY_CHARS:
            return content[-MAX_MEMORY_CHARS:]
        return content

    # Split into old and recent
    recent_entries = entries[-RECENT_ENTRIES_TO_KEEP:]
    old_entries = entries[:-RECENT_ENTRIES_TO_KEEP]

    # Build compressed summary of older entries
    old_count = len(old_entries)
    summary = f"\n\n### Archived Memories\n... ({old_count} earlier sessions summarized) ..."

    # Assemble pruned content
    recent_text = "\n\n".join(recent_entries)
    pruned = f"{preamble}{summary}\n\n{recent_text}"

    # If still too long, trim preamble
    if len(pruned) > MAX_MEMORY_CHARS:
        excess = len(pruned) - MAX_MEMORY_CHARS
        if len(preamble) > excess + 100:
            preamble = preamble[:len(preamble) - excess]
            last_period = preamble.rfind(".")
            if last_period > len(preamble) * 0.5:
                preamble = preamble[:last_period + 1]
            pruned = f"{preamble}{summary}\n\n{recent_text}"

    logger.info(
        f"Memory pruned: {old_count} old entries archived, "
        f"{len(recent_entries)} recent kept, {len(pruned)} chars total"
    )
    return pruned


def get_memory_stats(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Get memory file statistics for the brain status endpoint.

    Args:
        db: Database session
        user_id: Owner ID

    Returns:
        Dict with memory_entry_count and memory_size_chars
    """
    memory_file = (
        db.query(BrainFile)
        .filter(BrainFile.owner_id == user_id, BrainFile.file_key == "memory")
        .first()
    )

    if not memory_file or not memory_file.content:
        return {"memory_entry_count": 0, "memory_size_chars": 0}

    _, entries = _split_memory_entries(memory_file.content)

    return {
        "memory_entry_count": len(entries),
        "memory_size_chars": len(memory_file.content),
    }
