"""Search feature - Semantic search endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from core.auth import get_current_user
from models import User, Note

from features.search import schemas
from features.search.logic.semantic import (
    semantic_search,
    semantic_search_document_chunks,
    find_similar_notes,
    find_unlinked_mentions,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/semantic", response_model=schemas.SemanticSearchResponse)
async def semantic_search_endpoint(
    query: str = Query(..., min_length=1, description="Search query text"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Semantic search notes + document chunks by similarity. Rate limit: 20/min."""
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

        # Also search document chunks
        doc_results = semantic_search_document_chunks(
            db=db,
            query=query,
            owner_id=current_user.id,
            limit=max(5, limit // 2),
            threshold=threshold
        )

        # Convert note results
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

        # Convert document chunk results into the same schema
        for dr in doc_results:
            formatted_results.append(
                schemas.SimilarNoteResult(
                    id=dr["document_id"],
                    title=f"[PDF] {dr['display_name']}",
                    content=dr["content"],
                    similarity=dr["similarity"],
                    snippet=dr["content"][:200] + "...",
                    slug=None,
                    created_at=None,
                )
            )

        # Re-sort by similarity and limit
        formatted_results.sort(key=lambda r: r.similarity, reverse=True)
        formatted_results = formatted_results[:limit]

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
