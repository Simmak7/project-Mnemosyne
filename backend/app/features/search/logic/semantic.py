"""
Semantic similarity search using pgvector embeddings.

This module provides functions for:
- Semantic search: Find notes similar to a text query
- Similar notes: Find notes similar to a given note
- Unlinked mentions: Find semantically related notes that aren't wikilinked

pgvector Integration:
- Uses cosine distance operator (<=>)
- Similarity = 1 - distance (so higher = more similar)
- Threshold filtering for quality control
- ivfflat index for efficient nearest neighbor search

Typical thresholds:
- 0.5: Very loose matching (exploratory)
- 0.7: Good default for related content
- 0.85: High confidence matches
- 0.95: Near-identical content
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from models import Note
from features.search.logic.embeddings import generate_embedding

logger = logging.getLogger(__name__)


def semantic_search(
    db: Session,
    query: str,
    owner_id: int,
    limit: int = 10,
    threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Search notes by semantic similarity to a text query.

    Generates an embedding for the query text and finds notes with similar
    embeddings using cosine similarity via pgvector.

    Args:
        db: Database session
        query: Search query text
        owner_id: User ID for multi-tenant filtering
        limit: Maximum results to return
        threshold: Minimum similarity threshold (0.0-1.0)

    Returns:
        List of note dictionaries sorted by similarity (highest first)

    Raises:
        ValueError: If embedding generation fails
    """
    logger.info(f"Semantic search: owner={owner_id}, query='{query[:50]}...', threshold={threshold}")

    # Generate embedding for query
    query_embedding = generate_embedding(query)

    if not query_embedding:
        logger.error("Failed to generate query embedding")
        raise ValueError("Failed to generate query embedding. Ollama service may be unavailable.")

    # Convert embedding list to pgvector string format: '[0.1,0.2,...]'
    embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'

    try:
        # Use pgvector's cosine similarity operator (<=>)
        # Lower distance = higher similarity, so we use 1 - distance
        query_text = text("""
            SELECT
                id,
                title,
                content,
                slug,
                created_at,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity,
                SUBSTRING(content, 1, 200) AS snippet
            FROM notes
            WHERE
                owner_id = :owner_id
                AND embedding IS NOT NULL
                AND (1 - (embedding <=> CAST(:query_embedding AS vector))) >= :threshold
            ORDER BY similarity DESC
            LIMIT :limit
        """)

        result = db.execute(
            query_text,
            {
                "query_embedding": embedding_str,
                "owner_id": owner_id,
                "threshold": threshold,
                "limit": limit
            }
        )

        rows = result.fetchall()

        results = [
            {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "slug": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
                "similarity": float(row[5]),
                "snippet": row[6] + ("..." if len(row[2] or "") > 200 else "")
            }
            for row in rows
        ]

        logger.info(f"Semantic search returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Semantic search failed: {str(e)}", exc_info=True)
        raise


def find_similar_notes(
    db: Session,
    note_id: int,
    owner_id: int,
    limit: int = 10,
    threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Find notes similar to a given note using embedding similarity.

    Uses the source note's embedding to find other notes with similar
    semantic content. Excludes the source note from results.

    Args:
        db: Database session
        note_id: ID of the source note
        owner_id: User ID for multi-tenant filtering
        limit: Maximum results to return
        threshold: Minimum similarity threshold (0.0-1.0)

    Returns:
        List of similar note dictionaries sorted by similarity

    Raises:
        ValueError: If source note not found or has no embedding
    """
    logger.info(f"Finding similar notes: note_id={note_id}, owner={owner_id}")

    # Verify note exists and has embedding
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == owner_id
    ).first()

    if not note:
        raise ValueError("Note not found")

    if note.embedding is None or (hasattr(note.embedding, '__len__') and len(note.embedding) == 0):
        raise ValueError("Note does not have an embedding yet")

    try:
        # Find similar notes using pgvector
        query_text = text("""
            SELECT
                id,
                title,
                content,
                slug,
                created_at,
                1 - (embedding <=> (SELECT embedding FROM notes WHERE id = :note_id)) AS similarity,
                SUBSTRING(content, 1, 200) AS snippet
            FROM notes
            WHERE
                owner_id = :owner_id
                AND id != :note_id
                AND embedding IS NOT NULL
                AND (1 - (embedding <=> (SELECT embedding FROM notes WHERE id = :note_id))) >= :threshold
            ORDER BY similarity DESC
            LIMIT :limit
        """)

        result = db.execute(
            query_text,
            {
                "note_id": note_id,
                "owner_id": owner_id,
                "threshold": threshold,
                "limit": limit
            }
        )

        rows = result.fetchall()

        results = [
            {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "slug": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
                "similarity": float(row[5]),
                "snippet": row[6] + ("..." if len(row[2] or "") > 200 else "")
            }
            for row in rows
        ]

        logger.info(f"Found {len(results)} similar notes for note {note_id}")
        return results

    except Exception as e:
        logger.error(f"Find similar notes failed: {str(e)}", exc_info=True)
        raise


def find_unlinked_mentions(
    db: Session,
    note_id: int,
    owner_id: int,
    limit: int = 10,
    threshold: float = 0.7,
    linked_note_ids: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Find unlinked mentions - notes that are semantically similar but NOT wikilinked.

    This is a key feature for knowledge graph building. It finds notes that SHOULD
    be linked based on semantic similarity, but currently aren't.

    The caller should provide the list of already-linked note IDs from wikilink
    resolution. This function then filters them out from semantic matches.

    Args:
        db: Database session
        note_id: ID of the source note
        owner_id: User ID for multi-tenant filtering
        limit: Maximum results to return
        threshold: Minimum similarity threshold (0.7 default for quality)
        linked_note_ids: List of note IDs that are already linked

    Returns:
        List of unlinked mention dictionaries sorted by similarity

    Raises:
        ValueError: If source note not found or has no embedding
    """
    logger.info(f"Finding unlinked mentions: note_id={note_id}, owner={owner_id}")

    # Verify note exists and has embedding
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == owner_id
    ).first()

    if not note:
        raise ValueError("Note not found")

    if note.embedding is None or (hasattr(note.embedding, '__len__') and len(note.embedding) == 0):
        raise ValueError("Note does not have an embedding yet")

    linked_ids = linked_note_ids or []

    try:
        # Find semantically similar notes
        query_text = text("""
            SELECT
                id,
                title,
                content,
                1 - (embedding <=> (SELECT embedding FROM notes WHERE id = :note_id)) AS similarity,
                SUBSTRING(content, 1, 150) AS snippet
            FROM notes
            WHERE
                owner_id = :owner_id
                AND id != :note_id
                AND embedding IS NOT NULL
                AND (1 - (embedding <=> (SELECT embedding FROM notes WHERE id = :note_id))) >= :threshold
            ORDER BY similarity DESC
        """)

        result = db.execute(
            query_text,
            {
                "note_id": note_id,
                "owner_id": owner_id,
                "threshold": threshold
            }
        )

        rows = result.fetchall()

        # Filter out notes that are already linked
        unlinked_results = [
            {
                "id": row[0],
                "title": row[1],
                "similarity": float(row[3]),
                "snippet": row[4] + ("..." if len(row[2] or "") > 150 else "")
            }
            for row in rows
            if row[0] not in linked_ids
        ]

        # Apply limit after filtering
        unlinked_results = unlinked_results[:limit]

        logger.info(
            f"Found {len(unlinked_results)} unlinked mentions for note {note_id} "
            f"(filtered from {len(rows)} similar notes)"
        )

        return unlinked_results

    except Exception as e:
        logger.error(f"Find unlinked mentions failed: {str(e)}", exc_info=True)
        raise


