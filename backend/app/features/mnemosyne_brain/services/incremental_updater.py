"""
Incremental Brain Updater - Updates affected topics when notes change.

Instead of a full brain rebuild (~60s), only regenerates the topic(s)
affected by a single note change (~5-15s).
"""

import logging
from typing import List, Optional, Dict

from sqlalchemy.orm import Session

import models
from features.mnemosyne_brain.models.brain_file import BrainFile
from features.mnemosyne_brain.services.topic_updater import (
    regenerate_topic,
    create_micro_topic,
    update_master_map,
)

logger = logging.getLogger(__name__)


def incremental_update(db: Session, user_id: int, note_id: int, change_type: str) -> Dict:
    """
    Handle note create/update/delete without full rebuild.

    Args:
        change_type: 'created' | 'updated' | 'deleted'

    Returns:
        Dict with status info
    """
    topic_count = db.query(BrainFile).filter(
        BrainFile.owner_id == user_id, BrainFile.file_type == "topic"
    ).count()

    if topic_count == 0:
        logger.info(f"No brain topics for user {user_id}, skipping incremental")
        return {"status": "skipped", "reason": "no_brain"}

    affected = _find_topics_for_note(db, user_id, note_id)
    updated = []

    if change_type == "created":
        updated = _handle_created(db, user_id, note_id, affected)
    elif change_type == "updated":
        for topic in affected:
            if regenerate_topic(db, user_id, topic):
                updated.append(topic.file_key)
    elif change_type == "deleted":
        updated = _handle_deleted(db, user_id, note_id, affected)

    if updated:
        update_master_map(db, user_id)
        _check_rebuild_recommendation(db, user_id)

    db.commit()
    return {"status": "updated", "topics_updated": updated}


def _handle_created(
    db: Session, user_id: int, note_id: int, affected: List[BrainFile]
) -> List[str]:
    """Handle a newly created note."""
    updated = []

    if not affected:
        note = _load_note(db, user_id, note_id)
        if not note:
            return []

        best_topic = _find_best_matching_topic(db, user_id, note)
        if best_topic:
            _add_note_to_topic(best_topic, note_id)
            affected = [best_topic]
        else:
            create_micro_topic(db, user_id, note)
            return ["micro_topic_created"]

    for topic in affected:
        if regenerate_topic(db, user_id, topic):
            updated.append(topic.file_key)

    return updated


def _handle_deleted(
    db: Session, user_id: int, note_id: int, affected: List[BrainFile]
) -> List[str]:
    """Handle a deleted note."""
    updated = []
    for topic in affected:
        _remove_note_from_topic(topic, note_id)
        remaining = topic.source_note_ids or []
        if not remaining:
            db.delete(topic)
            updated.append(f"{topic.file_key}_deleted")
        elif regenerate_topic(db, user_id, topic):
            updated.append(topic.file_key)
    return updated


def _find_topics_for_note(db: Session, user_id: int, note_id: int) -> List[BrainFile]:
    """Find all topic files that contain this note in source_note_ids."""
    topics = db.query(BrainFile).filter(
        BrainFile.owner_id == user_id, BrainFile.file_type == "topic"
    ).all()
    return [t for t in topics if note_id in (t.source_note_ids or [])]


def _load_note(db: Session, user_id: int, note_id: int) -> Optional[Dict]:
    """Load a single note as a dict."""
    note = db.query(models.Note).filter(
        models.Note.id == note_id,
        models.Note.owner_id == user_id,
        models.Note.is_trashed == False,  # noqa: E712
    ).first()
    if not note:
        return None
    return {"id": note.id, "title": note.title or "Untitled", "content": note.content or ""}


def _find_best_matching_topic(db: Session, user_id: int, note: Dict) -> Optional[BrainFile]:
    """Find the existing topic that best matches a new note via keyword overlap."""
    topics = db.query(BrainFile).filter(
        BrainFile.owner_id == user_id, BrainFile.file_type == "topic"
    ).all()
    if not topics:
        return None

    text = (note.get("title", "") + " " + note.get("content", "")[:300]).lower()
    note_words = {w.strip(".,!?;:()[]{}\"'") for w in text.split() if len(w) > 2}

    best_topic, best_score = None, 0.0

    for topic in topics:
        keywords = topic.topic_keywords or []
        if not keywords:
            continue
        kw_set = {k.lower() for k in keywords}
        score = len(note_words & kw_set) / max(len(kw_set), 1)

        title_words = set((topic.title or "").lower().split())
        score += len(note_words & title_words) * 0.3

        if score > best_score:
            best_score = score
            best_topic = topic

    return best_topic if best_score >= 0.3 else None


def _add_note_to_topic(topic: BrainFile, note_id: int):
    """Add a note ID to a topic's source_note_ids."""
    ids = list(topic.source_note_ids or [])
    if note_id not in ids:
        ids.append(note_id)
        topic.source_note_ids = ids


def _remove_note_from_topic(topic: BrainFile, note_id: int):
    """Remove a note ID from a topic's source_note_ids."""
    ids = list(topic.source_note_ids or [])
    if note_id in ids:
        ids.remove(note_id)
        topic.source_note_ids = ids


def _check_rebuild_recommendation(db: Session, user_id: int):
    """Log a warning if too many micro-topics exist (single-note topics)."""
    topics = db.query(BrainFile).filter(
        BrainFile.owner_id == user_id, BrainFile.file_type == "topic"
    ).all()
    micro_count = sum(1 for t in topics if len(t.source_note_ids or []) <= 1)
    if micro_count > 5:
        logger.info(
            f"User {user_id} has {micro_count} micro-topics. "
            f"Full rebuild recommended for better organization."
        )
