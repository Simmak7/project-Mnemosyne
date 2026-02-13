"""
Navigation Cache Service

Builds and retrieves community map and tag overview caches used by
the GraphNavigator for single-LLM-call navigation.

Cache types:
- community_map: Compact description of each community (ID, name, note count, top terms)
- tag_overview: List of all tags with note counts
"""

import logging
from typing import Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session

from features.nexus.models import NexusNavigationCache

logger = logging.getLogger(__name__)


def get_navigation_cache(
    db: Session,
    owner_id: int,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieve cached community map and tag overview.

    Returns:
        Tuple of (community_map, tag_overview), either may be None
    """
    caches = db.query(NexusNavigationCache).filter(
        NexusNavigationCache.owner_id == owner_id,
    ).all()

    community_map = None
    tag_overview = None

    for cache in caches:
        if cache.cache_type == "community_map":
            community_map = cache.content
        elif cache.cache_type == "tag_overview":
            tag_overview = cache.content

    return community_map, tag_overview


def build_navigation_cache(db: Session, owner_id: int) -> dict:
    """
    Build navigation caches from current graph state.

    Reads community_metadata and tags tables to create compact
    text summaries for the navigation LLM.

    Returns:
        Dict with cache stats
    """
    community_map = _build_community_map(db, owner_id)
    tag_overview = _build_tag_overview(db, owner_id)

    # Upsert community_map
    _upsert_cache(db, owner_id, "community_map", community_map)
    _upsert_cache(db, owner_id, "tag_overview", tag_overview)

    db.commit()

    logger.info(
        f"Navigation cache built: community_map={len(community_map)} chars, "
        f"tag_overview={len(tag_overview)} chars"
    )

    return {
        "community_map_chars": len(community_map),
        "tag_overview_chars": len(tag_overview),
    }


def _build_community_map(db: Session, owner_id: int) -> str:
    """Build compact community map text."""
    try:
        result = db.execute(text("""
            SELECT
                cm.community_id,
                cm.label,
                cm.node_count,
                cm.top_terms
            FROM community_metadata cm
            WHERE cm.owner_id = :owner_id
            ORDER BY cm.node_count DESC
        """), {"owner_id": owner_id})

        lines = []
        for row in result:
            label = row.label or f"Cluster {row.community_id}"
            terms = row.top_terms or ""
            lines.append(
                f"[{row.community_id}] {label} ({row.node_count} notes): {terms}"
            )

        if not lines:
            return "No communities detected yet. Run Brain Build first."

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Community map build failed: {e}")
        db.rollback()
        return "Community data unavailable."


def _build_tag_overview(db: Session, owner_id: int) -> str:
    """Build compact tag overview text."""
    try:
        result = db.execute(text("""
            SELECT t.name, COUNT(nt.note_id) as note_count
            FROM tags t
            JOIN note_tags nt ON nt.tag_id = t.id
            JOIN notes n ON n.id = nt.note_id
            WHERE n.owner_id = :owner_id AND n.is_trashed = false
            GROUP BY t.name
            ORDER BY note_count DESC
            LIMIT 50
        """), {"owner_id": owner_id})

        tags = []
        for row in result:
            tags.append(f"#{row.name} ({row.note_count})")

        if not tags:
            return "No tags found."

        return ", ".join(tags)

    except Exception as e:
        logger.error(f"Tag overview build failed: {e}")
        db.rollback()
        return "Tag data unavailable."


def _upsert_cache(
    db: Session, owner_id: int, cache_type: str, content: str
):
    """Insert or update a navigation cache entry."""
    existing = db.query(NexusNavigationCache).filter(
        NexusNavigationCache.owner_id == owner_id,
        NexusNavigationCache.cache_type == cache_type,
    ).first()

    if existing:
        existing.content = content
        existing.version = (existing.version or 0) + 1
    else:
        db.add(NexusNavigationCache(
            owner_id=owner_id,
            cache_type=cache_type,
            content=content,
        ))
