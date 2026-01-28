"""
Brain Builder - Orchestrates the full brain build pipeline.

Steps:
1. Collect all user notes
2. Run Louvain community detection
3. Group notes by community
4. Generate topic files for each community
5. Generate core files (askimap, mnemosyne, user_profile)
6. Preserve user-edited files (soul, memory)
7. Store all as BrainFile records with embeddings
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

import models
from features.mnemosyne_brain.models.brain_file import BrainFile
from features.mnemosyne_brain.models.brain_build_log import BrainBuildLog
from features.mnemosyne_brain.services.topic_generator import (
    generate_topic_file,
    compute_content_hash,
    estimate_tokens,
)
from features.mnemosyne_brain.services.core_file_generator import (
    generate_askimap,
    generate_mnemosyne_overview,
    generate_user_profile,
    get_default_soul,
    get_default_memory,
)

logger = logging.getLogger(__name__)


def _try_generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding, return None on failure."""
    try:
        from embeddings import generate_embedding
        return generate_embedding(text)
    except Exception as e:
        logger.warning(f"Embedding generation failed: {e}")
        return None


def _update_build_progress(db: Session, build_log: BrainBuildLog, pct: int, step: str):
    """Update build log progress."""
    build_log.progress_pct = pct
    build_log.current_step = step
    try:
        db.commit()
    except Exception:
        db.rollback()


def collect_user_notes(db: Session, user_id: int) -> List[Dict]:
    """Collect all non-trashed notes for the user."""
    notes = (
        db.query(models.Note)
        .filter(
            models.Note.owner_id == user_id,
            models.Note.is_trashed == False,  # noqa: E712
        )
        .order_by(models.Note.updated_at.desc().nullslast())
        .all()
    )
    return [
        {
            "id": n.id,
            "title": n.title or "Untitled",
            "content": n.content or "",
            "community_id": n.community_id,
        }
        for n in notes
    ]


def group_notes_by_community(notes: List[Dict]) -> Dict[int, List[Dict]]:
    """Group notes by their community_id. Notes without community go to -1."""
    groups: Dict[int, List[Dict]] = {}
    for note in notes:
        cid = note.get("community_id") or -1
        groups.setdefault(cid, []).append(note)
    return groups


def run_community_detection(db: Session, user_id: int) -> int:
    """Run Louvain community detection and return number of communities."""
    try:
        from features.graph.services.clustering import ClusteringService, CLUSTERING_AVAILABLE
        if not CLUSTERING_AVAILABLE:
            logger.warning("Clustering not available, skipping community detection")
            return 0
        service = ClusteringService(db, user_id)
        result = service.detect_communities()
        if result.community_count > 0:
            service.save_communities(result)
            db.commit()
        return result.community_count
    except Exception as e:
        logger.error(f"Community detection failed: {e}")
        db.rollback()
        return 0


