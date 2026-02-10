"""
Notes AI - Regenerate from Source Image

Re-analyzes linked images and regenerates note content,
preserving existing wikilinks and extracting tags.
"""

import re
import logging
from typing import List, Dict
from sqlalchemy.orm import Session

from core import config

logger = logging.getLogger(__name__)

OLLAMA_HOST = config.OLLAMA_HOST


def _extract_wikilinks_from_content(content: str) -> List[str]:
    """Extract all [[wikilink]] titles from note content."""
    if not content:
        return []
    return re.findall(r'\[\[([^\]]+)\]\]', content)


def regenerate_from_source(db: Session, note_id: int, owner_id: int) -> Dict:
    """
    Re-analyze the linked image and regenerate note content.
    Preserves existing wikilinks and extracts tags from new content.

    Args:
        db: Database session
        note_id: ID of the note to regenerate
        owner_id: Owner ID for authorization

    Returns:
        Dict with new_content, new_title, image_id, extracted_tags
    """
    from features.notes.models import Note
    from model_router import ModelRouter
    from sqlalchemy.orm import joinedload

    # Get the note with its linked images
    note = db.query(Note).options(
        joinedload(Note.images)
    ).filter(
        Note.id == note_id,
        Note.owner_id == owner_id
    ).first()

    if not note:
        raise ValueError("Note not found")

    # Preserve existing wikilinks before regeneration
    existing_wikilinks = _extract_wikilinks_from_content(note.content or "")

    linked_images = note.images
    if not linked_images:
        raise ValueError("No linked images found for this note.")

    image = linked_images[0]
    if not image.filepath:
        raise ValueError(f"Image file path not found for image ID {image.id}")

    # Resolve image path
    from pathlib import Path

    image_path = Path(image.filepath)
    if not image_path.exists():
        alt_path = Path(config.UPLOAD_DIR) / image.filepath
        if alt_path.exists():
            image_path = alt_path
        else:
            filename_only = Path(image.filepath).name
            alt_path = Path(config.UPLOAD_DIR) / filename_only
            if alt_path.exists():
                image_path = alt_path
            else:
                raise ValueError(f"Image file no longer exists at path: {image.filepath}")

    # Re-analyze the image
    router = ModelRouter(ollama_host=OLLAMA_HOST)
    resolved_path = str(image_path)
    logger.info(f"Regenerating analysis for note {note_id} from image {image.id}")

    result = router.analyze_image(image_path=resolved_path, timeout=120)

    if result.get("status") != "success":
        error_msg = result.get("error", "Unknown error from model router")
        raise Exception(f"AI analysis failed: {error_msg}")

    new_content = result.get("response", "")

    # Extract tags and format content
    from features.images.tasks_helpers import (
        generate_note_title, extract_image_metadata,
        extract_tags_from_ai_response, format_note_content
    )
    metadata = extract_image_metadata(resolved_path)
    new_title = generate_note_title(new_content, image.filename, metadata)
    extracted_tags = extract_tags_from_ai_response(new_content)

    # Format content with tags and preserved wikilinks
    formatted_content = format_note_content(
        ai_analysis=new_content,
        tags=extracted_tags,
        wikilinks=existing_wikilinks
    )

    logger.info(f"Regenerated note {note_id}: {len(formatted_content)} chars, "
                f"{len(extracted_tags)} tags, {len(existing_wikilinks)} preserved wikilinks")

    return {
        "new_content": formatted_content,
        "new_title": new_title,
        "image_id": image.id,
        "extracted_tags": extracted_tags
    }
