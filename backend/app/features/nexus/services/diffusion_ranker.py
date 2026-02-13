"""
Stage 2c: Personalized PageRank Diffusion Ranker (DEEP mode)

Builds a sparse adjacency matrix from wikilinks, semantic edges, and shared tags,
then runs personalized PageRank with query-based seed distribution.

Complexity: O(edges x iterations), ~10ms for 500 notes.
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Try scipy for sparse matrix operations
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("numpy not available, diffusion ranker disabled")


def diffusion_rank(
    db: Session,
    owner_id: int,
    query_embedding: Optional[List[float]],
    damping: float = 0.85,
    max_iterations: int = 20,
    convergence_threshold: float = 1e-6,
    max_candidates: int = 500,
) -> Dict[int, float]:
    """
    Run personalized PageRank on the user's knowledge graph.

    Args:
        db: Database session
        owner_id: User ID
        query_embedding: Query embedding for personalization vector
        damping: PageRank damping factor
        max_iterations: Max iterations
        convergence_threshold: Convergence threshold
        max_candidates: Max notes to include

    Returns:
        Dict mapping note_id -> importance score (0-1)
    """
    if not NUMPY_AVAILABLE:
        logger.warning("Diffusion ranker unavailable (numpy missing)")
        return {}

    try:
        # Step 1: Load notes with embeddings
        notes = _load_note_ids(db, owner_id, max_candidates)
        if len(notes) < 2:
            return {}

        note_ids = [n["id"] for n in notes]
        id_to_idx = {nid: i for i, nid in enumerate(note_ids)}
        n = len(note_ids)

        # Step 2: Build adjacency matrix
        adj = np.zeros((n, n), dtype=np.float32)
        _add_wikilink_edges(db, note_ids, id_to_idx, adj, weight=1.0)
        _add_semantic_edges(db, owner_id, note_ids, id_to_idx, adj, weight=0.6)
        _add_shared_tag_edges(db, note_ids, id_to_idx, adj, weight=0.5)

        # Normalize columns
        col_sums = adj.sum(axis=0)
        col_sums[col_sums == 0] = 1.0
        adj = adj / col_sums

        # Step 3: Build personalization vector
        if query_embedding:
            personalization = _build_personalization(notes, query_embedding)
        else:
            personalization = np.ones(n, dtype=np.float32) / n

        # Step 4: Power iteration
        scores = np.ones(n, dtype=np.float32) / n
        for iteration in range(max_iterations):
            new_scores = (1 - damping) * personalization + damping * adj @ scores
            delta = np.abs(new_scores - scores).sum()
            scores = new_scores
            if delta < convergence_threshold:
                logger.info(f"Diffusion converged at iteration {iteration + 1}")
                break

        # Normalize to 0-1
        max_score = scores.max()
        if max_score > 0:
            scores = scores / max_score

        return {note_ids[i]: float(scores[i]) for i in range(n) if scores[i] > 0.01}

    except Exception as e:
        logger.error(f"Diffusion ranker failed: {e}")
        return {}


def _load_note_ids(db: Session, owner_id: int, limit: int) -> List[Dict]:
    """Load note IDs and embeddings for the user."""
    result = db.execute(text("""
        SELECT id, embedding
        FROM notes
        WHERE owner_id = :owner_id AND is_trashed = false
            AND embedding IS NOT NULL
        ORDER BY updated_at DESC
        LIMIT :limit
    """), {"owner_id": owner_id, "limit": limit})

    notes = []
    for row in result:
        embedding = None
        if row.embedding:
            try:
                embedding = list(row.embedding)
            except (TypeError, ValueError):
                pass
        notes.append({"id": row.id, "embedding": embedding})
    return notes


def _add_wikilink_edges(
    db: Session, note_ids: List[int], id_to_idx: Dict,
    adj: "np.ndarray", weight: float,
):
    """Add wikilink edges to adjacency matrix."""
    result = db.execute(text("""
        SELECT source_note_id, target_note_id
        FROM note_links
        WHERE source_note_id = ANY(:ids) AND target_note_id = ANY(:ids)
    """), {"ids": note_ids})

    for row in result:
        src_idx = id_to_idx.get(row.source_note_id)
        tgt_idx = id_to_idx.get(row.target_note_id)
        if src_idx is not None and tgt_idx is not None:
            adj[tgt_idx, src_idx] += weight
            adj[src_idx, tgt_idx] += weight * 0.5  # Backlink at half weight


def _add_semantic_edges(
    db: Session, owner_id: int, note_ids: List[int],
    id_to_idx: Dict, adj: "np.ndarray", weight: float,
):
    """Add semantic similarity edges to adjacency matrix."""
    try:
        result = db.execute(text("""
            SELECT source_note_id, target_note_id, similarity
            FROM semantic_edges
            WHERE owner_id = :owner_id
              AND source_note_id = ANY(:ids) AND target_note_id = ANY(:ids)
        """), {"owner_id": owner_id, "ids": note_ids})

        for row in result:
            src_idx = id_to_idx.get(row.source_note_id)
            tgt_idx = id_to_idx.get(row.target_note_id)
            if src_idx is not None and tgt_idx is not None:
                edge_weight = row.similarity * weight
                adj[tgt_idx, src_idx] += edge_weight
                adj[src_idx, tgt_idx] += edge_weight
    except Exception as e:
        logger.debug(f"Semantic edges query failed (may not exist): {e}")
        db.rollback()


def _add_shared_tag_edges(
    db: Session, note_ids: List[int], id_to_idx: Dict,
    adj: "np.ndarray", weight: float,
):
    """Add edges between notes sharing tags."""
    try:
        result = db.execute(text("""
            SELECT a.note_id as note_a, b.note_id as note_b
            FROM note_tags a
            JOIN note_tags b ON a.tag_id = b.tag_id AND a.note_id < b.note_id
            WHERE a.note_id = ANY(:ids) AND b.note_id = ANY(:ids)
        """), {"ids": note_ids})

        for row in result:
            a_idx = id_to_idx.get(row.note_a)
            b_idx = id_to_idx.get(row.note_b)
            if a_idx is not None and b_idx is not None:
                adj[a_idx, b_idx] += weight
                adj[b_idx, a_idx] += weight
    except Exception as e:
        logger.debug(f"Shared tag edges query failed: {e}")
        db.rollback()


def _build_personalization(
    notes: List[Dict], query_embedding: List[float]
) -> "np.ndarray":
    """Build personalization vector from cosine similarity to query."""
    n = len(notes)
    personalization = np.ones(n, dtype=np.float32)
    query_arr = np.array(query_embedding, dtype=np.float32)
    query_norm = np.linalg.norm(query_arr)

    if query_norm == 0:
        return personalization / n

    for i, note in enumerate(notes):
        if note.get("embedding"):
            try:
                note_arr = np.array(note["embedding"], dtype=np.float32)
                note_norm = np.linalg.norm(note_arr)
                if note_norm > 0:
                    sim = np.dot(query_arr, note_arr) / (query_norm * note_norm)
                    personalization[i] = max(sim, 0.01)
            except (ValueError, TypeError):
                pass

    # Normalize to probability distribution
    total = personalization.sum()
    if total > 0:
        personalization /= total

    return personalization
