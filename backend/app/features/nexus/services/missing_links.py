"""
Missing Link Detection

Finds pairs of semantically similar notes that aren't connected
via wikilinks, suggesting potential knowledge graph links.

Uses semantic_edges table (similarity > threshold) minus existing wikilinks.
"""

import logging
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session

from features.nexus.models import NexusLinkSuggestion

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.75
MAX_SUGGESTIONS = 50


def detect_missing_links(
    db: Session,
    owner_id: int,
    threshold: float = SIMILARITY_THRESHOLD,
    max_suggestions: int = MAX_SUGGESTIONS,
) -> Dict[str, Any]:
    """
    Detect missing links between semantically similar but unlinked notes.

    Args:
        db: Database session
        owner_id: User ID
        threshold: Minimum similarity for suggestion
        max_suggestions: Maximum suggestions to create

    Returns:
        Dict with detection results
    """
    try:
        # Find semantic edges above threshold that lack wikilinks
        result = db.execute(text("""
            SELECT
                se.source_note_id,
                se.target_note_id,
                se.similarity
            FROM semantic_edges se
            WHERE se.owner_id = :owner_id
              AND se.similarity >= :threshold
              AND NOT EXISTS (
                  SELECT 1 FROM note_links nw
                  WHERE nw.source_note_id = se.source_note_id
                    AND nw.target_note_id = se.target_note_id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM note_links nw
                  WHERE nw.source_note_id = se.target_note_id
                    AND nw.target_note_id = se.source_note_id
              )
            ORDER BY se.similarity DESC
            LIMIT :limit
        """), {
            "owner_id": owner_id,
            "threshold": threshold,
            "limit": max_suggestions,
        })

        new_suggestions = 0
        for row in result:
            # Check if suggestion already exists
            existing = db.query(NexusLinkSuggestion).filter(
                NexusLinkSuggestion.owner_id == owner_id,
                NexusLinkSuggestion.source_note_id == row.source_note_id,
                NexusLinkSuggestion.target_note_id == row.target_note_id,
            ).first()

            if not existing:
                db.add(NexusLinkSuggestion(
                    owner_id=owner_id,
                    source_note_id=row.source_note_id,
                    target_note_id=row.target_note_id,
                    similarity_score=row.similarity,
                ))
                new_suggestions += 1

        db.commit()

        total = db.query(NexusLinkSuggestion).filter(
            NexusLinkSuggestion.owner_id == owner_id,
            NexusLinkSuggestion.status == "pending",
        ).count()

        return {
            "status": "success",
            "new_suggestions": new_suggestions,
            "total_pending": total,
        }

    except Exception as e:
        logger.error(f"Missing link detection failed: {e}")
        db.rollback()
        return {"status": "failed", "error": str(e)}


def get_pending_suggestions(
    db: Session,
    owner_id: int,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Get pending link suggestions with note titles."""
    try:
        result = db.execute(text("""
            SELECT
                ls.id,
                ls.source_note_id,
                sn.title as source_title,
                ls.target_note_id,
                tn.title as target_title,
                ls.similarity_score,
                ls.co_retrieval_count
            FROM nexus_link_suggestions ls
            JOIN notes sn ON sn.id = ls.source_note_id
            JOIN notes tn ON tn.id = ls.target_note_id
            WHERE ls.owner_id = :owner_id AND ls.status = 'pending'
            ORDER BY ls.similarity_score DESC
            LIMIT :limit
        """), {"owner_id": owner_id, "limit": limit})

        return [
            {
                "id": row.id,
                "source_note_id": row.source_note_id,
                "source_note_title": row.source_title,
                "target_note_id": row.target_note_id,
                "target_note_title": row.target_title,
                "similarity_score": round(row.similarity_score, 3),
                "co_retrieval_count": row.co_retrieval_count,
            }
            for row in result
        ]
    except Exception as e:
        logger.error(f"Pending suggestions query failed: {e}")
        return []
