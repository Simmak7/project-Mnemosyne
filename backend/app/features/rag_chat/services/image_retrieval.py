"""
Image retrieval module for RAG system.

Provides image-specific retrieval methods:
- Tag-based matching
- Linked images (via image_note_relations)
- Images connected to semantically matched notes
"""

import logging
from typing import List, Set, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from models import Image, Tag, Note
from .retrieval import RetrievalResult

logger = logging.getLogger(__name__)


def get_images_by_tags(
    db: Session,
    tag_names: List[str],
    owner_id: int,
    limit: int = 10
) -> List[RetrievalResult]:
    """
    Find images that share tags with the query entities.

    Args:
        db: Database session
        tag_names: List of tag names to match
        owner_id: User ID for filtering
        limit: Maximum results

    Returns:
        List of RetrievalResult objects
    """
    if not tag_names:
        return []

    try:
        # Normalize tag names (lowercase)
        normalized_tags = [t.lower().strip() for t in tag_names]

        result = db.execute(text("""
            SELECT
                i.id,
                i.filename,
                i.filepath,
                i.ai_analysis_result,
                COUNT(DISTINCT t.id) AS tag_matches,
                ARRAY_AGG(DISTINCT t.name) AS matched_tags
            FROM images i
            JOIN image_tags it ON i.id = it.image_id
            JOIN tags t ON it.tag_id = t.id
            WHERE i.owner_id = :owner_id
              AND LOWER(t.name) = ANY(:tag_names)
              AND i.ai_analysis_result IS NOT NULL
            GROUP BY i.id, i.filename, i.filepath, i.ai_analysis_result
            ORDER BY tag_matches DESC
            LIMIT :limit
        """), {
            "owner_id": owner_id,
            "tag_names": normalized_tags,
            "limit": limit
        })

        results = []
        for row in result:
            # Calculate similarity based on tag match ratio
            similarity = min(1.0, float(row.tag_matches) / len(tag_names) * 0.8 + 0.2)

            results.append(RetrievalResult(
                source_type='image',
                source_id=row.id,
                title=row.filename or 'Image',
                content=row.ai_analysis_result or '',
                similarity=similarity,
                retrieval_method='image_tag',
                metadata={
                    'filepath': row.filepath,
                    'filename': row.filename,
                    'matched_tags': list(row.matched_tags) if row.matched_tags else [],
                    'tag_match_count': row.tag_matches
                }
            ))

        logger.debug(f"Found {len(results)} images via tag matching")
        return results

    except Exception as e:
        logger.error(f"Error in image tag search: {e}")
        return []


def get_images_linked_to_notes(
    db: Session,
    note_ids: List[int],
    owner_id: int,
    limit: int = 10
) -> List[RetrievalResult]:
    """
    Find images linked to specific notes via image_note_relations.

    Args:
        db: Database session
        note_ids: List of note IDs to find linked images for
        owner_id: User ID for filtering
        limit: Maximum results

    Returns:
        List of RetrievalResult objects
    """
    if not note_ids:
        return []

    try:
        result = db.execute(text("""
            SELECT DISTINCT
                i.id,
                i.filename,
                i.filepath,
                i.ai_analysis_result,
                n.id AS linked_note_id,
                n.title AS linked_note_title
            FROM images i
            JOIN image_note_relations inr ON i.id = inr.image_id
            JOIN notes n ON inr.note_id = n.id
            WHERE i.owner_id = :owner_id
              AND n.id = ANY(:note_ids)
              AND i.ai_analysis_result IS NOT NULL
            LIMIT :limit
        """), {
            "owner_id": owner_id,
            "note_ids": note_ids,
            "limit": limit
        })

        results = []
        for row in result:
            results.append(RetrievalResult(
                source_type='image',
                source_id=row.id,
                title=row.filename or 'Image',
                content=row.ai_analysis_result or '',
                similarity=0.75,  # Linked images get moderate relevance
                retrieval_method='image_link',
                metadata={
                    'filepath': row.filepath,
                    'filename': row.filename,
                    'linked_note_id': row.linked_note_id,
                    'linked_note_title': row.linked_note_title
                }
            ))

        logger.debug(f"Found {len(results)} images linked to notes")
        return results

    except Exception as e:
        logger.error(f"Error in linked image search: {e}")
        return []


