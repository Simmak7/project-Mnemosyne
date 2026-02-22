"""
Context Assembler - Builds the full brain context for LLM queries.

Two-tier knowledge system:
- Knowledge Map: compressed summaries of ALL topics (always loaded)
- Deep Knowledge: full content of selected topics (within budget)
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
    context_budget: Optional[int] = None,
    query: Optional[str] = None,
) -> AssembledBrainContext:
    """Assemble full brain context with two-tier knowledge for an LLM query."""
    max_context = context_budget or getattr(config, "BRAIN_MAX_CONTEXT_TOKENS", 6000)
    core_budget = max(int(max_context * 0.4), 1500)

    # 1. Load core files (always included)
    core_files = (
        db.query(BrainFile)
        .filter(BrainFile.owner_id == user_id, BrainFile.file_key.in_(["soul", "mnemosyne", "memory"]))
        .all()
    )
    core_map = {f.file_key: f for f in core_files}
    files_used, core_parts, core_tokens = [], [], 0

    soul = core_map.get("soul")
    soul_instructions = ""
    if soul:
        soul_instructions = soul.content
        files_used.append("soul")
        core_tokens += soul.token_count_approx or len(soul.content) // 4

    memory = core_map.get("memory")
    if memory and memory.content and len(memory.content) > 100:
        remaining = core_budget - core_tokens
        if remaining > 200:
            content = _truncate_to_budget(memory.content, remaining)
            core_parts.append(f"## Memory\n{content}")
            files_used.append("memory")
            core_tokens += len(content) // 4

    # 2. Load ALL compressed summaries (Knowledge Map)
    all_topics = (
        db.query(BrainFile)
        .filter(BrainFile.owner_id == user_id, BrainFile.file_type == "topic")
        .all()
    )

    compressed_parts, compressed_tokens = [], 0
    has_compressed = any(bf.compressed_content for bf in all_topics)

    if has_compressed:
        for bf in all_topics:
            if bf.compressed_content:
                compressed_parts.append(f"**{bf.title}** ({bf.file_key}): {bf.compressed_content}")
                compressed_tokens += bf.compressed_token_count or len(bf.compressed_content) // 4
        if compressed_parts:
            files_used.append("knowledge_map")
    else:
        overview = core_map.get("mnemosyne")
        if overview:
            content = _truncate_to_budget(overview.content, core_budget - core_tokens)
            core_parts.append(f"## Knowledge Overview\n{content}")
            files_used.append("mnemosyne")
            core_tokens += len(content) // 4

    used_tokens = core_tokens + compressed_tokens

    # 3. Fill remaining budget with deep topics
    deep_budget = max_context - used_tokens - 500
    topic_parts, topic_tokens, topics_matched = [], 0, []
    topic_file_map = {bf.file_key: bf for bf in all_topics}

    # LLM-guided topic selection override (when budget allows)
    if query and max_context >= 4500 and has_compressed:
        from features.mnemosyne_brain.services.llm_topic_selector import select_topics_llm_guided
        from features.mnemosyne_brain.services.topic_selector import compute_max_topics
        summaries_for_llm = [
            {"file_key": bf.file_key, "title": bf.title, "summary": bf.compressed_content}
            for bf in all_topics if bf.compressed_content
        ]
        llm_scores = select_topics_llm_guided(
            query, summaries_for_llm, topic_file_map,
            max_topics=compute_max_topics(max_context), token_budget=deep_budget,
        )
        if llm_scores:
            topic_scores = llm_scores

    for ts in topic_scores:
        if topic_tokens >= deep_budget:
            break
        topic_file = topic_file_map.get(ts.file_key)
        if not topic_file:
            continue
        content = _truncate_to_budget(topic_file.content, deep_budget - topic_tokens)
        topic_parts.append(f"## {topic_file.title}\n{content}")
        files_used.append(ts.file_key)
        topic_tokens += len(content) // 4
        topics_matched.append({
            "key": ts.file_key, "title": ts.title,
            "score": round(ts.score, 3), "method": ts.match_method,
        })

    # 4. Build loaded files summary
    loaded_parts = []
    if has_compressed:
        loaded_parts.append(f"Knowledge Map: {len(compressed_parts)} topics indexed")
    else:
        loaded_parts.append("Core: " + ", ".join(k for k in ["mnemosyne", "memory"] if k in files_used))
    if topics_matched:
        loaded_parts.append("Deep: " + ", ".join(t["title"] for t in topics_matched))
    loaded_summary = "; ".join(loaded_parts) if loaded_parts else "No files loaded"

    # 5. Format system prompt with two-tier knowledge
    system_prompt = BRAIN_SYSTEM_PROMPT.format(
        soul_instructions=soul_instructions,
        loaded_files_summary=loaded_summary,
    )

    knowledge_sections = list(core_parts)
    if compressed_parts:
        knowledge_sections.append("## Your Knowledge Map\n" + "\n\n".join(compressed_parts))
    if topic_parts:
        knowledge_sections.append("## Deep Knowledge (Selected Topics)")
        knowledge_sections.extend(topic_parts)

    # If topics exist but none matched, add honest-answer instruction
    if all_topics and not topics_matched:
        knowledge_sections.append(
            "## NOTE: No topics closely matched this query. "
            "Be honest with the user that you don't have detailed knowledge "
            "on this specific subject. Share what you can from the Knowledge Map "
            "summaries, but clearly indicate the limits of your knowledge. "
            "Suggest the user check if they have notes on this topic or try "
            "different search terms."
        )

    knowledge_context = "\n\n".join(knowledge_sections)
    if knowledge_context:
        system_prompt += f"\n\n--- YOUR KNOWLEDGE ---\n{knowledge_context}\n--- END KNOWLEDGE ---"

    logger.info(
        f"Assembled brain context: system_prompt={len(system_prompt)} chars, "
        f"knowledge={len(knowledge_context)} chars, "
        f"core_parts={len(core_parts)}, compressed={len(compressed_parts)}, "
        f"deep_topics={len(topic_parts)}, files={files_used}"
    )

    return AssembledBrainContext(
        system_prompt=system_prompt,
        brain_files_used=files_used,
        topics_matched=topics_matched,
        total_tokens=used_tokens + topic_tokens,
        truncated=topic_tokens >= deep_budget,
    )


def _truncate_to_budget(content: str, token_budget: int) -> str:
    """Truncate content to fit within token budget (approx 4 chars/token)."""
    char_budget = token_budget * 4
    if len(content) <= char_budget:
        return content
    truncated = content[:char_budget]
    last_period = truncated.rfind(".")
    if last_period > char_budget * 0.5:
        truncated = truncated[:last_period + 1]
    return truncated + "\n\n[...truncated]"


def format_conversation_history_tiered(
    messages: List[Dict],
    conversation_summary: Optional[str] = None,
) -> str:
    """Format conversation history: recent full, older condensed, archive summarized."""
    parts = []
    if conversation_summary:
        parts.append(f"[Previous conversation summary]\n{conversation_summary}")

    recent = messages[-5:] if len(messages) > 5 else messages
    older = messages[-15:-5] if len(messages) > 5 else []

    if older:
        older_text = "\n".join(f"{m['role'].capitalize()}: {m['content'][:200]}..." for m in older)
        parts.append(f"[Earlier in this conversation]\n{older_text}")
    if recent:
        recent_text = "\n\n".join(f"{m['role'].capitalize()}: {m['content'][:1000]}" for m in recent)
        parts.append(f"[Recent messages]\n{recent_text}")

    return "\n\n---\n\n".join(parts) if parts else ""
