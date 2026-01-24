"""
Semantic retrieval module for RAG system.

Provides multi-level retrieval:
- Note-level embeddings (existing)
- Chunk-level embeddings (more precise)
- Image-level embeddings (AI analysis content)

Uses pgvector cosine similarity for semantic search.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from models import Note, NoteChunk, Image, ImageChunk
from embeddings import generate_embedding

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result from semantic retrieval."""
    source_type: str  # 'note', 'chunk', 'image', 'image_chunk'
    source_id: int
    title: str
    content: str
    similarity: float
    retrieval_method: str = 'semantic'
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalConfig:
    """Configuration for retrieval."""
    min_similarity: float = 0.5
    max_results: int = 10
    include_notes: bool = True
    include_chunks: bool = True
    include_images: bool = True
    chunk_boost: float = 1.1  # Boost chunk results slightly (more precise)


def semantic_search_notes(
    db: Session,
    query_embedding: List[float],
    owner_id: int,
    config: RetrievalConfig = None
) -> List[RetrievalResult]:
    """
    Search notes by semantic similarity using note-level embeddings.

    Args:
        db: Database session
        query_embedding: Query embedding vector (768 dimensions)
        owner_id: User ID for filtering
        config: Retrieval configuration

    Returns:
        List of RetrievalResult objects sorted by similarity
    """
    if config is None:
        config = RetrievalConfig()

    if not config.include_notes:
        return []

    try:
        # Convert embedding to PostgreSQL array format
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        # Note: Use CAST() instead of :: to avoid SQLAlchemy parameter binding issues
        result = db.execute(text("""
            SELECT
                id,
                title,
                content,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM notes
            WHERE owner_id = :owner_id
              AND embedding IS NOT NULL
              AND (1 - (embedding <=> CAST(:query_embedding AS vector))) >= :min_similarity
            ORDER BY similarity DESC
            LIMIT :max_results
        """), {
            "query_embedding": embedding_str,
            "owner_id": owner_id,
            "min_similarity": config.min_similarity,
            "max_results": config.max_results
        })

        results = []
        for row in result:
            results.append(RetrievalResult(
                source_type='note',
                source_id=row.id,
                title=row.title or 'Untitled',
                content=row.content or '',
                similarity=float(row.similarity),
                retrieval_method='semantic',
                metadata={'full_note': True}
            ))

        logger.debug(f"Found {len(results)} notes via semantic search")
        return results

    except Exception as e:
        logger.error(f"Error in semantic note search: {e}")
        return []


def semantic_search_chunks(
    db: Session,
    query_embedding: List[float],
    owner_id: int,
    config: RetrievalConfig = None
) -> List[RetrievalResult]:
    """
    Search note chunks by semantic similarity for precise retrieval.

    Args:
        db: Database session
        query_embedding: Query embedding vector
        owner_id: User ID for filtering
        config: Retrieval configuration

    Returns:
        List of RetrievalResult objects sorted by similarity
    """
    if config is None:
        config = RetrievalConfig()

    if not config.include_chunks:
        return []

    try:
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        result = db.execute(text("""
            SELECT
                nc.id,
                nc.note_id,
                nc.content,
                nc.chunk_type,
                nc.char_start,
                nc.char_end,
                n.title AS note_title,
                1 - (nc.embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM note_chunks nc
            JOIN notes n ON nc.note_id = n.id
            WHERE n.owner_id = :owner_id
              AND nc.embedding IS NOT NULL
              AND (1 - (nc.embedding <=> CAST(:query_embedding AS vector))) >= :min_similarity
            ORDER BY similarity DESC
            LIMIT :max_results
        """), {
            "query_embedding": embedding_str,
            "owner_id": owner_id,
            "min_similarity": config.min_similarity,
            "max_results": config.max_results
        })

        results = []
        for row in result:
            # Apply chunk boost for more precise matches
            boosted_similarity = min(1.0, float(row.similarity) * config.chunk_boost)

            results.append(RetrievalResult(
                source_type='chunk',
                source_id=row.id,
                title=row.note_title or 'Untitled',
                content=row.content,
                similarity=boosted_similarity,
                retrieval_method='semantic',
                metadata={
                    'note_id': row.note_id,
                    'chunk_type': row.chunk_type,
                    'char_start': row.char_start,
                    'char_end': row.char_end
                }
            ))

        logger.debug(f"Found {len(results)} chunks via semantic search")
        return results

    except Exception as e:
        logger.error(f"Error in semantic chunk search: {e}")
        return []


