"""
Brain Builder - Orchestrates the full brain build pipeline.

Steps: Collect notes -> Community detection -> Topic generation ->
       Topic compression -> Core file generation -> Store brain files
"""

import logging
from datetime import datetime
from typing import Dict

from sqlalchemy.orm import Session

from features.mnemosyne_brain.models.brain_file import BrainFile
from features.mnemosyne_brain.models.brain_build_log import BrainBuildLog
from features.mnemosyne_brain.services.topic_generator import (
    generate_topic_file,
    compress_topic_content,
)
from features.mnemosyne_brain.services.core_file_generator import (
    generate_askimap,
    generate_mnemosyne_overview,
    generate_user_profile,
    get_default_soul,
    get_default_memory,
)
from features.mnemosyne_brain.services.brain_helpers import (
    try_generate_embedding,
    collect_user_notes,
    group_notes_by_community,
    run_community_detection,
    upsert_brain_file,
)

logger = logging.getLogger(__name__)


def _update_progress(db: Session, build_log: BrainBuildLog, pct: int, step: str):
    """Update build log progress."""
    build_log.progress_pct = pct
    build_log.current_step = step
    try:
        db.commit()
    except Exception:
        db.rollback()


def build_brain(db: Session, user_id: int, build_log: BrainBuildLog) -> None:
    """Full brain build pipeline."""
    try:
        _update_progress(db, build_log, 5, "Collecting notes")
        notes = collect_user_notes(db, user_id)
        build_log.notes_processed = len(notes)

        if len(notes) < 3:
            build_log.status = "failed"
            build_log.error_message = f"Need at least 3 notes (found {len(notes)})"
            build_log.completed_at = datetime.utcnow()
            db.commit()
            return

        # Community detection
        _update_progress(db, build_log, 15, "Detecting communities")
        community_count = run_community_detection(db, user_id)
        build_log.communities_detected = community_count
        notes = collect_user_notes(db, user_id)  # Re-fetch with updated community IDs

        # Group and generate topics
        _update_progress(db, build_log, 25, "Grouping notes by topic")
        groups = group_notes_by_community(notes)

        _update_progress(db, build_log, 30, "Generating topic files")
        topic_results = []
        topic_index = 0
        total_groups = len(groups)

        for idx, (community_id, community_notes) in enumerate(groups.items()):
            pct = 30 + int((idx / max(total_groups, 1)) * 30)
            _update_progress(db, build_log, pct, f"Generating topic {topic_index + 1}")
            result = generate_topic_file(community_id, topic_index, community_notes)
            if result:
                topic_results.append(result)
                topic_index += 1

        build_log.topic_files_generated = len(topic_results)

        # Compress topics for knowledge map
        _update_progress(db, build_log, 60, "Compressing topics")
        for idx, t in enumerate(topic_results):
            pct = 60 + int((idx / max(len(topic_results), 1)) * 5)
            _update_progress(db, build_log, pct, f"Compressing topic {idx + 1}")
            compress_topic_content(t)

        topics_summary = [
            {"file_key": t.file_key, "title": t.title, "keywords": t.keywords, "content_preview": t.content[:200]}
            for t in topic_results
        ]

        # Generate core files
        _update_progress(db, build_log, 65, "Generating askimap")
        askimap = generate_askimap(topics_summary)

        _update_progress(db, build_log, 70, "Generating knowledge map")
        overview = generate_mnemosyne_overview(
            topics_summary, len(notes), community_count,
            compressed_summaries=[
                {"file_key": t.file_key, "title": t.title, "summary": t.compressed_content}
                for t in topic_results if t.compressed_content
            ],
        )

        _update_progress(db, build_log, 75, "Generating user profile")
        user_profile = generate_user_profile(topics_summary, notes[:15])

        # Preserve user-edited soul/memory or create defaults
        _update_progress(db, build_log, 80, "Preserving user files")
        soul = _get_soul_if_needed(db, user_id)
        memory = _get_memory_if_needed(db, user_id)

        # Store all files
        _update_progress(db, build_log, 85, "Saving brain files")
        total_tokens = _save_all_files(db, user_id, build_log.id, topic_results, askimap, overview, user_profile, soul, memory)

        # Clean up old topic files
        _update_progress(db, build_log, 95, "Cleaning up old topics")
        _cleanup_old_topics(db, user_id, {t.file_key for t in topic_results})

        db.query(BrainFile).filter(BrainFile.owner_id == user_id).update({"is_stale": False})

        build_log.total_tokens_generated = total_tokens
        build_log.status = "completed"
        build_log.progress_pct = 100
        build_log.current_step = "Complete"
        build_log.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Brain build complete for user {user_id}: {len(topic_results)} topics, {total_tokens} tokens")

    except Exception as e:
        logger.exception(f"Brain build failed for user {user_id}: {e}")
        db.rollback()
        try:
            build_log.status = "failed"
            build_log.error_message = str(e)[:500]
            build_log.completed_at = datetime.utcnow()
            db.commit()
        except Exception:
            db.rollback()


def _get_soul_if_needed(db: Session, user_id: int):
    """Return default soul dict if no user-edited soul exists."""
    existing = db.query(BrainFile).filter(BrainFile.owner_id == user_id, BrainFile.file_key == "soul").first()
    if not existing or not existing.is_user_edited:
        return get_default_soul()
    return None


def _get_memory_if_needed(db: Session, user_id: int):
    """Return default memory dict if no memory file exists."""
    existing = db.query(BrainFile).filter(BrainFile.owner_id == user_id, BrainFile.file_key == "memory").first()
    if not existing:
        return get_default_memory()
    return None


def _save_all_files(db, user_id, build_id, topic_results, askimap, overview, user_profile, soul, memory) -> int:
    """Save all brain files and return total token count."""
    total_tokens = 0
    for t in topic_results:
        embedding = try_generate_embedding(t.content[:2000])
        upsert_brain_file(db, user_id, build_id, {
            "file_key": t.file_key, "file_type": "topic", "title": t.title,
            "content": t.content, "compressed_content": t.compressed_content,
            "compressed_token_count": t.compressed_token_count, "community_id": t.community_id,
            "topic_keywords": t.keywords, "source_note_ids": t.source_note_ids,
            "token_count_approx": t.token_count_approx, "embedding": embedding,
        })
        total_tokens += t.token_count_approx

    for core_file in [askimap, overview, user_profile]:
        upsert_brain_file(db, user_id, build_id, core_file)
        total_tokens += core_file.get("token_count_approx", 0)

    for optional_file in [soul, memory]:
        if optional_file:
            upsert_brain_file(db, user_id, build_id, optional_file)
            total_tokens += optional_file.get("token_count_approx", 0)

    return total_tokens


def _cleanup_old_topics(db: Session, user_id: int, current_keys: set):
    """Delete topic files that no longer exist."""
    old_topics = (
        db.query(BrainFile)
        .filter(
            BrainFile.owner_id == user_id,
            BrainFile.file_type == "topic",
            ~BrainFile.file_key.in_(current_keys) if current_keys else True,
        )
        .all()
    )
    for old in old_topics:
        db.delete(old)