def build_brain(db: Session, user_id: int, build_log: BrainBuildLog) -> None:
    """
    Full brain build pipeline.

    Args:
        db: Database session
        user_id: Owner ID
        build_log: Active build log to update progress
    """
    try:
        # Step 1: Collect notes
        _update_build_progress(db, build_log, 5, "Collecting notes")
        notes = collect_user_notes(db, user_id)
        build_log.notes_processed = len(notes)

        min_notes = getattr(models, "BRAIN_MIN_NOTES", 3)
        if len(notes) < min_notes:
            build_log.status = "failed"
            build_log.error_message = f"Need at least {min_notes} notes (found {len(notes)})"
            build_log.completed_at = datetime.utcnow()
            db.commit()
            return

        # Step 2: Run community detection
        _update_build_progress(db, build_log, 15, "Detecting communities")
        community_count = run_community_detection(db, user_id)
        build_log.communities_detected = community_count

        # Re-fetch notes (community_ids may have changed)
        notes = collect_user_notes(db, user_id)

        # Step 3: Group by community
        _update_build_progress(db, build_log, 25, "Grouping notes by topic")
        groups = group_notes_by_community(notes)

        # Step 4: Generate topic files
        _update_build_progress(db, build_log, 30, "Generating topic files")
        topic_results = []
        topic_index = 0
        total_groups = len(groups)

        for idx, (community_id, community_notes) in enumerate(groups.items()):
            pct = 30 + int((idx / max(total_groups, 1)) * 30)
            _update_build_progress(db, build_log, pct, f"Generating topic {topic_index + 1}")

            result = generate_topic_file(
                community_id=community_id,
                topic_index=topic_index,
                notes=community_notes,
            )
            if result:
                topic_results.append(result)
                topic_index += 1

        build_log.topic_files_generated = len(topic_results)

        # Prepare topics summary for core file generation
        topics_summary = [
            {
                "file_key": t.file_key,
                "title": t.title,
                "keywords": t.keywords,
                "content_preview": t.content[:200],
            }
            for t in topic_results
        ]

        # Step 5: Generate core files
        _update_build_progress(db, build_log, 65, "Generating askimap")
        askimap = generate_askimap(topics_summary)

        _update_build_progress(db, build_log, 70, "Generating overview")
        overview = generate_mnemosyne_overview(topics_summary, len(notes), community_count)

        _update_build_progress(db, build_log, 75, "Generating user profile")
        sample_notes = notes[:15]
        user_profile = generate_user_profile(topics_summary, sample_notes)

        # Step 6: Preserve user-edited soul/memory or create defaults
        _update_build_progress(db, build_log, 80, "Preserving user files")
        existing_soul = (
            db.query(BrainFile)
            .filter(BrainFile.owner_id == user_id, BrainFile.file_key == "soul")
            .first()
        )
        existing_memory = (
            db.query(BrainFile)
            .filter(BrainFile.owner_id == user_id, BrainFile.file_key == "memory")
            .first()
        )

        soul = None
        if not existing_soul or not existing_soul.is_user_edited:
            soul = get_default_soul()

        memory = None
        if not existing_memory:
            memory = get_default_memory()

        # Step 7: Store all files
        _update_build_progress(db, build_log, 85, "Saving brain files")
        total_tokens = 0

        # Save topic files
        for t in topic_results:
            embedding = _try_generate_embedding(t.content[:2000])
            _upsert_brain_file(db, user_id, build_log.id, {
                "file_key": t.file_key,
                "file_type": "topic",
                "title": t.title,
                "content": t.content,
                "community_id": t.community_id,
                "topic_keywords": t.keywords,
                "source_note_ids": t.source_note_ids,
                "token_count_approx": t.token_count_approx,
                "embedding": embedding,
            })
            total_tokens += t.token_count_approx

        # Save core files
        for core_file in [askimap, overview, user_profile]:
            _upsert_brain_file(db, user_id, build_log.id, core_file)
            total_tokens += core_file.get("token_count_approx", 0)

        if soul:
            _upsert_brain_file(db, user_id, build_log.id, soul)
            total_tokens += soul.get("token_count_approx", 0)

        if memory:
            _upsert_brain_file(db, user_id, build_log.id, memory)
            total_tokens += memory.get("token_count_approx", 0)

        # Clean up old topic files that no longer exist
        _update_build_progress(db, build_log, 95, "Cleaning up old topics")
        current_topic_keys = {t.file_key for t in topic_results}
        old_topics = (
            db.query(BrainFile)
            .filter(
                BrainFile.owner_id == user_id,
                BrainFile.file_type == "topic",
                ~BrainFile.file_key.in_(current_topic_keys) if current_topic_keys else True,
            )
            .all()
        )
        for old in old_topics:
            db.delete(old)

        # Mark all files as not stale
        db.query(BrainFile).filter(
            BrainFile.owner_id == user_id
        ).update({"is_stale": False})

        # Complete build
        build_log.total_tokens_generated = total_tokens
        build_log.status = "completed"
        build_log.progress_pct = 100
        build_log.current_step = "Complete"
        build_log.completed_at = datetime.utcnow()
        db.commit()

        logger.info(
            f"Brain build complete for user {user_id}: "
            f"{len(topic_results)} topics, {total_tokens} tokens"
        )

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


def _upsert_brain_file(db: Session, user_id: int, build_id: int, data: Dict):
    """Insert or update a brain file."""
    file_key = data["file_key"]
    content = data.get("content", "")

    existing = (
        db.query(BrainFile)
        .filter(BrainFile.owner_id == user_id, BrainFile.file_key == file_key)
        .first()
    )

    content_hash = compute_content_hash(content)

    if existing:
        # Don't overwrite user-edited core files
        if existing.is_user_edited and data.get("file_type") == "core":
            return
        existing.title = data.get("title", existing.title)
        existing.content = content
        existing.content_hash = content_hash
        existing.file_type = data.get("file_type", existing.file_type)
        existing.community_id = data.get("community_id", existing.community_id)
        existing.topic_keywords = data.get("topic_keywords", existing.topic_keywords)
        existing.source_note_ids = data.get("source_note_ids", existing.source_note_ids)
        existing.token_count_approx = data.get("token_count_approx", existing.token_count_approx)
        existing.build_id = build_id
        existing.version = (existing.version or 0) + 1
        existing.is_stale = False
        if "embedding" in data and data["embedding"]:
            existing.embedding = data["embedding"]
    else:
        new_file = BrainFile(
            owner_id=user_id,
            file_key=file_key,
            file_type=data.get("file_type", "core"),
            title=data.get("title", file_key),
            content=content,
            content_hash=content_hash,
            community_id=data.get("community_id"),
            topic_keywords=data.get("topic_keywords"),
            source_note_ids=data.get("source_note_ids"),
            token_count_approx=data.get("token_count_approx"),
            build_id=build_id,
            embedding=data.get("embedding"),
        )
        db.add(new_file)

    db.flush()