def get_images_from_note_tags(
    db: Session,
    note_ids: List[int],
    owner_id: int,
    limit: int = 10
) -> List[RetrievalResult]:
    """
    Find images that share tags with specific notes.

    This provides indirect image retrieval:
    Query → Notes (semantic) → Tags → Images (shared tags)

    Args:
        db: Database session
        note_ids: List of note IDs to find related images for
        owner_id: User ID for filtering
        limit: Maximum results

    Returns:
        List of RetrievalResult objects
    """
    if not note_ids:
        return []

    try:
        result = db.execute(text("""
            WITH note_tag_ids AS (
                SELECT DISTINCT nt.tag_id
                FROM note_tags nt
                WHERE nt.note_id = ANY(:note_ids)
            )
            SELECT DISTINCT
                i.id,
                i.filename,
                i.filepath,
                i.ai_analysis_result,
                COUNT(DISTINCT it.tag_id) AS shared_tags
            FROM images i
            JOIN image_tags it ON i.id = it.image_id
            WHERE i.owner_id = :owner_id
              AND it.tag_id IN (SELECT tag_id FROM note_tag_ids)
              AND i.ai_analysis_result IS NOT NULL
              AND i.id NOT IN (
                  SELECT image_id FROM image_note_relations
                  WHERE note_id = ANY(:note_ids)
              )
            GROUP BY i.id, i.filename, i.filepath, i.ai_analysis_result
            ORDER BY shared_tags DESC
            LIMIT :limit
        """), {
            "owner_id": owner_id,
            "note_ids": note_ids,
            "limit": limit
        })

        results = []
        for row in result:
            # Lower similarity since this is indirect matching
            similarity = min(0.7, 0.3 + float(row.shared_tags) * 0.1)

            results.append(RetrievalResult(
                source_type='image',
                source_id=row.id,
                title=row.filename or 'Image',
                content=row.ai_analysis_result or '',
                similarity=similarity,
                retrieval_method='image_tag_indirect',
                metadata={
                    'filepath': row.filepath,
                    'filename': row.filename,
                    'shared_tag_count': row.shared_tags
                }
            ))

        logger.debug(f"Found {len(results)} images via shared tags with notes")
        return results

    except Exception as e:
        logger.error(f"Error in indirect image search: {e}")
        return []


def extract_potential_tags(query: str) -> List[str]:
    """
    Extract potential tag names from a query.

    Looks for:
    - Hashtags (#python)
    - Quoted terms ("machine learning")
    - Important nouns/concepts

    Args:
        query: User query text

    Returns:
        List of potential tag names
    """
    import re

    tags = []

    # Extract hashtags
    hashtags = re.findall(r'#(\w+)', query)
    tags.extend([h.lower() for h in hashtags])

    # Extract quoted phrases
    quoted = re.findall(r'"([^"]+)"', query)
    tags.extend([q.lower().strip() for q in quoted])

    # Extract capitalized words (potential topics)
    # Skip common words
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when', 'where', 'who'}
    words = query.split()
    for word in words:
        clean = word.strip('?!.,;:').lower()
        if len(clean) > 2 and clean not in stop_words:
            if word[0].isupper() or clean not in stop_words:
                tags.append(clean)

    # Deduplicate while preserving order
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)

    return unique_tags[:10]  # Limit to 10 tags


def combined_image_retrieval(
    db: Session,
    query: str,
    owner_id: int,
    semantic_note_ids: List[int] = None,
    limit: int = 10
) -> List[RetrievalResult]:
    """
    Combine all image retrieval methods.

    Strategy:
    1. Tag-based matching from query
    2. Images linked to semantically matched notes
    3. Images sharing tags with matched notes

    Args:
        db: Database session
        query: User query text
        owner_id: User ID for filtering
        semantic_note_ids: Note IDs from semantic search (for linked images)
        limit: Maximum results

    Returns:
        Combined list of image results
    """
    results = []
    seen_ids: Set[int] = set()

    # 1. Tag-based retrieval
    potential_tags = extract_potential_tags(query)
    if potential_tags:
        tag_results = get_images_by_tags(db, potential_tags, owner_id, limit=limit)
        for r in tag_results:
            if r.source_id not in seen_ids:
                results.append(r)
                seen_ids.add(r.source_id)

    # 2. Linked images
    if semantic_note_ids:
        linked_results = get_images_linked_to_notes(db, semantic_note_ids, owner_id, limit=limit)
        for r in linked_results:
            if r.source_id not in seen_ids:
                results.append(r)
                seen_ids.add(r.source_id)

        # 3. Shared tag images
        shared_tag_results = get_images_from_note_tags(db, semantic_note_ids, owner_id, limit=limit)
        for r in shared_tag_results:
            if r.source_id not in seen_ids:
                results.append(r)
                seen_ids.add(r.source_id)

    # Sort by similarity
    results.sort(key=lambda x: x.similarity, reverse=True)

    logger.info(f"Combined image retrieval returned {len(results)} results")
    return results[:limit]
