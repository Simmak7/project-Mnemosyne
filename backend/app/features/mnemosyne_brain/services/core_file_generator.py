"""
Core File Generator - Creates master brain files.

Generates: mnemosyne.md, askimap.md, user_profile.md, soul.md, memory.md
"""

import logging
from typing import List, Dict, Optional

from features.mnemosyne_brain.services.topic_generator import (
    call_ollama_generate,
    estimate_tokens,
)
from features.mnemosyne_brain.services.prompts import (
    ASKIMAP_GENERATION_PROMPT,
    MNEMOSYNE_OVERVIEW_PROMPT,
    USER_PROFILE_PROMPT,
    DEFAULT_SOUL_CONTENT,
    DEFAULT_MEMORY_CONTENT,
)

logger = logging.getLogger(__name__)


def _build_topics_summary(topics: List[Dict]) -> str:
    """Build a concise summary of all topics for prompt input."""
    parts = []
    for t in topics:
        keywords = ", ".join(t.get("keywords", [])[:5])
        parts.append(f"- **{t['title']}** ({t['file_key']}): {keywords}")
    return "\n".join(parts)


def generate_askimap(topics: List[Dict], model: str = None) -> Dict:
    """
    Generate askimap.md - question-to-topic navigation index.

    Args:
        topics: List of dicts with {file_key, title, keywords, content_preview}
    """
    if not topics:
        return _empty_file("askimap", "Askimap - Question Navigation")

    topics_summary = _build_topics_summary(topics)

    topic_entries = []
    for t in topics:
        kw = ", ".join(t.get("keywords", []))
        topic_entries.append(f"### {t['file_key']}: {t['title']}\n**Keywords:** {kw}")

    prompt = ASKIMAP_GENERATION_PROMPT.format(
        topics_summary=topics_summary,
        topic_entries="\n\n".join(topic_entries),
    )

    content = call_ollama_generate(prompt, model=model)
    if not content:
        content = _build_fallback_askimap(topics)

    return {
        "file_key": "askimap",
        "file_type": "core",
        "title": "Askimap - Question Navigation",
        "content": content,
        "token_count_approx": estimate_tokens(content),
    }


def generate_mnemosyne_overview(
    topics: List[Dict],
    total_notes: int,
    community_count: int,
    model: str = None,
) -> Dict:
    """Generate mnemosyne.md - master overview of all knowledge."""
    if not topics:
        return _empty_file("mnemosyne", "Mnemosyne - Knowledge Overview")

    topics_summary = _build_topics_summary(topics)
    topic_list = "\n".join(f"- {t['file_key']}: {t['title']}" for t in topics)

    prompt = MNEMOSYNE_OVERVIEW_PROMPT.format(
        topics_summary=topics_summary,
        total_notes=total_notes,
        community_count=community_count,
        topic_list=topic_list,
    )

    content = call_ollama_generate(prompt, model=model)
    if not content:
        content = f"# Mnemosyne - Knowledge Overview\n\n{total_notes} notes across {community_count} topics."

    return {
        "file_key": "mnemosyne",
        "file_type": "core",
        "title": "Mnemosyne - Knowledge Overview",
        "content": content,
        "token_count_approx": estimate_tokens(content),
    }


def generate_user_profile(
    topics: List[Dict],
    sample_notes: List[Dict],
    model: str = None,
) -> Dict:
    """Generate user_profile.md - patterns and interests from notes."""
    topics_summary = _build_topics_summary(topics) if topics else "No topics yet."

    notes_text = ""
    for n in sample_notes[:10]:
        title = n.get("title", "Untitled")
        content = n.get("content", "")[:300]
        notes_text += f"### {title}\n{content}\n\n"

    prompt = USER_PROFILE_PROMPT.format(
        topics_summary=topics_summary,
        sample_notes=notes_text or "No notes available.",
    )

    content = call_ollama_generate(prompt, model=model)
    if not content:
        content = "# User Profile\n\nNot enough data to generate profile yet."

    return {
        "file_key": "user_profile",
        "file_type": "core",
        "title": "User Profile",
        "content": content,
        "token_count_approx": estimate_tokens(content),
    }


def get_default_soul() -> Dict:
    """Return default soul.md content."""
    return {
        "file_key": "soul",
        "file_type": "core",
        "title": "Soul - Personality",
        "content": DEFAULT_SOUL_CONTENT,
        "token_count_approx": estimate_tokens(DEFAULT_SOUL_CONTENT),
    }


def get_default_memory() -> Dict:
    """Return default memory.md scaffold."""
    return {
        "file_key": "memory",
        "file_type": "core",
        "title": "Memory - Conversation Learnings",
        "content": DEFAULT_MEMORY_CONTENT,
        "token_count_approx": estimate_tokens(DEFAULT_MEMORY_CONTENT),
    }


def _empty_file(file_key: str, title: str) -> Dict:
    """Create an empty placeholder brain file."""
    content = f"# {title}\n\nNo content generated yet. Build the brain to populate."
    return {
        "file_key": file_key,
        "file_type": "core",
        "title": title,
        "content": content,
        "token_count_approx": estimate_tokens(content),
    }


def _build_fallback_askimap(topics: List[Dict]) -> str:
    """Build a simple askimap without LLM (fallback)."""
    lines = ["# Askimap - Question Navigation\n"]
    lines.append("## Topic Index\n")
    for t in topics:
        keywords = ", ".join(t.get("keywords", []))
        lines.append(f"### {t['file_key']}: {t['title']}")
        lines.append(f"**Keywords:** {keywords}")
        lines.append("")
    return "\n".join(lines)
