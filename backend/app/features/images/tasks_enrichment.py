"""
Image task enrichment helpers - Phase 2 best-effort operations.

These functions handle tag extraction, note creation, and album linking
after the core image analysis has been committed. Failures here do NOT
affect the saved analysis result (two-phase commit pattern).
"""

import logging
from pathlib import Path
from typing import List, Optional

import crud
from features.albums.service import AlbumService
from features.images.tasks_helpers import (
    extract_image_metadata,
    generate_note_title,
    format_note_content,
    extract_tags_from_ai_response,
)

logger = logging.getLogger(__name__)


def extract_tags(
    task_id: str,
    analysis_text: str,
    content_metadata: dict,
    auto_tagging: bool,
    max_tags: int,
) -> List[str]:
    """Extract tags from AI response, returning empty list on failure."""
    if not auto_tagging:
        return []
    try:
        if content_metadata and content_metadata.get("tags"):
            tags = content_metadata["tags"]
        else:
            tags = extract_tags_from_ai_response(analysis_text)
        return tags[:max_tags]
    except Exception as e:
        logger.warning(f"[Task {task_id}] Tag extraction failed: {e}")
        return []


def add_tags_to_image(db, task_id: str, image, tags: List[str]) -> None:
    """Add tags to image. Each tag is independent - failures don't affect others."""
    for tag_name in tags:
        try:
            crud.add_tag_to_image(
                db=db, image_id=image.id, tag_name=tag_name, owner_id=image.owner_id,
            )
        except Exception as e:
            logger.warning(f"[Task {task_id}] Failed to add tag '{tag_name}' to image: {e}")
            try:
                db.rollback()
            except Exception:
                pass


def create_and_link_note(
    db,
    task_id: str,
    image,
    image_path: str,
    analysis_text: str,
    tags: List[str],
    wikilinks: List[str],
) -> None:
    """Create note, link to image, add tags. Best-effort."""
    try:
        metadata = extract_image_metadata(image_path)
        note_title = generate_note_title(
            ai_analysis=analysis_text,
            image_filename=Path(image_path).name,
            metadata=metadata,
        )
        note_content = format_note_content(
            ai_analysis=analysis_text, tags=tags, wikilinks=wikilinks,
        )

        note = crud.create_note(
            db=db,
            title=note_title,
            content=note_content,
            owner_id=image.owner_id,
            source='image_analysis',
            is_standalone=False,
        )
        logger.info(f"[Task {task_id}] Note created: ID {note.id}, title '{note_title}'")

        # Set display name (best-effort)
        try:
            crud.update_image_display_name(db=db, image_id=image.id, display_name=note_title)
        except Exception as e:
            logger.warning(f"[Task {task_id}] Failed to set display_name: {e}")
            db.rollback()

        # Link note to image (best-effort)
        try:
            crud.add_image_to_note(db=db, image_id=image.id, note_id=note.id)
        except Exception as e:
            logger.warning(f"[Task {task_id}] Failed to link note to image: {e}")
            db.rollback()

        # Add tags to note - each tag independent
        for tag_name in tags:
            try:
                crud.add_tag_to_note(
                    db=db, note_id=note.id, tag_name=tag_name, owner_id=image.owner_id,
                )
            except Exception as e:
                logger.warning(f"[Task {task_id}] Failed to add tag '{tag_name}' to note: {e}")
                try:
                    db.rollback()
                except Exception:
                    pass

    except Exception as e:
        logger.error(f"[Task {task_id}] Failed to create note: {e}", exc_info=True)
        db.rollback()


def add_to_album(db, task_id: str, image_id: int, album_id: int) -> None:
    """Add image to album. Best-effort."""
    try:
        image = crud.get_image(db, image_id=image_id)
        if image:
            added = AlbumService.add_images_to_album(
                db=db, album_id=album_id, owner_id=image.owner_id, image_ids=[image_id],
            )
            if added > 0:
                logger.info(f"[Task {task_id}] Added image {image_id} to album {album_id}")
    except Exception as e:
        logger.warning(f"[Task {task_id}] Failed to add image to album {album_id}: {e}")
        db.rollback()
