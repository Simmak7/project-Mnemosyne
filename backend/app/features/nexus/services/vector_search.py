"""
Stage 2b: Vector Search Wrapper

Wraps existing retrieval services and adds batch missing-link detection
from co-retrieval patterns.
"""

import re
import logging
from typing import List, Optional
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from embeddings import generate_embedding
from features.rag_chat.services.retrieval import (
    RetrievalResult,
    RetrievalConfig,
    semantic_search_notes,
    semantic_search_chunks,
    fulltext_search_notes,
)
from features.rag_chat.services.image_retrieval import combined_image_retrieval
from features.rag_chat.services.graph_retrieval import (
    GraphTraversalConfig,
    graph_traversal,
)
from features.rag_chat.services.ranking import (
    RankingConfig,
    RankedResult,
    get_dynamic_config,
    reciprocal_rank_fusion,
    deduplicate_results,
    ensure_image_slots,
)

logger = logging.getLogger(__name__)


def _title_search(db: Session, query: str, owner_id: int, limit: int = 3) -> List[RetrievalResult]:
    """
    Find notes whose title closely matches words in the query.

    Uses ILIKE with normalized query tokens to catch references like
    'EN_US-AI-Principles' that semantic/fulltext search miss.
    """
    # Common words that match too many titles
    STOP_WORDS = {
        'tell', 'about', 'what', 'note', 'notes', 'show', 'find', 'give',
        'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have', 'has',
        'how', 'does', 'can', 'could', 'would', 'should', 'which', 'where',
        'know', 'anything', 'something', 'everything', 'related', 'titled',
        'called', 'named', 'document', 'documents', 'image', 'images',
        'any', 'all', 'some', 'your', 'you', 'my', 'me', 'its',
    }
    # Extract potential title tokens (3+ chars, alphanumeric/hyphens/underscores)
    tokens = re.findall(r'[\w-]{3,}', query)
    tokens = [t for t in tokens if t.lower() not in STOP_WORDS]
    if not tokens:
        return []

    # Build ILIKE conditions for each token
    conditions = []
    params = {"owner_id": owner_id, "limit": limit}
    for i, token in enumerate(tokens):
        key = f"t{i}"
        conditions.append(f"title ILIKE :{key}")
        params[key] = f"%{token}%"

    where = " OR ".join(conditions)
    try:
        result = db.execute(sql_text(f"""
            SELECT id, title, content
            FROM notes
            WHERE owner_id = :owner_id AND is_trashed = false
              AND LENGTH(TRIM(COALESCE(content, ''))) > 10
              AND ({where})
            ORDER BY LENGTH(title) ASC
            LIMIT :limit
        """), params)

        results = []
        for row in result:
            results.append(RetrievalResult(
                source_type='note',
                source_id=row.id,
                title=row.title or 'Untitled',
                content=row.content or '',
                similarity=0.85,
                retrieval_method='direct',
                metadata={'full_note': True, 'title_match': True}
            ))
        if results:
            logger.info(f"Title search found {len(results)} notes")
        return results
    except Exception as e:
        logger.error(f"Title search failed: {e}")
        return []


def nexus_vector_search(
    db: Session,
    query: str,
    owner_id: int,
    max_sources: int = 10,
    min_similarity: float = 0.4,
    include_images: bool = True,
    include_graph: bool = True,
) -> List[RankedResult]:
    """
    Run the full vector search + graph traversal pipeline.

    Reuses existing RAG retrieval, ranking, and graph traversal.
    """
    query_embedding = generate_embedding(query)
    if not query_embedding:
        logger.warning("NEXUS: Failed to generate embedding, falling back to fulltext")
        fulltext_results = fulltext_search_notes(db, query, owner_id, limit=max_sources)
        return _wrap_as_ranked(fulltext_results)

    # Note-level search uses a lower threshold (notes compress full docs into
    # one embedding, losing specificity). Chunk search keeps the user threshold.
    note_config = RetrievalConfig(
        min_similarity=max(0.3, min_similarity - 0.15),
        max_results=max_sources,
        include_notes=True,
        include_chunks=False,
        include_images=include_images,
    )
    chunk_config = RetrievalConfig(
        min_similarity=min_similarity,
        max_results=max_sources,
        include_notes=False,
        include_chunks=True,
        include_images=False,
    )

    # Multi-source retrieval
    semantic_results = semantic_search_notes(db, query_embedding, owner_id, note_config)
    chunk_results = semantic_search_chunks(db, query_embedding, owner_id, chunk_config)
    fulltext_results = fulltext_search_notes(db, query, owner_id, limit=5)
    title_results = _title_search(db, query, owner_id, limit=3)

    image_results = []
    if include_images:
        note_ids = [r.source_id for r in semantic_results if r.source_type == "note"]
        image_results = combined_image_retrieval(db, query, owner_id, note_ids, limit=5)

    graph_results = []
    seed_sources = semantic_results + title_results
    if include_graph and seed_sources:
        seed_ids = [r.source_id for r in seed_sources[:3] if r.source_type == "note"]
        if seed_ids:
            graph_results = graph_traversal(
                db, seed_ids, owner_id,
                GraphTraversalConfig(max_hops=2, max_results_per_hop=3)
            )

    # Build result lists with title as its own method (weight=1.0 for 'direct')
    config = get_dynamic_config(query, RankingConfig(max_results=max_sources))
    result_lists = {
        'semantic': semantic_results,
        'chunk_semantic': chunk_results,
        'wikilink': graph_results,
        'fulltext': fulltext_results,
    }
    if title_results:
        result_lists['direct'] = title_results
    for img in image_results:
        method = img.retrieval_method
        if method not in result_lists:
            result_lists[method] = []
        result_lists[method].append(img)
    result_lists = {k: v for k, v in result_lists.items() if v}

    ranked = reciprocal_rank_fusion(result_lists, config)
    ranked = deduplicate_results(ranked)
    ranked = ensure_image_slots(ranked, config)

    logger.info(
        f"NEXUS vector search: {len(ranked)} results "
        f"(sem={len(semantic_results)}, chunk={len(chunk_results)}, "
        f"ft={len(fulltext_results)}, title={len(title_results)}, "
        f"img={len(image_results)}, graph={len(graph_results)})"
    )

    return ranked


def _wrap_as_ranked(results: List[RetrievalResult]) -> List[RankedResult]:
    """Wrap basic retrieval results as RankedResult for consistency."""
    from features.rag_chat.services.ranking import RankedResult
    ranked = []
    for i, r in enumerate(results):
        ranked.append(RankedResult(
            result=r,
            final_score=r.similarity if hasattr(r, 'similarity') else 0.5,
            rank=i + 1,
            contributing_methods=[r.retrieval_method],
        ))
    return ranked