def semantic_search_document_chunks(
    db: Session,
    query: str,
    owner_id: int,
    limit: int = 10,
    threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Search document chunks by semantic similarity to a query.

    Generates a query embedding and finds document chunks with similar
    embeddings using cosine similarity via pgvector.

    Args:
        db: Database session
        query: Search query text
        owner_id: User ID for multi-tenant filtering
        limit: Maximum results to return
        threshold: Minimum similarity threshold (0.0-1.0)

    Returns:
        List of document chunk dicts sorted by similarity
    """
    logger.info(f"Document chunk search: owner={owner_id}, query='{query[:50]}...'")

    query_embedding = generate_embedding(query)
    if not query_embedding:
        logger.error("Failed to generate query embedding for document search")
        return []

    embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'

    try:
        query_text = text("""
            SELECT
                dc.id,
                dc.document_id,
                dc.content,
                dc.chunk_index,
                dc.page_number,
                d.filename,
                d.display_name,
                d.ai_summary,
                1 - (dc.embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE
                d.owner_id = :owner_id
                AND d.is_trashed = false
                AND dc.embedding IS NOT NULL
                AND (1 - (dc.embedding <=> CAST(:query_embedding AS vector))) >= :threshold
            ORDER BY similarity DESC
            LIMIT :limit
        """)

        result = db.execute(
            query_text,
            {
                "query_embedding": embedding_str,
                "owner_id": owner_id,
                "threshold": threshold,
                "limit": limit,
            }
        )

        rows = result.fetchall()
        results = [
            {
                "id": row[0],
                "document_id": row[1],
                "content": row[2],
                "chunk_index": row[3],
                "page_number": row[4],
                "filename": row[5],
                "display_name": row[6] or row[5],
                "document_summary": row[7],
                "similarity": float(row[8]),
                "type": "document_chunk",
            }
            for row in rows
        ]

        logger.info(f"Document chunk search returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Document chunk search failed: {str(e)}", exc_info=True)
        return []


def get_embedding_coverage(db: Session, owner_id: int) -> Dict[str, Any]:
    """
    Get statistics about embedding coverage for a user's notes.

    Useful for monitoring embedding generation progress and health.

    Args:
        db: Database session
        owner_id: User ID to check

    Returns:
        Dictionary with coverage statistics
    """
    try:
        query_text = text("""
            SELECT
                COUNT(*) as total_notes,
                COUNT(embedding) as notes_with_embedding,
                COUNT(*) - COUNT(embedding) as notes_without_embedding
            FROM notes
            WHERE owner_id = :owner_id
        """)

        result = db.execute(query_text, {"owner_id": owner_id})
        row = result.fetchone()

        total = row[0]
        with_embedding = row[1]
        without_embedding = row[2]

        return {
            "total_notes": total,
            "notes_with_embedding": with_embedding,
            "notes_without_embedding": without_embedding,
            "coverage_percent": round(with_embedding / total * 100, 2) if total > 0 else 0
        }

    except Exception as e:
        logger.error(f"Failed to get embedding coverage: {str(e)}", exc_info=True)
        return {
            "total_notes": 0,
            "notes_with_embedding": 0,
            "notes_without_embedding": 0,
            "coverage_percent": 0,
            "error": str(e)
        }
