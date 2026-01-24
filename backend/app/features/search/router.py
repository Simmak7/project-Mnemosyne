"""
Search API router.

Provides endpoints for:
- Full-text search across notes, images, and tags
- Semantic similarity search using pgvector
- Finding similar notes
- Finding unlinked mentions
- Embedding management
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from core.auth import get_current_user
from models import User, Note

from features.search import schemas
from features.search.logic.fulltext import (
    search_notes_fulltext,
    search_images_fulltext,
    search_tags_fuzzy,
    search_combined,
    search_by_tag,
)
from features.search.logic.semantic import (
    semantic_search,
    find_similar_notes,
    find_unlinked_mentions,
    get_embedding_coverage,
)
from features.search.logic.embeddings import generate_embedding

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


# ============================================================================
# Full-text Search Endpoints
# ============================================================================

@router.get("/fulltext", response_model=schemas.FulltextSearchResponse)
async def fulltext_search(
    query: str = Query(..., min_length=1, alias="q", description="Search query text"),
    type_filter: str = Query("all", alias="type", description="Filter by type: 'all', 'notes', 'images', 'tags'"),
    date_range: str = Query("all", description="Date filter: 'all', 'today', 'week', 'month', 'year'"),
    sort_by: str = Query("relevance", description="Sort by: 'relevance', 'date', 'title'"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Full-text search across notes, images, and tags.

    Uses PostgreSQL tsvector for fast full-text search with relevance ranking.
    Results can be filtered by type, date range, and sorted by various criteria.

    **Rate limit:** 20 requests/minute

    **Example:**
    ```
    GET /search/fulltext?query=machine+learning&type_filter=notes&sort_by=relevance
    ```
    """
    logger.info(
        f"Full-text search: user={current_user.id}, query='{query}', "
        f"type={type_filter}, date={date_range}"
    )

    try:
        results = search_combined(
            db=db,
            query=query,
            owner_id=current_user.id,
            type_filter=type_filter,
            date_range=date_range,
            sort_by=sort_by,
            limit=limit
        )

        return schemas.FulltextSearchResponse(
            results=results,
            query=query,
            total=len(results),
            type_filter=type_filter,
            date_range=date_range
        )

    except Exception as e:
        logger.error(f"Full-text search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/notes", response_model=schemas.FulltextSearchResponse)
