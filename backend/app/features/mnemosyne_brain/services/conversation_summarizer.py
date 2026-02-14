"""
Conversation Summarizer - LLM-based conversation summarization.

Uses a fast model to create rolling summaries of older messages,
enabling long-term context retention within token budgets.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from core import config
from core.llm import get_default_provider, LLMMessage
from features.mnemosyne_brain.models.brain_conversation import (
    BrainConversation,
    BrainMessage,
)

logger = logging.getLogger(__name__)

SUMMARY_MODEL = "llama3.2:3b"  # Fast model for summarization

SUMMARY_PROMPT = """Summarize this conversation segment concisely, preserving:
1. Key topics discussed
2. Important facts or preferences the user mentioned
3. Decisions or conclusions reached
4. Questions that were answered

Keep the summary under 300 words. Focus on information useful for continuing later.

Conversation:
{messages}

Summary:"""


def should_update_summary(conversation: BrainConversation) -> bool:
    """Check if the conversation summary needs updating."""
    return (conversation.messages_since_summary or 0) >= 5


def _call_ollama_summary(prompt: str) -> Optional[str]:
    """Call LLM provider for summarization with fast model."""
    messages = [LLMMessage(role="user", content=prompt)]

    try:
        provider = get_default_provider()
        response = provider.generate(
            messages=messages,
            model=SUMMARY_MODEL,
            temperature=0.3,
            max_tokens=500,
            timeout=60,
        )
        return response.content.strip()
    except Exception as e:
        logger.error(f"Summarization LLM call failed: {e}")
        return None


def summarize_messages(messages: List[Dict]) -> Optional[str]:
    """
    Use LLM to summarize conversation messages.

    Args:
        messages: List of {"role": str, "content": str} dicts

    Returns:
        Summary string or None on failure
    """
    if not messages:
        return None

    messages_text = "\n".join([
        f"{m['role'].upper()}: {m['content'][:500]}"
        for m in messages
    ])

    prompt = SUMMARY_PROMPT.format(messages=messages_text)
    return _call_ollama_summary(prompt)


def update_conversation_summary(
    db: Session,
    conversation: BrainConversation,
) -> bool:
    """
    Update the rolling summary of a conversation.

    Gets messages since last summary, summarizes them,
    and combines with existing summary.

    Args:
        db: Database session
        conversation: BrainConversation to update

    Returns:
        True if summary was updated, False otherwise
    """
    # Get messages since last summary
    since_time = conversation.summary_updated_at or datetime.min
    messages = (
        db.query(BrainMessage)
        .filter(
            BrainMessage.conversation_id == conversation.id,
            BrainMessage.created_at > since_time,
        )
        .order_by(BrainMessage.created_at)
        .all()
    )

    if len(messages) < 5:
        return False

    messages_data = [{"role": m.role, "content": m.content} for m in messages]

    # Generate summary of new messages
    new_summary = summarize_messages(messages_data)
    if not new_summary:
        logger.warning(f"Failed to summarize conversation {conversation.id}")
        return False

    # Combine with existing summary
    if conversation.conversation_summary:
        combined = f"{conversation.conversation_summary}\n\n{new_summary}"
        # If combined is too long, re-summarize it
        if len(combined) > 2000:
            condensed = summarize_messages([
                {"role": "system", "content": combined}
            ])
            combined = condensed or combined[:2000]
    else:
        combined = new_summary

    # Update conversation
    conversation.conversation_summary = combined
    conversation.summary_updated_at = datetime.utcnow()
    conversation.messages_since_summary = 0

    try:
        db.commit()
        logger.info(f"Updated summary for conversation {conversation.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to save summary: {e}")
        db.rollback()
        return False


def increment_message_counter(db: Session, conversation: BrainConversation) -> None:
    """Increment the messages_since_summary counter."""
    conversation.messages_since_summary = (
        conversation.messages_since_summary or 0
    ) + 1
    try:
        db.commit()
    except Exception:
        db.rollback()
