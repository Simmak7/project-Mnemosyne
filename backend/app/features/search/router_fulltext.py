"""Search feature - Full-text search endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from core.auth import get_current_user
from models import User

from features.search import schemas
from features.search.logic.fulltext import (
    search_notes_fulltext,
    search_images_fulltext,
    search_tags_fuzzy,
    search_combined,
    search_by_tag,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


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
