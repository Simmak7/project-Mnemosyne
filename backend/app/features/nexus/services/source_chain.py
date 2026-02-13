"""
Source Chain Resolution

Traces each note back to its origin: was it manually created, generated
from an image analysis, or extracted from a PDF document?

Also resolves community membership and tag associations.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def resolve_source_chains(
    db: Session,
    note_ids: List[int],
    owner_id: int,
) -> Dict[int, Dict[str, Any]]:
    """
    Resolve origin chains for a batch of notes.

    Returns a dict keyed by note_id with origin info, community, and tags.

    Args:
        db: Database session
        note_ids: List of note IDs to resolve
        owner_id: User ID for filtering

    Returns:
        Dict mapping note_id -> {origin_type, artifact_id, community_id,
        community_name, tags, wikilink_targets}
    """
    if not note_ids:
        return {}

    chains: Dict[int, Dict[str, Any]] = {}

    try:
        # Batch query: note metadata + source + community
        result = db.execute(text("""
            SELECT
                n.id,
                n.source,
                n.community_id,
                cm.label as community_name,
                cm.top_terms as community_top_terms
            FROM notes n
            LEFT JOIN community_metadata cm ON cm.community_id = n.community_id
                AND cm.owner_id = n.owner_id
            WHERE n.id = ANY(:note_ids) AND n.owner_id = :owner_id
        """), {"note_ids": note_ids, "owner_id": owner_id})

        for row in result:
            chains[row.id] = {
                "origin_type": row.source or "manual",
                "artifact_id": None,
                "community_id": row.community_id,
                "community_name": row.community_name,
                "community_top_terms": row.community_top_terms,
                "tags": [],
                "wikilink_targets": [],
            }

        # Batch query: image origins (with filename)
        image_note_ids = [nid for nid in note_ids if nid in chains
                          and chains[nid]["origin_type"] == "image_analysis"]
        if image_note_ids:
            img_result = db.execute(text("""
                SELECT inr.note_id, inr.image_id,
                       COALESCE(i.display_name, i.filename) as artifact_filename
                FROM image_note_relations inr
                JOIN images i ON i.id = inr.image_id
                WHERE inr.note_id = ANY(:note_ids)
            """), {"note_ids": image_note_ids})
            for row in img_result:
                if row.note_id in chains:
                    chains[row.note_id]["artifact_id"] = row.image_id
                    chains[row.note_id]["artifact_filename"] = row.artifact_filename

        # Batch query: document origins (with filename)
        doc_note_ids = [nid for nid in note_ids if nid in chains
                        and chains[nid]["origin_type"] == "document_analysis"]
        if doc_note_ids:
            doc_result = db.execute(text("""
                SELECT summary_note_id, id as document_id,
                       COALESCE(display_name, filename) as artifact_filename
                FROM documents
                WHERE summary_note_id = ANY(:note_ids)
            """), {"note_ids": doc_note_ids})
            for row in doc_result:
                if row.summary_note_id in chains:
                    chains[row.summary_note_id]["artifact_id"] = row.document_id
                    chains[row.summary_note_id]["artifact_filename"] = row.artifact_filename

        # Batch query: tags
        tag_result = db.execute(text("""
            SELECT nt.note_id, t.name
            FROM note_tags nt
            JOIN tags t ON t.id = nt.tag_id
            WHERE nt.note_id = ANY(:note_ids)
        """), {"note_ids": note_ids})
        for row in tag_result:
            if row.note_id in chains:
                chains[row.note_id]["tags"].append(row.name)

        # Batch query: outgoing wikilinks
        wl_result = db.execute(text("""
            SELECT nw.source_note_id, nw.target_note_id, n.title
            FROM note_links nw
            JOIN notes n ON n.id = nw.target_note_id
            WHERE nw.source_note_id = ANY(:note_ids)
        """), {"note_ids": note_ids})
        for row in wl_result:
            if row.source_note_id in chains:
                chains[row.source_note_id]["wikilink_targets"].append({
                    "note_id": row.target_note_id,
                    "title": row.title,
                })

    except Exception as e:
        logger.error(f"Source chain resolution failed: {e}")
        db.rollback()

    return chains
