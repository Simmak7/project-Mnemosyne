"""
Result ranking and scoring utilities for search.

Provides functions for:
- Combining and ranking mixed result types
- Applying recency boosts to scores
- Calculating relevance scores with multiple factors

Ranking Factors:
- Base score: From full-text search (ts_rank) or semantic similarity
- Recency boost: Newer content ranked higher
- Type boost: Notes ranked higher than images
- Tag match boost: Results with matching tags ranked higher
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Ranking weights
RECENCY_WEIGHT = 0.1  # Max boost from recency
TYPE_WEIGHTS = {
    "note": 1.0,    # Notes are primary content
    "image": 0.8,   # Images slightly lower
    "tag": 0.6      # Tags for discovery only
}
TAG_MATCH_BOOST = 0.05  # Boost per matching tag


def calculate_relevance_score(
    base_score: float,
    item_type: str,
    created_at: Optional[datetime] = None,
    matching_tags: int = 0,
    recency_days: int = 30
) -> float:
    """
    Calculate final relevance score with multiple factors.

    Final score = base_score * type_weight + recency_boost + tag_boost

    Args:
        base_score: Initial score from search (0.0-1.0)
        item_type: Type of result ('note', 'image', 'tag')
        created_at: When the item was created (for recency)
        matching_tags: Number of query tags that match this item
        recency_days: Days within which recency boost applies

    Returns:
        Final relevance score (0.0-1.0+)
    """
    # Apply type weight
    type_weight = TYPE_WEIGHTS.get(item_type, 1.0)
    score = base_score * type_weight

    # Apply recency boost
    if created_at:
        recency_boost = apply_recency_boost(created_at, max_boost=RECENCY_WEIGHT, days=recency_days)
        score += recency_boost

    # Apply tag match boost
    if matching_tags > 0:
        tag_boost = min(matching_tags * TAG_MATCH_BOOST, 0.2)  # Cap at 0.2
        score += tag_boost

    return score


def apply_recency_boost(
    created_at: datetime,
    max_boost: float = 0.1,
    days: int = 30
) -> float:
    """
    Calculate recency boost based on item age.

    Items created within the specified days get a linearly decreasing boost.
    Items older than the specified days get no boost.

    Args:
        created_at: When the item was created
        max_boost: Maximum boost for brand new items
        days: Number of days over which boost decreases to 0

    Returns:
        Recency boost value (0.0 to max_boost)
    """
    now = datetime.utcnow()
    age = now - created_at

    if age.days >= days:
        return 0.0

    # Linear decay: max_boost at day 0, 0 at day `days`
    return max_boost * (1 - age.days / days)


def rank_combined_results(
    results: List[Dict[str, Any]],
    sort_by: str = "relevance",
    recency_boost: bool = True
) -> List[Dict[str, Any]]:
    """
    Rank combined search results from multiple sources.

    Applies relevance scoring with type weights and optional recency boost,
    then sorts by the specified criterion.

    Args:
        results: List of result dictionaries (must have 'type' and 'score' keys)
        sort_by: Sort criterion ('relevance', 'date', 'title')
        recency_boost: Whether to apply recency boost to scores

    Returns:
        Sorted list of results with updated 'final_score' key
    """
    # Calculate final scores
    for result in results:
        base_score = result.get("score", 0.0)
        item_type = result.get("type", "note")

        # Get created_at timestamp
        created_at = None
        if recency_boost:
            date_str = result.get("created_at") or result.get("uploaded_at")
            if date_str:
                try:
                    if isinstance(date_str, str):
                        created_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    elif isinstance(date_str, datetime):
                        created_at = date_str
                except ValueError:
                    pass

        final_score = calculate_relevance_score(
            base_score=base_score,
            item_type=item_type,
            created_at=created_at if recency_boost else None,
            matching_tags=0  # Could be enhanced to track matching tags
        )

        result["final_score"] = final_score

    # Sort by criterion
    if sort_by == "relevance":
        results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    elif sort_by == "date":
        def get_date(item):
            date_str = item.get("created_at") or item.get("uploaded_at") or ""
            return date_str if isinstance(date_str, str) else ""
        results.sort(key=get_date, reverse=True)
    elif sort_by == "title":
        results.sort(key=lambda x: x.get("title", "").lower())

    return results


def deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate results based on ID and type.

    When the same item appears from multiple search sources,
    keep the one with the highest score.

    Args:
        results: List of result dictionaries

    Returns:
        Deduplicated list with highest-scored duplicates retained
    """
    seen = {}  # key: (type, id), value: result with highest score

    for result in results:
        key = (result.get("type"), result.get("id"))
        if key not in seen:
            seen[key] = result
        else:
            # Keep the one with higher score
            existing_score = seen[key].get("score", 0)
            new_score = result.get("score", 0)
            if new_score > existing_score:
                seen[key] = result

    return list(seen.values())


def merge_search_results(
    fulltext_results: List[Dict[str, Any]],
    semantic_results: List[Dict[str, Any]],
    fulltext_weight: float = 0.6,
    semantic_weight: float = 0.4,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Merge and rank results from full-text and semantic search.

    Items appearing in both searches get boosted scores.
    Allows combining keyword matching with semantic understanding.

    Args:
        fulltext_results: Results from full-text search
        semantic_results: Results from semantic search
        fulltext_weight: Weight for full-text scores (default 0.6)
        semantic_weight: Weight for semantic scores (default 0.4)
        limit: Maximum results to return

    Returns:
        Merged and ranked results
    """
    # Index semantic results by (type, id)
    semantic_index = {}
    for result in semantic_results:
        key = (result.get("type", "note"), result.get("id"))
        semantic_index[key] = result

    merged = []
    seen_keys = set()

    # Process full-text results
    for result in fulltext_results:
        key = (result.get("type", "note"), result.get("id"))
        fulltext_score = result.get("score", 0)

        # Check if also in semantic results
        if key in semantic_index:
            semantic_score = semantic_index[key].get("similarity", 0)
            # Combined score with boost for appearing in both
            combined_score = (
                fulltext_score * fulltext_weight +
                semantic_score * semantic_weight +
                0.1  # Boost for appearing in both
            )
        else:
            combined_score = fulltext_score * fulltext_weight

        result["combined_score"] = combined_score
        merged.append(result)
        seen_keys.add(key)

    # Add semantic-only results
    for result in semantic_results:
        key = (result.get("type", "note"), result.get("id"))
        if key not in seen_keys:
            semantic_score = result.get("similarity", 0)
            result["combined_score"] = semantic_score * semantic_weight
            merged.append(result)

    # Sort by combined score
    merged.sort(key=lambda x: x.get("combined_score", 0), reverse=True)

    logger.debug(
        f"Merged {len(fulltext_results)} fulltext + {len(semantic_results)} semantic "
        f"-> {len(merged[:limit])} results"
    )

    return merged[:limit]
