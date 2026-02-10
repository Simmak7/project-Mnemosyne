"""
Topic Generator - Creates topic markdown files from note clusters.

Takes a group of notes (same Louvain community) and generates a
condensed topic summary using LLM.
"""

import hashlib
import json
import logging
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass

from core import config

logger = logging.getLogger(__name__)

OLLAMA_HOST = config.OLLAMA_HOST


@dataclass
class TopicResult:
    """Result of generating a single topic file."""
    file_key: str
    title: str
    content: str
    community_id: int
    keywords: List[str]
    source_note_ids: List[int]
    token_count_approx: int


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English."""
    return len(text) // 4


def compute_content_hash(content: str) -> str:
    """SHA-256 hash for change detection."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def call_ollama_generate(prompt: str, system: str = "", model: str = None) -> str:
    """Call Ollama generate endpoint (non-streaming)."""
    model = model or getattr(config, "BRAIN_MODEL", "llama3.2:3b")
    temperature = getattr(config, "BRAIN_TEMPERATURE", 0.7)

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "think": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 2048,
                },
            },
            timeout=180,
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        logger.error(f"Ollama generate failed: {e}")
        return ""


def generate_topic_file(
    community_id: int,
    topic_index: int,
    notes: List[Dict],
    model: str = None,
) -> Optional[TopicResult]:
    """
    Generate a topic markdown file from a cluster of notes.

    Args:
        community_id: Louvain community ID
        topic_index: Sequential index for file_key (topic_0, topic_1, ...)
        notes: List of dicts with {id, title, content}
        model: Ollama model override

    Returns:
        TopicResult or None on failure
    """
    if not notes:
        return None

    from features.mnemosyne_brain.services.prompts import TOPIC_GENERATION_PROMPT

    # Prepare notes content (truncate each to keep prompt manageable)
    max_chars_per_note = 1500
    notes_text_parts = []
    for note in notes:
        title = note.get("title", "Untitled")
        content = note.get("content", "")[:max_chars_per_note]
        notes_text_parts.append(f"### {title}\n{content}")

    notes_content = "\n\n---\n\n".join(notes_text_parts)

    prompt = TOPIC_GENERATION_PROMPT.format(
        note_count=len(notes),
        notes_content=notes_content,
    )

    result_text = call_ollama_generate(prompt, model=model)
    if not result_text:
        logger.warning(f"Empty response for topic {topic_index} (community {community_id})")
        return None

    # Extract title from first heading
    title = f"Topic {topic_index}"
    for line in result_text.split("\n"):
        line = line.strip()
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Extract keywords from content (simple heuristic)
    keywords = _extract_keywords_from_notes(notes)

    file_key = f"topic_{topic_index}"
    source_ids = [n["id"] for n in notes if "id" in n]

    return TopicResult(
        file_key=file_key,
        title=title,
        content=result_text,
        community_id=community_id,
        keywords=keywords,
        source_note_ids=source_ids,
        token_count_approx=estimate_tokens(result_text),
    )


def _extract_keywords_from_notes(notes: List[Dict], max_keywords: int = 10) -> List[str]:
    """Extract representative keywords from note titles and content."""
    # Simple approach: collect title words, filter common words
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "and", "or", "but", "in", "on", "at", "to", "for", "of",
        "with", "by", "from", "as", "into", "this", "that", "it",
        "not", "no", "do", "does", "did", "has", "have", "had",
        "will", "would", "could", "should", "may", "might", "can",
        "i", "my", "me", "we", "our", "you", "your", "they", "them",
        "about", "how", "what", "when", "where", "which", "who",
        "some", "all", "any", "more", "very", "just", "also", "so",
    }

    word_freq: Dict[str, int] = {}
    for note in notes:
        title = note.get("title", "")
        # Title words weighted 3x
        for word in title.lower().split():
            word = word.strip(".,!?;:()[]{}\"'")
            if len(word) > 2 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 3

        # First 200 chars of content
        content = note.get("content", "")[:200]
        for word in content.lower().split():
            word = word.strip(".,!?;:()[]{}\"'")
            if len(word) > 2 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:max_keywords]]
