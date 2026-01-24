"""
Ranking module for RAG system.

Implements Reciprocal Rank Fusion (RRF) for combining results
from multiple retrieval methods with different scoring scales.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any, Tuple
from datetime import datetime, timedelta

from .retrieval import RetrievalResult

logger = logging.getLogger(__name__)


@dataclass
class RankingConfig:
    """Configuration for result ranking."""
    rrf_k: int = 60  # RRF constant (typical range: 10-100)

    # Method weights (should sum to ~1.0 for interpretability)
    semantic_weight: float = 0.4
    chunk_weight: float = 0.25
    wikilink_weight: float = 0.2
    fulltext_weight: float = 0.1
    image_weight: float = 0.05

    # Boost factors
    recency_boost: bool = True
    recency_half_life_days: int = 30  # Notes lose half relevance after this

    max_results: int = 20


@dataclass
class RankedResult:
    """A result with combined ranking score."""
    result: RetrievalResult
    rrf_score: float
    method_scores: Dict[str, float] = field(default_factory=dict)
    final_score: float = 0.0
    rank: int = 0


def reciprocal_rank_fusion(
    result_lists: Dict[str, List[RetrievalResult]],
    config: RankingConfig = None
) -> List[RankedResult]:
    """
    Combine multiple ranked result lists using Reciprocal Rank Fusion.

    RRF Formula: score(d) = Σ (1 / (k + rank(d, r)))
    where k is a constant and rank(d, r) is the rank of document d in result list r.

    Args:
        result_lists: Dictionary mapping method names to result lists
        config: Ranking configuration

    Returns:
        List of RankedResult objects sorted by combined score
    """
    if config is None:
        config = RankingConfig()

    # Map source to RRF scores from each method
    source_scores: Dict[Tuple[str, int], Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    # Track the actual results for each source
    source_results: Dict[Tuple[str, int], RetrievalResult] = {}

    # Get method weights
    method_weights = {
        'semantic': config.semantic_weight,
        'chunk_semantic': config.chunk_weight,
        'wikilink': config.wikilink_weight,
        'fulltext': config.fulltext_weight,
        'image_tag': config.image_weight,
        'image_link': config.image_weight,
        'image_tag_indirect': config.image_weight * 0.5,
        'direct': 1.0,  # Direct fetches get full weight
    }

    # Calculate RRF scores for each method
    for method, results in result_lists.items():
        weight = method_weights.get(method, 0.1)

        for rank, result in enumerate(results):
            source_key = (result.source_type, result.source_id)

            # RRF score contribution
            rrf_contribution = weight / (config.rrf_k + rank + 1)
            source_scores[source_key][method] = rrf_contribution

            # Keep the best result (highest similarity) for each source
            if source_key not in source_results or result.similarity > source_results[source_key].similarity:
                source_results[source_key] = result

    # Combine scores and create ranked results
    ranked_results: List[RankedResult] = []

    for source_key, method_scores in source_scores.items():
        if source_key not in source_results:
            continue

        result = source_results[source_key]

        # Sum all RRF contributions
        total_rrf_score = sum(method_scores.values())

        ranked_results.append(RankedResult(
            result=result,
            rrf_score=total_rrf_score,
            method_scores=dict(method_scores),
            final_score=total_rrf_score
        ))

    # Sort by final score
    ranked_results.sort(key=lambda x: x.final_score, reverse=True)

    # Assign ranks
    for i, rr in enumerate(ranked_results):
        rr.rank = i + 1

    # Limit results
    ranked_results = ranked_results[:config.max_results]

    logger.info(f"RRF fusion: {len(ranked_results)} combined results from {len(result_lists)} methods")
    return ranked_results


def apply_recency_boost(
    results: List[RankedResult],
    note_dates: Dict[int, datetime],
    half_life_days: int = 30
) -> List[RankedResult]:
    """
    Apply recency boost to note results.

    More recent notes get a slight score boost.

    Args:
        results: Ranked results to boost
        note_dates: Dictionary mapping note IDs to created/updated dates
        half_life_days: Days after which boost decays to 50%

    Returns:
        Results with boosted scores
    """
    now = datetime.now()

    for rr in results:
        if rr.result.source_type != 'note':
            continue

        note_date = note_dates.get(rr.result.source_id)
        if not note_date:
            continue

        # Calculate age in days
        age_days = (now - note_date).days

        # Exponential decay: boost = 0.5^(age/half_life)
        # This gives a small boost (0.0-0.2) for recent content
        if age_days < 0:
            age_days = 0

        decay_factor = 0.5 ** (age_days / half_life_days)
        recency_boost = 0.2 * decay_factor  # Max 20% boost for brand new content

        rr.final_score += recency_boost

    # Re-sort after boost
    results.sort(key=lambda x: x.final_score, reverse=True)

    # Re-assign ranks
    for i, rr in enumerate(results):
        rr.rank = i + 1

    return results


def deduplicate_results(results: List[RankedResult]) -> List[RankedResult]:
    """
    Remove duplicate sources, keeping highest-ranked version.

    Handles cases where a note appears both as full note and as chunk.

    Args:
        results: Ranked results to deduplicate

    Returns:
        Deduplicated results
    """
    seen_notes: Set[int] = set()
    deduplicated: List[RankedResult] = []

    for rr in results:
        # For chunks, use the parent note ID
        if rr.result.source_type == 'chunk':
            note_id = rr.result.metadata.get('note_id')
            if note_id and note_id in seen_notes:
                continue
            if note_id:
                seen_notes.add(note_id)
        elif rr.result.source_type == 'note':
            if rr.result.source_id in seen_notes:
                continue
            seen_notes.add(rr.result.source_id)

        deduplicated.append(rr)

    # Re-assign ranks
    for i, rr in enumerate(deduplicated):
        rr.rank = i + 1

    logger.debug(f"Deduplication: {len(results)} -> {len(deduplicated)} results")
    return deduplicated


def merge_and_rank(
    semantic_results: List[RetrievalResult],
    chunk_results: List[RetrievalResult],
    graph_results: List[RetrievalResult],
    fulltext_results: List[RetrievalResult],
    image_results: List[RetrievalResult],
    config: RankingConfig = None
) -> List[RankedResult]:
    """
    Convenience function to merge all result types and rank.

    Args:
        semantic_results: Results from note-level semantic search
        chunk_results: Results from chunk-level semantic search
        graph_results: Results from wikilink graph traversal
        fulltext_results: Results from full-text search
        image_results: Results from image retrieval
        config: Ranking configuration

    Returns:
        Combined and ranked results
    """
    result_lists = {
        'semantic': semantic_results,
        'chunk_semantic': chunk_results,
        'wikilink': graph_results,
        'fulltext': fulltext_results,
    }

    # Categorize image results by method
    for img_result in image_results:
        method = img_result.retrieval_method
        if method not in result_lists:
            result_lists[method] = []
        result_lists[method].append(img_result)

    # Remove empty lists
    result_lists = {k: v for k, v in result_lists.items() if v}

    # Apply RRF
    ranked = reciprocal_rank_fusion(result_lists, config)

    # Deduplicate
    ranked = deduplicate_results(ranked)

    return ranked


def get_retrieval_summary(ranked_results: List[RankedResult]) -> Dict[str, Any]:
    """
    Generate a summary of the retrieval process for explainability.

    Args:
        ranked_results: Final ranked results

    Returns:
        Summary dictionary with statistics
    """
    if not ranked_results:
        return {
            'total_sources_searched': 0,
            'sources_used': 0,
            'retrieval_methods_used': [],
            'avg_relevance_score': 0.0,
            'source_type_breakdown': {}
        }

    # Collect method contributions
    methods_used: Set[str] = set()
    for rr in ranked_results:
        methods_used.update(rr.method_scores.keys())

    # Source type breakdown
    type_counts: Dict[str, int] = defaultdict(int)
    for rr in ranked_results:
        type_counts[rr.result.source_type] += 1

    # Calculate average relevance
    avg_score = sum(rr.final_score for rr in ranked_results) / len(ranked_results)

    return {
        'total_sources_searched': len(ranked_results),
        'sources_used': len(ranked_results),
        'retrieval_methods_used': sorted(list(methods_used)),
        'avg_relevance_score': round(avg_score, 3),
        'source_type_breakdown': dict(type_counts),
        'top_method': max(methods_used, key=lambda m: sum(
            rr.method_scores.get(m, 0) for rr in ranked_results
        )) if methods_used else None
    }
