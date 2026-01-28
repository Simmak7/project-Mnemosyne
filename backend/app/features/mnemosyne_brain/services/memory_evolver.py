"""
Memory Evolver - Extracts learnings from conversations and updates memory.md.

After a brain conversation, this service analyzes the exchange and
appends any new learnings to the user's memory.md brain file.
"""

import logging
from datetime import datetime
from typing import Optional

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


def evolve_memory(
    db: Session,
    user_id: int,
    conversation_id: int,
) -> Optional[str]:
    """
    Extract learnings from a conversation and append to memory.md.

    Args:
        db: Database session
        user_id: Owner ID
        conversation_id: Brain conversation to analyze

    Returns:
        New learnings text or None if nothing new
    """
    # Load conversation messages
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
        content = msg.content[:1000]  # Truncate long messages
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

    # Clean up result
    learnings = result.strip()
    if not learnings:
        return None

    # Append to memory.md
    memory_file = (
        db.query(BrainFile)
        .filter(
            BrainFile.owner_id == user_id,
            BrainFile.file_key == "memory",
        )
        .first()
    )

    if not memory_file:
        logger.warning(f"No memory file found for user {user_id}")
        return None

    # Append learnings with timestamp section
    date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    new_section = f"\n\n### Session {date_str}\n{learnings}"

    memory_file.content += new_section
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
