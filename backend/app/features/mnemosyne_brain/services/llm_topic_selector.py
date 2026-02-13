"""
LLM-Guided Topic Selector - Uses a fast LLM to pick deep topics.

Given compressed summaries (already loaded for the Knowledge Map),
asks the LLM which topics are most relevant to the user's query.
Falls back gracefully if the LLM response is unparseable.
"""

import json
import logging
import re
from typing import List, Dict, Any

from features.mnemosyne_brain.services.topic_selector import TopicScore
from core import config

logger = logging.getLogger(__name__)


def select_topics_llm_guided(
    query: str,
    compressed_summaries: List[Dict],
    topic_file_map: Dict[str, Any],
    max_topics: int = 5,
    token_budget: int = 6000,
) -> List[TopicScore]:
    """
    Use LLM to select which deep topics to load for a query.

    Returns list of TopicScore objects, or empty list on failure
    (caller should fall back to embedding-based selection).
    """
    from features.mnemosyne_brain.services.topic_generator import call_ollama_generate
    from features.mnemosyne_brain.services.prompts import TOPIC_SELECTION_PROMPT

    if not compressed_summaries or not query:
        return []

    topic_list = "\n".join(
        f"- {s['file_key']}: {s['title']} -- {s.get('summary', '')[:150]}"
        for s in compressed_summaries
    )

    prompt = TOPIC_SELECTION_PROMPT.format(
        query=query,
        topic_list=topic_list,
        max_topics=max_topics,
    )

    # Use the brain model (typically a small/fast model) for selection
    selection_model = getattr(config, "BRAIN_MODEL", "llama3.2:3b")
    response = call_ollama_generate(prompt, model=selection_model)

    if not response:
        logger.warning("LLM topic selection returned empty response")
        return []

    valid_keys = {s["file_key"] for s in compressed_summaries}
    selected_keys = _parse_topic_keys(response, valid_keys)

    if not selected_keys:
        logger.warning(f"LLM topic selection parse failed: {response[:200]}")
        return []

    # Build TopicScore objects from selected keys
    results = []
    tokens_used = 0
    for rank, key in enumerate(selected_keys[:max_topics]):
        tf = topic_file_map.get(key)
        if not tf:
            continue
        tc = tf.token_count_approx or 0
        if tokens_used + tc > token_budget:
            continue
        results.append(TopicScore(
            file_key=key,
            title=tf.title,
            score=1.0 - (rank * 0.05),
            keyword_score=0.0,
            embedding_score=0.0,
            match_method="llm_guided",
            token_count=tc,
        ))
        tokens_used += tc

    logger.info(
        f"LLM-guided selection: {[r.file_key for r in results]} "
        f"for query: {query[:60]}"
    )
    return results


def _parse_topic_keys(response: str, valid_keys: set) -> List[str]:
    """Extract topic file_keys from LLM response, validating against known keys."""
    # Try to find a JSON array in the response
    match = re.search(r'\[.*?\]', response, re.DOTALL)
    if match:
        try:
            keys = json.loads(match.group())
            if isinstance(keys, list):
                validated = [k for k in keys if isinstance(k, str) and k in valid_keys]
                if validated:
                    return validated
        except (json.JSONDecodeError, TypeError):
            pass

    # Fallback: extract topic_N patterns from free text
    found = re.findall(r'topic_\d+', response)
    seen = set()
    unique = []
    for k in found:
        if k in valid_keys and k not in seen:
            seen.add(k)
            unique.append(k)
    return unique