async def search_notes_only(
    query: str = Query(..., min_length=1, alias="q", description="Search query text"),
    date_range: str = Query("all", description="Date filter: 'all', 'today', 'week', 'month', 'year'"),
    sort_by: str = Query("relevance", description="Sort by: 'relevance', 'date', 'title'"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search notes only (optimized for note-specific search).

    Uses PostgreSQL tsvector for fast full-text search on note title and content.

    **Rate limit:** 30 requests/minute

    **Example:**
    ```
    GET /search/notes?q=machine+learning&date_range=week&sort_by=date
    ```
    """
    logger.info(f"Note search: user={current_user.id}, query='{query}'")

    try:
        results = search_notes_fulltext(
            db=db,
            query=query,
            owner_id=current_user.id,
            date_range=date_range,
            sort_by=sort_by,
            limit=limit
        )

        return schemas.FulltextSearchResponse(
            results=results,
            query=query,
            total=len(results),
            type_filter="notes",
            date_range=date_range
        )

    except Exception as e:
        logger.error(f"Note search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Note search failed: {str(e)}")


@router.get("/images", response_model=schemas.FulltextSearchResponse)
async def search_images_only(
    query: str = Query(..., min_length=1, alias="q", description="Search query text"),
    date_range: str = Query("all", description="Date filter: 'all', 'today', 'week', 'month', 'year'"),
    sort_by: str = Query("relevance", description="Sort by: 'relevance', 'date'"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search images only (searches filename, prompt, and AI analysis).

    Uses PostgreSQL tsvector for fast full-text search across image metadata.

    **Rate limit:** 30 requests/minute

    **Example:**
    ```
    GET /search/images?q=screenshot&date_range=month
    ```
    """
    logger.info(f"Image search: user={current_user.id}, query='{query}'")

    try:
        results = search_images_fulltext(
            db=db,
            query=query,
            owner_id=current_user.id,
            date_range=date_range,
            sort_by=sort_by,
            limit=limit
        )

        return schemas.FulltextSearchResponse(
            results=results,
            query=query,
            total=len(results),
            type_filter="images",
            date_range=date_range
        )

    except Exception as e:
        logger.error(f"Image search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")


@router.get("/tags", response_model=schemas.FulltextSearchResponse)
async def search_tags_only(
    query: str = Query(..., min_length=1, alias="q", description="Search query text"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fuzzy search on tags using trigram similarity.

    Uses PostgreSQL pg_trgm extension for fuzzy matching on tag names.
    Returns tags sorted by similarity score.

    **Rate limit:** 30 requests/minute

    **Example:**
    ```
    GET /search/tags?q=machne (will match "machine" with fuzzy search)
    ```
    """
    logger.info(f"Tag search: user={current_user.id}, query='{query}'")

    try:
        results = search_tags_fuzzy(
            db=db,
            query=query,
            owner_id=current_user.id,
            limit=limit
        )

        return schemas.FulltextSearchResponse(
            results=results,
            query=query,
            total=len(results),
            type_filter="tags",
            date_range="all"
        )

    except Exception as e:
        logger.error(f"Tag search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Tag search failed: {str(e)}")


@router.get("/by-tag/{tag_name}", response_model=schemas.TagSearchResponse)
async def search_by_tag_name(
    tag_name: str,
    include_notes: bool = Query(True, description="Include notes with this tag"),
    include_images: bool = Query(True, description="Include images with this tag"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results per type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search for notes and images by tag name.

    Returns all items tagged with the specified tag name (exact match).
    Tags are global but results are filtered to the current user's content.

    **Rate limit:** 30 requests/minute

    **Example:**
    ```
    GET /search/by-tag/machine-learning?include_images=false
    ```
    """
    logger.info(f"Search by tag: user={current_user.id}, tag='{tag_name}'")

    try:
        results = search_by_tag(
            db=db,
            tag_name=tag_name,
            owner_id=current_user.id,
            include_notes=include_notes,
            include_images=include_images,
            limit=limit
        )

        return schemas.TagSearchResponse(
            notes=results.get("notes", []),
            images=results.get("images", []),
            tag_name=tag_name
        )

    except Exception as e:
        logger.error(f"Search by tag failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ============================================================================
# Semantic Search Endpoints
# ============================================================================

@router.get("/semantic", response_model=schemas.SemanticSearchResponse)
async def semantic_search_endpoint(
    query: str = Query(..., min_length=1, description="Search query text"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Semantic search notes by similarity to a query.

    Generates an embedding for the query and finds notes with similar embeddings
    using cosine similarity via pgvector. Results sorted by similarity (highest first).

    **Rate limit:** 20 requests/minute

    **Thresholds:**
    - 0.5: Loose matching (exploratory)
    - 0.7: Good for related content
    - 0.85: High confidence matches

    **Example:**
    ```
    GET /search/semantic?query=machine+learning+basics&limit=5&threshold=0.6
    ```
    """
    logger.info(
        f"Semantic search: user={current_user.id}, query='{query}', "
        f"limit={limit}, threshold={threshold}"
    )

    try:
        results = semantic_search(
            db=db,
            query=query,
            owner_id=current_user.id,
            limit=limit,
            threshold=threshold
        )

        # Convert to response schema format
        formatted_results = [
            schemas.SimilarNoteResult(
                id=r["id"],
                title=r["title"],
                content=r["content"],
                similarity=r["similarity"],
                snippet=r["snippet"],
                slug=r.get("slug"),
                created_at=r.get("created_at")
            )
            for r in results
        ]

        return schemas.SemanticSearchResponse(
            results=formatted_results,
            query=query,
            total=len(formatted_results),
            threshold=threshold
        )

    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Semantic search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


@router.get("/notes/{note_id}/similar", response_model=schemas.SimilarNotesResponse)
async def find_similar_notes_endpoint(
    note_id: int,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    threshold: float = Query(0.6, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Find notes similar to a given note.

    Uses the note's embedding to find other notes with similar semantic content.
    Excludes the source note from results.

    **Rate limit:** 30 requests/minute

    **Example:**
    ```
    GET /search/notes/42/similar?limit=5&threshold=0.7
    ```
    """
    logger.info(
        f"Find similar notes: user={current_user.id}, note_id={note_id}, "
        f"limit={limit}, threshold={threshold}"
    )

    # Get source note for response
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    try:
        results = find_similar_notes(
            db=db,
            note_id=note_id,
            owner_id=current_user.id,
            limit=limit,
            threshold=threshold
        )

        formatted_results = [
            schemas.SimilarNoteResult(
                id=r["id"],
                title=r["title"],
                content=r["content"],
                similarity=r["similarity"],
                snippet=r["snippet"],
                slug=r.get("slug"),
                created_at=r.get("created_at")
            )
            for r in results
        ]

        return schemas.SimilarNotesResponse(
            results=formatted_results,
            source_note_id=note_id,
            source_note_title=note.title,
            total=len(formatted_results)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Find similar notes failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to find similar notes: {str(e)}")


@router.get("/notes/{note_id}/unlinked-mentions", response_model=schemas.UnlinkedMentionsResponse)
async def find_unlinked_mentions_endpoint(
    note_id: int,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Find unlinked mentions - notes semantically similar but NOT wikilinked.

    Key feature for knowledge graph building. Finds notes that SHOULD be linked
    based on semantic similarity but currently aren't.

    **Rate limit:** 30 requests/minute

    **Example:**
    ```
    GET /search/notes/42/unlinked-mentions?limit=5&threshold=0.75
    ```
    """
    logger.info(
        f"Find unlinked mentions: user={current_user.id}, note_id={note_id}, "
        f"limit={limit}, threshold={threshold}"
    )

    # Get source note
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    try:
        # Get existing wikilinks for this note using graph service
        from features.graph.service import resolve_wikilinks, get_backlinks

        # Get notes this note links to (outgoing)
        linked_note_ids = resolve_wikilinks(db, note_id, note.content or "", current_user.id)

        # Also get notes that link to us (backlinks/incoming)
        backlink_ids = get_backlinks(db, note_id, current_user.id)

        # Combine both - these are all notes already connected
        linked_note_ids = list(set(linked_note_ids + backlink_ids))

        results = find_unlinked_mentions(
            db=db,
            note_id=note_id,
            owner_id=current_user.id,
            limit=limit,
            threshold=threshold,
            linked_note_ids=linked_note_ids
        )

        formatted_results = [
            schemas.UnlinkedMentionResult(
                id=r["id"],
                title=r["title"],
                similarity=r["similarity"],
                snippet=r["snippet"]
            )
            for r in results
        ]

        return schemas.UnlinkedMentionsResponse(
            results=formatted_results,
            note_id=note_id,
            note_title=note.title,
            total=len(formatted_results)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Find unlinked mentions failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to find unlinked mentions: {str(e)}")


# ============================================================================
# Embedding Management Endpoints
# ============================================================================

@router.get("/embeddings/coverage", response_model=schemas.EmbeddingCoverageResponse)
async def get_embedding_coverage_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about embedding coverage.

    Returns the number of notes with/without embeddings and coverage percentage.
    Useful for monitoring embedding generation progress.

    **Rate limit:** 30 requests/minute
    """
    try:
        stats = get_embedding_coverage(db, current_user.id)
        return schemas.EmbeddingCoverageResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to get embedding coverage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes/{note_id}/regenerate-embedding", response_model=schemas.EmbeddingRegenerateResponse)
async def regenerate_note_embedding_endpoint(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger embedding regeneration for a note.

    Useful for fixing corrupted embeddings or updating after significant changes.

    **Rate limit:** 10 requests/minute

    **Example:**
    ```
    POST /search/notes/42/regenerate-embedding
    ```
    """
    # Import here to avoid circular imports
    from features.search.tasks import generate_note_embedding_task

    # Verify note exists
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    try:
        task = generate_note_embedding_task.delay(note_id)
        logger.info(f"Queued embedding regeneration for note {note_id}: task_id={task.id}")

        return schemas.EmbeddingRegenerateResponse(
            status="queued",
            note_id=note_id,
            task_id=task.id,
            message="Embedding generation queued. Check task status for progress."
        )

    except Exception as e:
        logger.error(f"Failed to queue embedding task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue embedding generation: {str(e)}"
        )
