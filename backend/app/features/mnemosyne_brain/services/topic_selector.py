"""
Topic Selector - Matches a query to relevant brain topic files.

Uses keyword matching (0.3 weight) + embedding similarity (0.7 weight)
to select the most relevant topics within a token budget.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session

from features.mnemosyne_brain.models.brain_file import BrainFile
from core import config

logger = logging.getLogger(__name__)


def compute_max_topics(token_budget: int) -> int:
    """Compute the max number of deep topics based on available token budget."""
    if token_budget < 3000:
        return 3
    if token_budget <= 8000:
        return 5
    if token_budget <= 20000:
        return 10
    return 15


@dataclass
class TopicScore:
    """A scored topic match."""
    file_key: str
    title: str
    score: float
    keyword_score: float
    embedding_score: float
    match_method: str  # "keyword", "embedding", "both"
    token_count: int


def select_topics(
    db: Session,
    user_id: int,
    query: str,
    query_embedding: Optional[List[float]] = None,
    max_topics: Optional[int] = None,
    token_budget: Optional[int] = None,
    pinned_topics: Optional[List[str]] = None,
    previously_loaded_topics: Optional[List[str]] = None,
) -> List[TopicScore]:
    """
    Select the most relevant topic files for a query.

    Args:
        db: Database session
        user_id: Owner ID
        query: User query text
        query_embedding: Pre-computed query embedding (768-dim)
        max_topics: Maximum topics to return. If None, computed from token_budget.
        token_budget: Max total tokens across selected topics
        pinned_topics: List of topic keys to always include
        previously_loaded_topics: Topics loaded in prior turn (get +0.3 bonus)

    Returns:
        Sorted list of TopicScore (highest first)
    """
    if token_budget is None:
        token_budget = getattr(config, "BRAIN_TOPIC_TOKEN_BUDGET", 3000)

    if max_topics is None:
        max_topics = compute_max_topics(token_budget)

    pinned_topics = pinned_topics or []
    prev_set = set(previously_loaded_topics) if previously_loaded_topics else set()

    # Fetch all topic files
    topic_files = (
        db.query(BrainFile)
        .filter(
            BrainFile.owner_id == user_id,
            BrainFile.file_type == "topic",
        )
        .all()
    )

    if not topic_files:
        return []

    # Build topic map
    topic_map = {tf.file_key: tf for tf in topic_files}

    # Score each topic
    query_lower = query.lower()
    query_words = set(query_lower.split())

    # FIRST: Always include pinned topics
    selected: List[TopicScore] = []
    tokens_used = 0

    for key in pinned_topics:
        tf = topic_map.get(key)
        if not tf:
            continue

        token_count = tf.token_count_approx or 0
        if tokens_used + token_count > token_budget:
            continue

        keyword_score = _compute_keyword_score(query_words, query_lower, tf)
        embedding_score = _compute_embedding_score(query_embedding, tf)
        combined = (keyword_score * 0.3) + (embedding_score * 0.7)

        selected.append(TopicScore(
            file_key=tf.file_key,
            title=tf.title,
            score=max(combined, 1.0),  # Pinned topics get max score
            keyword_score=keyword_score,
            embedding_score=embedding_score,
            match_method="pinned",
            token_count=token_count,
        ))
        tokens_used += token_count

    # THEN: Score and select remaining topics
    remaining_budget = token_budget - tokens_used
    remaining_slots = max_topics - len(selected)

    scored: List[TopicScore] = []
    for tf in topic_files:
        if tf.file_key in pinned_topics:
            continue  # Already included

        keyword_score = _compute_keyword_score(query_words, query_lower, tf)
        embedding_score = _compute_embedding_score(query_embedding, tf)
        combined = (keyword_score * 0.3) + (embedding_score * 0.7)

        # Persistence bonus: previously loaded topics stay relevant
        if tf.file_key in prev_set:
            combined += 0.3

        if combined < 0.05:
            continue

        method = "both"
        if keyword_score > 0 and embedding_score == 0:
            method = "keyword"
        elif embedding_score > 0 and keyword_score == 0:
            method = "embedding"
        if tf.file_key in prev_set and method != "pinned":
            method = f"{method}+persistent"

        scored.append(TopicScore(
            file_key=tf.file_key,
            title=tf.title,
            score=combined,
            keyword_score=keyword_score,
            embedding_score=embedding_score,
            match_method=method,
            token_count=tf.token_count_approx or 0,
        ))

    # Sort by score descending
    scored.sort(key=lambda x: x.score, reverse=True)

    # Fill remaining slots within budget
    for topic in scored:
        if len(selected) >= max_topics + len(pinned_topics):
            break
        if tokens_used + topic.token_count > token_budget:
            continue
        selected.append(topic)
        tokens_used += topic.token_count

    logger.info(
        f"Selected {len(selected)} topics for query "
        f"(pinned: {len(pinned_topics)}, scores: {[f'{t.file_key}={t.score:.2f}' for t in selected]})"
    )
    return selected


def _compute_keyword_score(
    query_words: set,
    query_lower: str,
    brain_file: BrainFile,
) -> float:
    """Score based on keyword overlap with topic keywords and title."""
    keywords = brain_file.topic_keywords or []
    if not keywords:
        return 0.0

    # Check keyword presence in query
    keyword_matches = 0
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in query_lower:
            keyword_matches += 1

    if keyword_matches == 0:
        # Check query words in title
        title_words = set((brain_file.title or "").lower().split())
        title_overlap = len(query_words & title_words)
        if title_overlap > 0:
            return min(title_overlap / max(len(query_words), 1), 1.0) * 0.5
        return 0.0

    return min(keyword_matches / max(len(keywords), 1), 1.0)


def _compute_embedding_score(
    query_embedding: Optional[List[float]],
    brain_file: BrainFile,
) -> float:
    """Compute cosine similarity between query and topic embeddings."""
    if query_embedding is None or brain_file.embedding is None:
        return 0.0

    try:
        from embeddings import cosine_similarity
        topic_emb = list(brain_file.embedding)
        return max(cosine_similarity(query_embedding, topic_emb), 0.0)
    except Exception:
        return 0.0
