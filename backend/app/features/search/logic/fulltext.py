"""
Full-text search operations using PostgreSQL tsvector.

This module provides functions for:
- Full-text search on notes (title + content)
- Full-text search on images (filename + prompt + AI analysis)
- Fuzzy search on tags (using pg_trgm)
- Combined search across all entities

PostgreSQL Extensions Used:
- tsvector/tsquery: Full-text search with ranking
- pg_trgm: Trigram similarity for fuzzy tag matching
- GIN indexes: Fast full-text search indexing
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from models import Note, Image, Tag, NoteTag, ImageTag

logger = logging.getLogger(__name__)


def parse_search_query(query: str) -> str:
    """
    Parse user search query into PostgreSQL tsquery format.

    Handles:
    - Multiple words: "machine learning" -> "machine & learning"
    - Quoted phrases: '"exact phrase"' -> "exact <-> phrase"
    - Single words: "python" -> "python"

    Args:
        query: Raw search query from user

    Returns:
        PostgreSQL tsquery-compatible string
    """
    if not query or not query.strip():
        return ""

    # Remove extra whitespace
    query = query.strip()

    # For now, use simple AND logic between words
    # Future: Could add support for OR, NOT, phrase matching
    words = query.split()

    # Escape special characters and join with &
    escaped_words = [word.replace("'", "''") for word in words]
    return " & ".join(escaped_words)


def apply_date_filter(query_base, date_range: str, date_column: str):
    """
    Apply date range filter to a query.

    Args:
        query_base: SQLAlchemy query object
        date_range: One of: 'all', 'today', 'week', 'month', 'year'
        date_column: Name of the date column to filter on

    Returns:
        Query with date filter applied
    """
    if date_range == "all":
        return query_base

    now = datetime.utcnow()

    if date_range == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_range == "week":
        start_date = now - timedelta(days=7)
    elif date_range == "month":
        start_date = now - timedelta(days=30)
    elif date_range == "year":
        start_date = now - timedelta(days=365)
    else:
        return query_base  # Unknown range, return unfiltered

    return query_base.filter(text(f"{date_column} >= :start_date")).params(start_date=start_date)


def search_notes_fulltext(
    db: Session,
    query: str,
    owner_id: int,
    date_range: str = "all",
    sort_by: str = "relevance",
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Full-text search on notes using PostgreSQL tsvector.

    Searches across note title and content with relevance ranking.
    Uses ts_rank for relevance scoring based on term frequency.

    PostgreSQL Query:
    - Uses search_vector column (pre-computed tsvector)
    - Ranks results using ts_rank algorithm
    - Supports date filtering and multiple sort orders

    Args:
        db: Database session
        query: Search query string
        owner_id: User ID for multi-tenant filtering
        date_range: Date filter ('all', 'today', 'week', 'month', 'year')
        sort_by: Sort order ('relevance', 'date', 'title')
        limit: Maximum results to return

    Returns:
        List of note dictionaries with relevance scores
    """
    if not query or not query.strip():
        return []

    tsquery = parse_search_query(query)

    # Raw SQL query for full-text search with relevance ranking
    sql = text("""
        SELECT
            n.id,
            n.title,
            n.content,
            n.slug,
            n.created_at,
            n.updated_at,
            ts_rank(n.search_vector, to_tsquery('english', :tsquery)) as score,
            ARRAY(
                SELECT json_build_object('id', t.id, 'name', t.name)
                FROM tags t
                JOIN note_tags nt ON t.id = nt.tag_id
                WHERE nt.note_id = n.id
                ORDER BY t.name
                LIMIT 10
            ) as tags
        FROM notes n
        WHERE
            n.owner_id = :owner_id
            AND n.search_vector @@ to_tsquery('english', :tsquery)
            AND (:date_range = 'all' OR
                 (:date_range = 'today' AND n.created_at >= CURRENT_DATE) OR
                 (:date_range = 'week' AND n.created_at >= CURRENT_DATE - INTERVAL '7 days') OR
                 (:date_range = 'month' AND n.created_at >= CURRENT_DATE - INTERVAL '30 days') OR
                 (:date_range = 'year' AND n.created_at >= CURRENT_DATE - INTERVAL '365 days'))
        ORDER BY
            CASE
                WHEN :sort_by = 'relevance' THEN ts_rank(n.search_vector, to_tsquery('english', :tsquery))
                ELSE 0
            END DESC,
            CASE
                WHEN :sort_by = 'date' THEN n.created_at
                ELSE NULL
            END DESC,
            CASE
                WHEN :sort_by = 'title' THEN n.title
                ELSE NULL
            END ASC
        LIMIT :limit
    """)

    result = db.execute(sql, {
        "tsquery": tsquery,
        "owner_id": owner_id,
        "date_range": date_range,
        "sort_by": sort_by,
        "limit": limit
    })

    notes = []
    for row in result:
        notes.append({
            "type": "note",
            "id": row.id,
            "title": row.title,
            "content": row.content,
            "slug": row.slug,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "score": float(row.score),
            "tags": row.tags or []
        })

    logger.debug(f"Full-text search found {len(notes)} notes for query: {query}")
    return notes


