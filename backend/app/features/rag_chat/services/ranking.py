"""
Ranking module for RAG system.

Implements Reciprocal Rank Fusion (RRF) for combining results
from multiple retrieval methods with different scoring scales.

Includes smart image boosting based on query type.
"""

import re
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any, Tuple
from datetime import datetime, timedelta

from .retrieval import RetrievalResult

logger = logging.getLogger(__name__)


# Image query detection patterns
IMAGE_KEYWORDS = {
    'image', 'images', 'picture', 'pictures', 'photo', 'photos',
    'photograph', 'photographs', 'screenshot', 'screenshots',
    'diagram', 'diagrams', 'illustration', 'visual', 'visuals'
}

IMAGE_PHRASES = [
    r'show\s+me',
    r'what\s+does\s+.+\s+look\s+like',
    r'any\s+(pictures?|photos?|images?)\s+of',
    r'see\s+(the|my|a)\s+',
]

# Document query detection patterns
DOCUMENT_KEYWORDS = {
    'document', 'documents', 'pdf', 'pdfs', 'report', 'reports',
    'contract', 'contracts', 'paper', 'papers', 'file', 'files',
    'article', 'articles', 'manual', 'manuals', 'invoice', 'invoices',
}

DOCUMENT_PHRASES = [
    r'in\s+(the|my|a)\s+(document|pdf|report|contract)',
    r'from\s+(the|my|a)\s+(document|pdf|report)',
    r'uploaded\s+(document|pdf|file)',
]


def detect_image_query(query: str) -> bool:
    """
    Detect if query is specifically asking for images/visuals.

    Returns True if query contains image-related keywords or patterns.
    """
    query_lower = query.lower()

    # Check keywords
    words = set(re.findall(r'\b\w+\b', query_lower))
    if words & IMAGE_KEYWORDS:
        return True

    # Check phrases
    for pattern in IMAGE_PHRASES:
        if re.search(pattern, query_lower):
            return True

    return False


def detect_document_query(query: str) -> bool:
    """
    Detect if query is asking about document/PDF content.

    Returns True if query contains document-related keywords or patterns.
    """
    query_lower = query.lower()

    words = set(re.findall(r'\b\w+\b', query_lower))
    if words & DOCUMENT_KEYWORDS:
        return True

    for pattern in DOCUMENT_PHRASES:
        if re.search(pattern, query_lower):
            return True

    return False


@dataclass
class RankingConfig:
    """Configuration for result ranking."""
    rrf_k: int = 60  # RRF constant (typical range: 10-100)

    # Method weights (should sum to ~1.0 for interpretability)
    # Updated: Image weight increased from 0.05 to 0.20 for better visibility
    semantic_weight: float = 0.35
    chunk_weight: float = 0.20
    wikilink_weight: float = 0.15
    fulltext_weight: float = 0.10
    image_weight: float = 0.20  # 4x increase from original 0.05

    # Boost factors
    recency_boost: bool = True
    recency_half_life_days: int = 30  # Notes lose half relevance after this

    # Image slot reservation
    min_image_slots: int = 2  # Reserve slots for images in top results
    image_min_threshold: float = 0.15  # Minimum score for reserved images

    max_results: int = 20


def get_dynamic_config(query: str, base_config: RankingConfig = None) -> RankingConfig:
    """
    Get ranking config with dynamic weights based on query type.

    If query is image-focused, boost image weight significantly.
    """
    if base_config is None:
        base_config = RankingConfig()

    if detect_image_query(query):
        # Image-focused query: boost image weight to 40%
        return RankingConfig(
            rrf_k=base_config.rrf_k,
            semantic_weight=0.25,
            chunk_weight=0.15,
            wikilink_weight=0.10,
            fulltext_weight=0.10,
            image_weight=0.40,  # Boosted for image queries
            recency_boost=base_config.recency_boost,
            recency_half_life_days=base_config.recency_half_life_days,
            min_image_slots=4,  # More image slots for image queries
            image_min_threshold=0.10,
            max_results=base_config.max_results,
        )

    if detect_document_query(query):
        # Document-focused query: boost document chunk weight
        return RankingConfig(
            rrf_k=base_config.rrf_k,
            semantic_weight=0.25,
            chunk_weight=0.30,  # Boost chunk weight for doc queries
            wikilink_weight=0.10,
            fulltext_weight=0.15,
            image_weight=0.10,
            recency_boost=base_config.recency_boost,
            recency_half_life_days=base_config.recency_half_life_days,
            min_image_slots=1,
            image_min_threshold=0.15,
            max_results=base_config.max_results,
        )

    return base_config


@dataclass
class RankedResult:
    """A result with combined ranking score."""
    result: RetrievalResult
    rrf_score: float = 0.0
    method_scores: Dict[str, float] = field(default_factory=dict)
    final_score: float = 0.0
    rank: int = 0
    contributing_methods: List[str] = field(default_factory=list)


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
        'document_chunk': config.chunk_weight,  # Document chunks same weight as note chunks
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


