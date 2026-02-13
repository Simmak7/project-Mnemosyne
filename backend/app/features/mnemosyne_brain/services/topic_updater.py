"""
Topic Updater - Single-topic regeneration and master map updates.

Used by the incremental updater to regenerate individual topics
without a full brain rebuild.
"""

import logging
from typing import Dict

from sqlalchemy.orm import Session

import models
from features.mnemosyne_brain.models.brain_file import BrainFile
from features.mnemosyne_brain.services.topic_generator import (
    generate_topic_file,
    compress_topic_content,
    compute_content_hash,
    estimate_tokens,
)
from features.mnemosyne_brain.services.brain_helpers import try_generate_embedding

logger = logging.getLogger(__name__)


def regenerate_topic(db: Session, user_id: int, topic: BrainFile) -> bool:
    """Regenerate a single topic from its current source notes."""
    source_ids = topic.source_note_ids or []
    if not source_ids:
        return False

    notes = db.query(models.Note).filter(
        models.Note.id.in_(source_ids),
        models.Note.owner_id == user_id,
        models.Note.is_trashed == False,  # noqa: E712
    ).all()
    if not notes:
        return False

    notes_data = [
        {"id": n.id, "title": n.title or "Untitled", "content": n.content or ""}
        for n in notes
    ]

    try:
        topic_idx = int(topic.file_key.split("_")[1])
    except (ValueError, IndexError):
        topic_idx = 0

    result = generate_topic_file(topic.community_id or -1, topic_idx, notes_data)
    if not result:
        logger.warning(f"Failed to regenerate {topic.file_key}")
        topic.is_stale = True
        return False

    compress_topic_content(result)

    topic.title = result.title
    topic.content = result.content
    topic.content_hash = compute_content_hash(result.content)
    topic.token_count_approx = result.token_count_approx
    topic.compressed_content = result.compressed_content
    topic.compressed_token_count = result.compressed_token_count
    topic.topic_keywords = result.keywords
    topic.source_note_ids = [n.id for n in notes]
    topic.version = (topic.version or 0) + 1
    topic.is_stale = False

    embedding = try_generate_embedding(result.content[:2000])
    if embedding:
        topic.embedding = embedding

    return True


def create_micro_topic(db: Session, user_id: int, note: Dict):
    """Create a small topic file for a single orphaned note."""
    max_idx = _get_max_topic_index(db, user_id)
    new_idx = max_idx + 1

    result = generate_topic_file(community_id=-1, topic_index=new_idx, notes=[note])
    if not result:
        content = f"# {note['title']}\n\n{note['content'][:800]}"
        db.add(BrainFile(
            owner_id=user_id, file_key=f"topic_{new_idx}", file_type="topic",
            title=note["title"], content=content,
            content_hash=compute_content_hash(content),
            source_note_ids=[note["id"]],
            token_count_approx=estimate_tokens(content),
        ))
        return

    compress_topic_content(result)
    embedding = try_generate_embedding(result.content[:2000])

    db.add(BrainFile(
        owner_id=user_id, file_key=result.file_key, file_type="topic",
        title=result.title, content=result.content,
        content_hash=compute_content_hash(result.content),
        community_id=result.community_id, topic_keywords=result.keywords,
        source_note_ids=result.source_note_ids,
        token_count_approx=result.token_count_approx,
        compressed_content=result.compressed_content,
        compressed_token_count=result.compressed_token_count,
        embedding=embedding,
    ))


def update_master_map(db: Session, user_id: int):
    """Regenerate mnemosyne.md knowledge map from current compressed summaries."""
    from features.mnemosyne_brain.services.core_file_generator import generate_mnemosyne_overview
    from features.mnemosyne_brain.services.brain_helpers import upsert_brain_file

    topics = db.query(BrainFile).filter(
        BrainFile.owner_id == user_id, BrainFile.file_type == "topic"
    ).all()
    if not topics:
        return

    topics_summary = [
        {"file_key": t.file_key, "title": t.title,
         "keywords": t.topic_keywords or [], "content_preview": (t.content or "")[:200]}
        for t in topics
    ]
    compressed = [
        {"file_key": t.file_key, "title": t.title, "summary": t.compressed_content}
        for t in topics if t.compressed_content
    ]
    note_count = db.query(models.Note).filter(
        models.Note.owner_id == user_id, models.Note.is_trashed == False,  # noqa: E712
    ).count()

    overview = generate_mnemosyne_overview(
        topics_summary, note_count, len(topics),
        compressed_summaries=compressed if compressed else None,
    )

    existing = db.query(BrainFile).filter(
        BrainFile.owner_id == user_id, BrainFile.file_key == "mnemosyne"
    ).first()
    build_id = existing.build_id if existing else 0
    upsert_brain_file(db, user_id, build_id or 0, overview)


def _get_max_topic_index(db: Session, user_id: int) -> int:
    """Find the highest topic index among existing topic files."""
    topics = db.query(BrainFile.file_key).filter(
        BrainFile.owner_id == user_id, BrainFile.file_type == "topic"
    ).all()
    max_idx = -1
    for (key,) in topics:
        try:
            max_idx = max(max_idx, int(key.split("_")[1]))
        except (ValueError, IndexError):
            pass
    return max_idx
