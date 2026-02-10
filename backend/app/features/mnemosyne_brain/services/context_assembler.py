"""
Context Assembler - Builds the full brain context for LLM queries.

Assembles core brain files + selected topic files within token budget,
then formats the system prompt with personality and knowledge.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from features.mnemosyne_brain.models.brain_file import BrainFile
from features.mnemosyne_brain.services.topic_selector import TopicScore
from features.mnemosyne_brain.services.prompts import BRAIN_SYSTEM_PROMPT
from core import config

logger = logging.getLogger(__name__)


@dataclass
class AssembledBrainContext:
    """Result of context assembly."""
    system_prompt: str
    brain_files_used: List[str] = field(default_factory=list)
    topics_matched: List[Dict] = field(default_factory=list)
    total_tokens: int = 0
    truncated: bool = False


def assemble_context(
    db: Session,
    user_id: int,
    topic_scores: List[TopicScore],
    conversation_history: str = "",
) -> AssembledBrainContext:
    """
    Assemble full brain context for an LLM query.

    Loads core files (always) + selected topics (by score),
    respecting token budgets.

    Args:
        db: Database session
        user_id: Owner ID
        topic_scores: Pre-scored topic selections
        conversation_history: Previous messages in conversation
    """
    max_context = getattr(config, "BRAIN_MAX_CONTEXT_TOKENS", 6000)
    core_budget = getattr(config, "BRAIN_CORE_TOKEN_BUDGET", 2500)

    # Load core files (always included)
    core_keys = ["soul", "mnemosyne", "memory"]
    core_files = (
        db.query(BrainFile)
        .filter(
            BrainFile.owner_id == user_id,
            BrainFile.file_key.in_(core_keys),
        )
        .all()
    )
    core_map = {f.file_key: f for f in core_files}

    # Build core content
    files_used = []
    core_parts = []
    core_tokens = 0

    # Soul first (personality)
    soul = core_map.get("soul")
    soul_instructions = ""
    if soul:
        soul_instructions = soul.content
        files_used.append("soul")
        core_tokens += soul.token_count_approx or len(soul.content) // 4

    # Mnemosyne overview
    overview = core_map.get("mnemosyne")
    if overview:
        content = _truncate_to_budget(overview.content, core_budget - core_tokens)
        core_parts.append(f"## Knowledge Overview\n{content}")
        files_used.append("mnemosyne")
        core_tokens += len(content) // 4

    # Memory (learnings)
    memory = core_map.get("memory")
    if memory and memory.content and len(memory.content) > 100:
        remaining = core_budget - core_tokens
        if remaining > 200:
            content = _truncate_to_budget(memory.content, remaining)
            core_parts.append(f"## Memory\n{content}")
            files_used.append("memory")
            core_tokens += len(content) // 4

    # Build topic content
    topic_parts = []
    topic_budget = max_context - core_tokens - 500  # Reserve 500 for prompt overhead
    topic_tokens = 0
    topics_matched = []

    # Batch load all topic files in one query (prevents N+1)
    topic_keys = [ts.file_key for ts in topic_scores]
    if topic_keys:
        topic_files = (
            db.query(BrainFile)
            .filter(
                BrainFile.owner_id == user_id,
                BrainFile.file_key.in_(topic_keys),
            )
            .all()
        )
        topic_file_map = {f.file_key: f for f in topic_files}
    else:
        topic_file_map = {}

    for ts in topic_scores:
        if topic_tokens >= topic_budget:
            break

        topic_file = topic_file_map.get(ts.file_key)
        if not topic_file:
            continue

        remaining = topic_budget - topic_tokens
        content = _truncate_to_budget(topic_file.content, remaining)
        topic_parts.append(f"## {topic_file.title}\n{content}")
        files_used.append(ts.file_key)
        topic_tokens += len(content) // 4

        topics_matched.append({
            "key": ts.file_key,
            "title": ts.title,
            "score": round(ts.score, 3),
            "method": ts.match_method,
        })

    # Assemble loaded files summary
    loaded_summary_parts = []
    if core_parts:
        loaded_summary_parts.append("Core: " + ", ".join(
            k for k in ["mnemosyne", "memory"] if k in files_used
        ))
    if topics_matched:
        topic_names = [t["title"] for t in topics_matched]
        loaded_summary_parts.append("Topics: " + ", ".join(topic_names))

    loaded_summary = "; ".join(loaded_summary_parts) if loaded_summary_parts else "No files loaded"

    # Format system prompt
    knowledge_context = "\n\n".join(core_parts + topic_parts)

    system_prompt = BRAIN_SYSTEM_PROMPT.format(
        soul_instructions=soul_instructions,
        loaded_files_summary=loaded_summary,
    )

    if knowledge_context:
        system_prompt += f"\n\n--- YOUR KNOWLEDGE ---\n{knowledge_context}\n--- END KNOWLEDGE ---"

    total_tokens = core_tokens + topic_tokens

    return AssembledBrainContext(
        system_prompt=system_prompt,
        brain_files_used=files_used,
        topics_matched=topics_matched,
        total_tokens=total_tokens,
        truncated=topic_tokens >= topic_budget,
    )


def _truncate_to_budget(content: str, token_budget: int) -> str:
    """Truncate content to fit within token budget (approx 4 chars/token)."""
    char_budget = token_budget * 4
    if len(content) <= char_budget:
        return content

    # Truncate at sentence boundary
    truncated = content[:char_budget]
    last_period = truncated.rfind(".")
    if last_period > char_budget * 0.5:
        truncated = truncated[: last_period + 1]

    return truncated + "\n\n[...truncated]"


def format_conversation_history(
    messages: List[Dict],
    max_messages: int = 10,
) -> str:
    """Format recent conversation messages for context."""
    recent = messages[-max_messages:]
    parts = []
    for msg in recent:
        role = msg.get("role", "user")
        content = msg.get("content", "")[:500]
        parts.append(f"{role.capitalize()}: {content}")
    return "\n\n".join(parts)


def format_conversation_history_tiered(
    messages: List[Dict],
    conversation_summary: Optional[str] = None,
) -> str:
    """
    Format conversation history with tiered approach.

    Tier 1: Recent 5 messages - full content (up to 1000 chars each)
    Tier 2: Older messages (6-15) - condensed (200 chars each)
    Tier 3: Archive summary - single paragraph from LLM summarization

    Args:
        messages: List of {"role": str, "content": str} dicts
        conversation_summary: Pre-computed summary of older messages

    Returns:
        Formatted string for inclusion in system prompt
    """
    parts = []

    # Tier 3: Archive summary (if exists)
    if conversation_summary:
        parts.append(f"[Previous conversation summary]\n{conversation_summary}")

    # Split messages into tiers
    recent = messages[-5:] if len(messages) > 5 else messages
    older = messages[-15:-5] if len(messages) > 5 else []

    # Tier 2: Older messages (condensed)
    if older:
        older_text = "\n".join([
            f"{m['role'].capitalize()}: {m['content'][:200]}..."
            for m in older
        ])
        parts.append(f"[Earlier in this conversation]\n{older_text}")

    # Tier 1: Recent messages (full)
    if recent:
        recent_text = "\n\n".join([
            f"{m['role'].capitalize()}: {m['content'][:1000]}"
            for m in recent
        ])
        parts.append(f"[Recent messages]\n{recent_text}")

    return "\n\n---\n\n".join(parts) if parts else ""