def deduplicate_results(
    results: List[RankedResult],
    max_chunks_per_source: int = 1,
) -> List[RankedResult]:
    """
    Remove duplicate sources, keeping highest-ranked version(s).

    For document_chunk sources, allows multiple chunks per document
    (up to max_chunks_per_source) with a quality threshold: only keep
    chunks scoring above 50% of the top chunk's score for that document.

    For notes/chunks, keeps 1 per parent note.

    Args:
        results: Ranked results to deduplicate
        max_chunks_per_source: Max chunks to keep per document (default 1)

    Returns:
        Deduplicated results
    """
    seen_notes: Set[int] = set()
    # Track per-document: count and top score
    doc_counts: Dict[int, int] = defaultdict(int)
    doc_top_scores: Dict[int, float] = {}
    deduplicated: List[RankedResult] = []

    for rr in results:
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
        elif rr.result.source_type == 'document_chunk':
            doc_id = rr.result.metadata.get('document_id')
            if doc_id:
                if doc_id not in doc_top_scores:
                    doc_top_scores[doc_id] = rr.final_score
                # Quality gate: skip if below 50% of top chunk score
                if rr.final_score < doc_top_scores[doc_id] * 0.5:
                    continue
                if doc_counts[doc_id] >= max_chunks_per_source:
                    continue
                doc_counts[doc_id] += 1

        deduplicated.append(rr)

    # Sort document chunks by position within each document for coherent context
    _sort_document_chunks_by_position(deduplicated)

    # Re-assign ranks
    for i, rr in enumerate(deduplicated):
        rr.rank = i + 1

    logger.debug(f"Deduplication: {len(results)} -> {len(deduplicated)} results")
    return deduplicated


def _sort_document_chunks_by_position(results: List[RankedResult]) -> None:
    """
    Sort document chunks from the same document by page_number/chunk_index
    while preserving relative ordering of other result types.
    """
    # Group consecutive document chunks from the same doc
    i = 0
    while i < len(results):
        if results[i].result.source_type != 'document_chunk':
            i += 1
            continue
        doc_id = results[i].result.metadata.get('document_id')
        j = i + 1
        while j < len(results):
            if (results[j].result.source_type == 'document_chunk'
                    and results[j].result.metadata.get('document_id') == doc_id):
                j += 1
            else:
                break
        if j - i > 1:
            chunk_slice = results[i:j]
            chunk_slice.sort(
                key=lambda rr: rr.result.metadata.get('page_number', 0) or 0
            )
            results[i:j] = chunk_slice
        i = j


def ensure_image_slots(
    ranked: List[RankedResult],
    config: RankingConfig
) -> List[RankedResult]:
    """
    Ensure minimum number of images in top results if relevant images exist.

    Strategy:
    1. Count images in top 10 results
    2. If fewer than min_image_slots, promote best images from lower ranks
    3. Insert promoted images at positions 5-7 (middle of results)
    """
    top_n = min(10, len(ranked))
    top_results = ranked[:top_n]

    # Count images in top results
    image_count = sum(
        1 for r in top_results
        if r.result.source_type == 'image'
    )

    if image_count >= config.min_image_slots:
        return ranked  # Already enough images

    # Find best images not in top results
    images_outside = [
        r for r in ranked[top_n:]
        if r.result.source_type == 'image'
        and r.final_score >= config.image_min_threshold
    ]

    if not images_outside:
        return ranked  # No images to promote

    # Promote images to reserved slots
    slots_needed = config.min_image_slots - image_count
    to_promote = images_outside[:slots_needed]

    if not to_promote:
        return ranked

    # Remove promoted images from their current positions
    promoted_keys = {
        (r.result.source_type, r.result.source_id)
        for r in to_promote
    }
    new_ranked = [
        r for r in ranked
        if (r.result.source_type, r.result.source_id) not in promoted_keys
    ]

    # Insert at middle positions (5-7)
    insert_pos = min(5, len(new_ranked))
    for img in to_promote:
        new_ranked.insert(insert_pos, img)
        insert_pos += 1

    # Re-assign ranks
    for i, r in enumerate(new_ranked):
        r.rank = i + 1

    logger.info(f"Image slot reservation: promoted {len(to_promote)} images to top results")
    return new_ranked


def enforce_source_diversity(
    ranked: List[RankedResult],
    max_daily_notes: int = 3
) -> List[RankedResult]:
    """
    Cap how many daily notes appear in top results to prevent dominance.

    Daily notes contain broad content that matches many queries semantically,
    crowding out more topically relevant notes.
    """
    kept = []
    demoted = []
    daily_count = 0

    for rr in ranked:
        title = (rr.result.title or '').strip()
        is_daily = title.startswith('Daily Note')

        if is_daily and daily_count >= max_daily_notes:
            demoted.append(rr)
        else:
            kept.append(rr)
            if is_daily:
                daily_count += 1

    combined = kept + demoted
    for i, rr in enumerate(combined):
        rr.rank = i + 1

    if demoted:
        logger.info(f"Source diversity: demoted {len(demoted)} excess daily notes")
    return combined


def merge_and_rank(
    semantic_results: List[RetrievalResult],
    chunk_results: List[RetrievalResult],
    graph_results: List[RetrievalResult],
    fulltext_results: List[RetrievalResult],
    image_results: List[RetrievalResult],
    config: RankingConfig = None,
    query: str = None,
    title_results: List[RetrievalResult] = None
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
        query: Original query (for dynamic weight adjustment)

    Returns:
        Combined and ranked results
    """
    # Get dynamic config based on query type
    if query and config is None:
        config = get_dynamic_config(query)
    elif config is None:
        config = RankingConfig()

    result_lists = {
        'semantic': semantic_results,
        'chunk_semantic': chunk_results,
        'wikilink': graph_results,
        'fulltext': fulltext_results,
    }

    # Add title/direct results if provided
    if title_results:
        result_lists['direct'] = title_results

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

    # Deduplicate (allow up to 3 chunks per document for better recall)
    ranked = deduplicate_results(ranked, max_chunks_per_source=3)

    # Apply image slot reservation
    ranked = ensure_image_slots(ranked, config)

    # Enforce source diversity (cap daily notes)
    ranked = enforce_source_diversity(ranked)

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