def search_images_fulltext(
    db: Session,
    query: str,
    owner_id: int,
    date_range: str = "all",
    sort_by: str = "relevance",
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Full-text search on images using PostgreSQL tsvector.

    Searches across filename, prompt, and AI analysis result.

    Args:
        db: Database session
        query: Search query string
        owner_id: User ID for multi-tenant filtering
        date_range: Date filter ('all', 'today', 'week', 'month', 'year')
        sort_by: Sort order ('relevance', 'date')
        limit: Maximum results to return

    Returns:
        List of image dictionaries with relevance scores
    """
    if not query or not query.strip():
        return []

    tsquery = parse_search_query(query)

    sql = text("""
        SELECT
            i.id,
            i.filename,
            i.filepath,
            i.prompt,
            i.ai_analysis_status,
            i.ai_analysis_result,
            i.uploaded_at,
            ts_rank(i.search_vector, to_tsquery('english', :tsquery)) as score,
            ARRAY(
                SELECT json_build_object('id', t.id, 'name', t.name)
                FROM tags t
                JOIN image_tags it ON t.id = it.tag_id
                WHERE it.image_id = i.id
                ORDER BY t.name
                LIMIT 10
            ) as tags
        FROM images i
        WHERE
            i.owner_id = :owner_id
            AND i.search_vector @@ to_tsquery('english', :tsquery)
            AND (:date_range = 'all' OR
                 (:date_range = 'today' AND i.uploaded_at >= CURRENT_DATE) OR
                 (:date_range = 'week' AND i.uploaded_at >= CURRENT_DATE - INTERVAL '7 days') OR
                 (:date_range = 'month' AND i.uploaded_at >= CURRENT_DATE - INTERVAL '30 days') OR
                 (:date_range = 'year' AND i.uploaded_at >= CURRENT_DATE - INTERVAL '365 days'))
        ORDER BY
            CASE
                WHEN :sort_by = 'relevance' THEN ts_rank(i.search_vector, to_tsquery('english', :tsquery))
                ELSE 0
            END DESC,
            CASE
                WHEN :sort_by = 'date' THEN i.uploaded_at
                ELSE NULL
            END DESC
        LIMIT :limit
    """)

    result = db.execute(sql, {
        "tsquery": tsquery,
        "owner_id": owner_id,
        "date_range": date_range,
        "sort_by": sort_by,
        "limit": limit
    })

    images = []
    for row in result:
        images.append({
            "type": "image",
            "id": row.id,
            "filename": row.filename,
            "filepath": row.filepath,
            "prompt": row.prompt,
            "ai_analysis_status": row.ai_analysis_status,
            "ai_analysis_result": row.ai_analysis_result,
            "uploaded_at": row.uploaded_at.isoformat() if row.uploaded_at else None,
            "score": float(row.score),
            "tags": row.tags or []
        })

    logger.debug(f"Full-text search found {len(images)} images for query: {query}")
    return images


def search_tags_fuzzy(
    db: Session,
    query: str,
    owner_id: int,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Fuzzy search on tags using pg_trgm extension.

    Finds tags with names similar to the query using trigram similarity.
    Note: Tags are GLOBAL (shared across users) but filtered by usage context.

    PostgreSQL pg_trgm:
    - Uses similarity() function for scoring
    - Uses % operator for threshold matching
    - Requires GIN index with gin_trgm_ops

    Args:
        db: Database session
        query: Search query string
        owner_id: User ID for multi-tenant filtering (for usage counts)
        limit: Maximum results to return

    Returns:
        List of tag dictionaries with similarity scores and note counts
    """
    if not query or not query.strip():
        return []

    # Use pg_trgm similarity for fuzzy matching
    # Note: Tags are global but we show user's usage counts
    sql = text("""
        SELECT
            t.id,
            t.name,
            t.created_at,
            similarity(t.name, :query) as score,
            (SELECT COUNT(*) FROM note_tags nt
             JOIN notes n ON nt.note_id = n.id
             WHERE nt.tag_id = t.id AND n.owner_id = :owner_id) as note_count,
            (SELECT COUNT(*) FROM image_tags it
             JOIN images i ON it.image_id = i.id
             WHERE it.tag_id = t.id AND i.owner_id = :owner_id) as image_count
        FROM tags t
        WHERE
            t.name % :query  -- Trigram similarity operator
        ORDER BY
            similarity(t.name, :query) DESC
        LIMIT :limit
    """)

    result = db.execute(sql, {
        "query": query.lower(),
        "owner_id": owner_id,
        "limit": limit
    })

    tags = []
    for row in result:
        tags.append({
            "type": "tag",
            "id": row.id,
            "name": row.name,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "score": float(row.score),
            "note_count": row.note_count,
            "image_count": row.image_count
        })

    logger.debug(f"Fuzzy tag search found {len(tags)} tags for query: {query}")
    return tags


def search_combined(
    db: Session,
    query: str,
    owner_id: int,
    type_filter: str = "all",
    date_range: str = "all",
    sort_by: str = "relevance",
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Combined search across notes, images, and tags.

    Merges results from all search types and sorts by relevance.
    Uses weighted limit distribution: notes (50%), images (30%), tags (20%).

    Args:
        db: Database session
        query: Search query string
        owner_id: User ID for multi-tenant filtering
        type_filter: Filter by type ('all', 'notes', 'images', 'tags')
        date_range: Date filter ('all', 'today', 'week', 'month', 'year')
        sort_by: Sort order ('relevance', 'date', 'title')
        limit: Maximum results to return (distributed across types)

    Returns:
        List of mixed result dictionaries sorted by relevance
    """
    if not query or not query.strip():
        return []

    results = []

    # Distribute limit across result types
    # Give more weight to notes (50%), then images (30%), then tags (20%)
    if type_filter == "all":
        note_limit = int(limit * 0.5)
        image_limit = int(limit * 0.3)
        tag_limit = int(limit * 0.2)
    elif type_filter == "notes":
        note_limit = limit
        image_limit = 0
        tag_limit = 0
    elif type_filter == "images":
        note_limit = 0
        image_limit = limit
        tag_limit = 0
    elif type_filter == "tags":
        note_limit = 0
        image_limit = 0
        tag_limit = limit
    else:
        # Default to all if unknown filter
        note_limit = int(limit * 0.5)
        image_limit = int(limit * 0.3)
        tag_limit = int(limit * 0.2)

    # Search notes
    if note_limit > 0:
        notes = search_notes_fulltext(
            db, query, owner_id, date_range, sort_by, note_limit
        )
        results.extend(notes)

    # Search images
    if image_limit > 0:
        images = search_images_fulltext(
            db, query, owner_id, date_range, sort_by, image_limit
        )
        results.extend(images)

    # Search tags (tags don't have date filtering)
    if tag_limit > 0:
        tags = search_tags_fuzzy(db, query, owner_id, tag_limit)
        results.extend(tags)

    # Sort combined results by score (relevance) or date
    if sort_by == "relevance":
        results.sort(key=lambda x: x["score"], reverse=True)
    elif sort_by == "date":
        # Sort by date where available
        def get_date(item):
            if item["type"] == "note":
                return item.get("created_at", "")
            elif item["type"] == "image":
                return item.get("uploaded_at", "")
            elif item["type"] == "tag":
                return item.get("created_at", "")
            return ""
        results.sort(key=get_date, reverse=True)

    # Limit final results
    logger.info(f"Combined search returned {len(results[:limit])} results for query: {query}")
    return results[:limit]


def search_by_tag(
    db: Session,
    tag_name: str,
    owner_id: int,
    include_notes: bool = True,
    include_images: bool = True,
    limit: int = 100
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search for notes and images by tag name (exact match).

    Args:
        db: Database session
        tag_name: Exact tag name to search for
        owner_id: User ID for multi-tenant filtering
        include_notes: Include notes with this tag
        include_images: Include images with this tag
        limit: Maximum results per type

    Returns:
        Dictionary with 'notes' and 'images' lists
    """
    result = {"notes": [], "images": []}

    if not tag_name or not tag_name.strip():
        return result

    # Find tag by name (tags are global, case-insensitive)
    tag = db.query(Tag).filter(
        func.lower(Tag.name) == tag_name.lower()
    ).first()

    if not tag:
        return result

    # Get notes with this tag (filtered by owner)
    if include_notes:
        notes = db.query(Note).join(
            NoteTag, Note.id == NoteTag.note_id
        ).filter(
            NoteTag.tag_id == tag.id,
            Note.owner_id == owner_id
        ).limit(limit).all()

        result["notes"] = [
            {
                "type": "note",
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "slug": note.slug,
                "created_at": note.created_at.isoformat() if note.created_at else None,
                "updated_at": note.updated_at.isoformat() if note.updated_at else None
            }
            for note in notes
        ]

    # Get images with this tag (filtered by owner)
    if include_images:
        images = db.query(Image).join(
            ImageTag, Image.id == ImageTag.image_id
        ).filter(
            ImageTag.tag_id == tag.id,
            Image.owner_id == owner_id
        ).limit(limit).all()

        result["images"] = [
            {
                "type": "image",
                "id": image.id,
                "filename": image.filename,
                "filepath": image.filepath,
                "ai_analysis_status": image.ai_analysis_status,
                "uploaded_at": image.uploaded_at.isoformat() if image.uploaded_at else None
            }
            for image in images
        ]

    logger.debug(f"Tag search for '{tag_name}' found {len(result['notes'])} notes, {len(result['images'])} images")
    return result