def semantic_search_images(
    db: Session,
    query_embedding: List[float],
    owner_id: int,
    config: RetrievalConfig = None
) -> List[RetrievalResult]:
    """
    Search image chunks by semantic similarity.

    Args:
        db: Database session
        query_embedding: Query embedding vector
        owner_id: User ID for filtering
        config: Retrieval configuration

    Returns:
        List of RetrievalResult objects sorted by similarity
    """
    if config is None:
        config = RetrievalConfig()

    if not config.include_images:
        return []

    try:
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        result = db.execute(text("""
            SELECT
                ic.id,
                ic.image_id,
                ic.content,
                i.filename,
                i.filepath,
                1 - (ic.embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM image_chunks ic
            JOIN images i ON ic.image_id = i.id
            WHERE i.owner_id = :owner_id
              AND ic.embedding IS NOT NULL
              AND (1 - (ic.embedding <=> CAST(:query_embedding AS vector))) >= :min_similarity
            ORDER BY similarity DESC
            LIMIT :max_results
        """), {
            "query_embedding": embedding_str,
            "owner_id": owner_id,
            "min_similarity": config.min_similarity,
            "max_results": config.max_results
        })

        results = []
        for row in result:
            results.append(RetrievalResult(
                source_type='image',
                source_id=row.image_id,
                title=row.filename or 'Image',
                content=row.content,
                similarity=float(row.similarity),
                retrieval_method='semantic',
                metadata={
                    'chunk_id': row.id,
                    'filepath': row.filepath,
                    'filename': row.filename
                }
            ))

        logger.debug(f"Found {len(results)} image chunks via semantic search")
        return results

    except Exception as e:
        logger.error(f"Error in semantic image search: {e}")
        return []


def fulltext_search_notes(
    db: Session,
    query: str,
    owner_id: int,
    limit: int = 10
) -> List[RetrievalResult]:
    """
    Full-text search using PostgreSQL tsvector.

    Args:
        db: Database session
        query: Search query text
        owner_id: User ID for filtering
        limit: Maximum results

    Returns:
        List of RetrievalResult objects
    """
    try:
        # Convert query to tsquery format
        # Replace spaces with & for AND search
        ts_query = ' & '.join(query.split())

        result = db.execute(text("""
            SELECT
                id,
                title,
                content,
                ts_rank(
                    to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(content, '')),
                    plainto_tsquery('english', :query)
                ) AS rank
            FROM notes
            WHERE owner_id = :owner_id
              AND to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(content, ''))
                  @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :limit
        """), {
            "query": query,
            "owner_id": owner_id,
            "limit": limit
        })

        results = []
        for row in result:
            # Normalize rank to 0-1 range (ts_rank can exceed 1)
            normalized_rank = min(1.0, float(row.rank) / 10.0 + 0.3)

            results.append(RetrievalResult(
                source_type='note',
                source_id=row.id,
                title=row.title or 'Untitled',
                content=row.content or '',
                similarity=normalized_rank,
                retrieval_method='fulltext',
                metadata={'full_note': True}
            ))

        logger.debug(f"Found {len(results)} notes via full-text search")
        return results

    except Exception as e:
        logger.error(f"Error in full-text search: {e}")
        return []


def combined_semantic_search(
    db: Session,
    query: str,
    owner_id: int,
    config: RetrievalConfig = None
) -> List[RetrievalResult]:
    """
    Perform combined semantic search across notes, chunks, and images.

    Args:
        db: Database session
        query: Search query text
        owner_id: User ID for filtering
        config: Retrieval configuration

    Returns:
        Combined and deduplicated list of results
    """
    if config is None:
        config = RetrievalConfig()

    # Generate query embedding
    query_embedding = generate_embedding(query)
    if not query_embedding:
        logger.error("Failed to generate query embedding")
        return []

    results = []

    # Search notes
    if config.include_notes:
        note_results = semantic_search_notes(db, query_embedding, owner_id, config)
        results.extend(note_results)

    # Search chunks
    if config.include_chunks:
        chunk_results = semantic_search_chunks(db, query_embedding, owner_id, config)
        results.extend(chunk_results)

    # Search images
    if config.include_images:
        image_results = semantic_search_images(db, query_embedding, owner_id, config)
        results.extend(image_results)

    # Sort by similarity
    results.sort(key=lambda x: x.similarity, reverse=True)

    # Limit total results
    results = results[:config.max_results * 2]  # Allow some extra for deduplication

    logger.info(f"Combined semantic search returned {len(results)} results")
    return results


def get_note_by_id(db: Session, note_id: int, owner_id: int) -> Optional[RetrievalResult]:
    """
    Get a specific note as a RetrievalResult.

    Args:
        db: Database session
        note_id: Note ID
        owner_id: User ID for access check

    Returns:
        RetrievalResult or None if not found
    """
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == owner_id
    ).first()

    if not note:
        return None

    return RetrievalResult(
        source_type='note',
        source_id=note.id,
        title=note.title or 'Untitled',
        content=note.content or '',
        similarity=1.0,  # Direct fetch = perfect match
        retrieval_method='direct',
        metadata={'full_note': True}
    )


def get_image_by_id(db: Session, image_id: int, owner_id: int) -> Optional[RetrievalResult]:
    """
    Get a specific image as a RetrievalResult.

    Args:
        db: Database session
        image_id: Image ID
        owner_id: User ID for access check

    Returns:
        RetrievalResult or None if not found
    """
    image = db.query(Image).filter(
        Image.id == image_id,
        Image.owner_id == owner_id
    ).first()

    if not image:
        return None

    return RetrievalResult(
        source_type='image',
        source_id=image.id,
        title=image.filename or 'Image',
        content=image.ai_analysis_result or '',
        similarity=1.0,
        retrieval_method='direct',
        metadata={
            'filepath': image.filepath,
            'filename': image.filename
        }
    )
