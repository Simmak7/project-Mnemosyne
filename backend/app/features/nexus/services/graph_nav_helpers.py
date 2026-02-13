"""
Graph Navigator Helpers

Database query functions for loading community notes, tag notes,
and building RetrievalResult objects from graph navigation.
"""

import logging
from typing import List, Dict, Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from features.rag_chat.services.retrieval import RetrievalResult
from features.rag_chat.services.graph_retrieval import get_outgoing_wikilinks

logger = logging.getLogger(__name__)


def load_community_notes(
    db: Session, owner_id: int, community_ids: List[int],
    candidates: Dict[int, Dict],
):
    """Load notes from selected communities."""
    try:
        result = db.execute(text("""
            SELECT id, title, LEFT(content, 500) as content, community_id
            FROM notes
            WHERE owner_id = :owner_id
              AND community_id = ANY(:community_ids)
              AND is_trashed = false
            LIMIT 50
        """), {"owner_id": owner_id, "community_ids": community_ids})

        for row in result:
            candidates[row.id] = {
                "title": row.title,
                "content": row.content or "",
                "score": 0.4,
                "community_id": row.community_id,
                "hop_count": 0,
            }
    except Exception as e:
        logger.error(f"Community notes query failed: {e}")
        db.rollback()


def load_tag_notes(
    db: Session, owner_id: int, tag_names: List[str],
    candidates: Dict[int, Dict],
):
    """Load or boost notes that have the selected tags."""
    try:
        result = db.execute(text("""
            SELECT DISTINCT n.id, n.title, LEFT(n.content, 500) as content
            FROM notes n
            JOIN note_tags nt ON nt.note_id = n.id
            JOIN tags t ON t.id = nt.tag_id
            WHERE n.owner_id = :owner_id
              AND LOWER(t.name) = ANY(:tag_names)
              AND n.is_trashed = false
            LIMIT 30
        """), {"owner_id": owner_id, "tag_names": tag_names})

        for row in result:
            if row.id in candidates:
                candidates[row.id]["score"] = candidates[row.id].get("score", 0) + 0.3
            else:
                candidates[row.id] = {
                    "title": row.title,
                    "content": row.content or "",
                    "score": 0.3,
                    "hop_count": 0,
                }
    except Exception as e:
        logger.error(f"Tag notes query failed: {e}")
        db.rollback()


def follow_wikilinks(
    db: Session, owner_id: int,
    sorted_candidates: List[tuple],
    existing_candidates: Dict[int, Dict],
) -> Dict[int, Dict]:
    """Follow wikilinks from top candidates to find connected notes."""
    wikilink_additions: Dict[int, Dict] = {}

    for note_id, info in sorted_candidates:
        wl_notes = get_outgoing_wikilinks(db, note_id, owner_id)
        for wl in wl_notes[:3]:
            wl_id = wl["id"]
            if wl_id not in existing_candidates and wl_id not in wikilink_additions:
                wikilink_additions[wl_id] = {
                    "title": wl["title"],
                    "content": wl.get("content", "")[:500],
                    "score": info.get("score", 0.5) * 0.6,
                    "hop_count": 1,
                    "via_note_id": note_id,
                }

    return wikilink_additions


def candidates_to_results(
    candidates: Dict[int, Dict], max_results: int
) -> List[RetrievalResult]:
    """Convert scored candidate dict to sorted RetrievalResult list."""
    sorted_all = sorted(
        candidates.items(), key=lambda x: x[1].get("score", 0), reverse=True
    )[:max_results]

    results = []
    for note_id, info in sorted_all:
        results.append(RetrievalResult(
            source_type="note",
            source_id=note_id,
            title=info.get("title", ""),
            content=info.get("content", "")[:800],
            similarity=info.get("score", 0.5),
            retrieval_method="graph_nav",
            metadata={
                "hop_count": info.get("hop_count", 0),
                "via_note_id": info.get("via_note_id"),
            },
        ))

    return results
