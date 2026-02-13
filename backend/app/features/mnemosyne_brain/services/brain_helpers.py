"""
Brain Builder Helpers - Data collection and file storage utilities.

Extracted from brain_builder.py to keep files under 250 lines.
"""

import logging
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

import models
from features.mnemosyne_brain.models.brain_file import BrainFile
from features.mnemosyne_brain.services.topic_generator import compute_content_hash

logger = logging.getLogger(__name__)


def try_generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding, return None on failure."""
    try:
        from embeddings import generate_embedding
        return generate_embedding(text)
    except Exception as e:
        logger.warning(f"Embedding generation failed: {e}")
        return None


def collect_user_notes(db: Session, user_id: int) -> List[Dict]:
    """Collect all non-trashed notes for the user."""
    notes = (
        db.query(models.Note)
        .filter(models.Note.owner_id == user_id, models.Note.is_trashed == False)  # noqa: E712
        .order_by(models.Note.updated_at.desc().nullslast())
        .all()
    )
    return [
        {"id": n.id, "title": n.title or "Untitled", "content": n.content or "", "community_id": n.community_id}
        for n in notes
    ]


def group_notes_by_community(notes: List[Dict]) -> Dict[int, List[Dict]]:
    """Group notes by their community_id. Notes without community go to -1."""
    groups: Dict[int, List[Dict]] = {}
    for note in notes:
        groups.setdefault(note.get("community_id") or -1, []).append(note)
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


def upsert_brain_file(db: Session, user_id: int, build_id: int, data: Dict):
    """Insert or update a brain file."""
    file_key = data["file_key"]
    content = data.get("content", "")
    content_hash = compute_content_hash(content)

    existing = (
        db.query(BrainFile)
        .filter(BrainFile.owner_id == user_id, BrainFile.file_key == file_key)
        .first()
    )

    if existing:
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
        if "compressed_content" in data:
            existing.compressed_content = data["compressed_content"]
            existing.compressed_token_count = data.get("compressed_token_count", 0)
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
            compressed_content=data.get("compressed_content"),
            compressed_token_count=data.get("compressed_token_count", 0),
            build_id=build_id,
            embedding=data.get("embedding"),
        )
        db.add(new_file)

    db.flush()
