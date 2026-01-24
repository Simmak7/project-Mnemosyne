"""
Notes AI Enhancement Service

Provides AI-powered note enhancement features:
- Improve Title: Generate a better, more descriptive title
- Summarize: Create a concise summary of note content
- Suggest Wikilinks: Find potential [[wikilink]] connections
"""

import logging
import requests
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from core import config

logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_HOST = config.OLLAMA_HOST
RAG_MODEL = config.RAG_MODEL
RAG_TIMEOUT = 60  # Shorter timeout for quick operations


def call_ollama(prompt: str, system_prompt: str, max_tokens: int = 256) -> str:
    """Call Ollama API for text generation."""
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": RAG_MODEL,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": max_tokens,
                }
            },
            timeout=RAG_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except requests.exceptions.Timeout:
        logger.error(f"Ollama timeout after {RAG_TIMEOUT}s")
        raise Exception("AI service timeout")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama request failed: {e}")
        raise Exception("AI service unavailable")


# ============================================
# Improve Title
# ============================================

IMPROVE_TITLE_SYSTEM = """You are a note title generator. Given note content, generate a clear, concise, descriptive title.

Rules:
- Title should be 3-8 words
- Capture the main topic or theme
- Use title case
- No quotes, punctuation at end, or special characters
- Be specific, not generic

Respond with ONLY the title, nothing else."""

def improve_title(content: str, current_title: str) -> str:
    """Generate an improved title for a note."""
    # Truncate content for prompt
    content_preview = content[:2000] if len(content) > 2000 else content

    prompt = f"""Current title: {current_title}

Note content:
{content_preview}

Generate a better, more descriptive title:"""

    result = call_ollama(prompt, IMPROVE_TITLE_SYSTEM, max_tokens=50)

    # Clean up the result
    result = result.strip('"\'').strip()
    if result.endswith('.'):
        result = result[:-1]

    return result or current_title


# ============================================
# Summarize
# ============================================

SUMMARIZE_SYSTEM = """You are a note summarizer. Create a concise summary of the note content.

Rules:
- Summary should be 2-4 sentences
- Capture key points and main ideas
- Use clear, simple language
- Be informative but brief

Respond with ONLY the summary, nothing else."""

def summarize_note(content: str, title: str) -> str:
    """Generate a summary of a note."""
    # Truncate content for prompt
    content_preview = content[:3000] if len(content) > 3000 else content

    prompt = f"""Title: {title}

Content:
{content_preview}

Provide a concise summary:"""

    return call_ollama(prompt, SUMMARIZE_SYSTEM, max_tokens=200)


# ============================================
# Suggest Wikilinks
# ============================================

SUGGEST_WIKILINKS_SYSTEM = """You are a knowledge connection assistant. Given a note and a list of other note titles, suggest which existing notes could be linked using [[wikilinks]].

Rules:
- Only suggest links to notes from the provided list
- Explain briefly why each connection makes sense
- Maximum 5 suggestions
- Focus on meaningful semantic connections

Respond in this format:
1. [[Note Title]] - reason for connection
2. [[Another Title]] - reason for connection"""

def suggest_wikilinks(
    db: Session,
    note_id: int,
    content: str,
    title: str,
    owner_id: int
) -> List[Dict]:
    """Suggest potential wikilink connections for a note."""
    from features.notes.models import Note

    # Get other notes by the user (excluding current note)
    other_notes = db.query(Note).filter(
        Note.owner_id == owner_id,
        Note.id != note_id
    ).limit(100).all()

    if not other_notes:
        return []

    # Build list of available titles
    available_titles = [n.title for n in other_notes]
    titles_list = "\n".join(f"- {t}" for t in available_titles[:50])

    # Truncate content
    content_preview = content[:2000] if len(content) > 2000 else content

    prompt = f"""Current note title: {title}

Current note content:
{content_preview}

Available notes to link to:
{titles_list}

Suggest connections:"""

    result = call_ollama(prompt, SUGGEST_WIKILINKS_SYSTEM, max_tokens=400)

    # Parse suggestions
    suggestions = []
    for line in result.split('\n'):
        line = line.strip()
        if '[[' in line and ']]' in line:
            # Extract title from [[Title]]
            start = line.find('[[') + 2
            end = line.find(']]')
            if start > 1 and end > start:
                suggested_title = line[start:end]
                # Find the note
                for note in other_notes:
                    if note.title.lower() == suggested_title.lower():
                        reason = ""
                        if ' - ' in line:
                            reason = line.split(' - ', 1)[1]
                        suggestions.append({
                            "note_id": note.id,
                            "title": note.title,
                            "reason": reason
                        })
                        break

    return suggestions[:5]


# ============================================
# Regenerate from Source Image
# ============================================

def regenerate_from_source(db: Session, note_id: int, owner_id: int) -> Dict:
    """
    Re-analyze the linked image and regenerate note content.

    Args:
        db: Database session
        note_id: ID of the note to regenerate
        owner_id: Owner ID for authorization

    Returns:
        Dict with new_content and new_title
    """
    from features.notes.models import Note
    from model_router import ModelRouter
    from sqlalchemy.orm import joinedload

    # Get the note with its linked images (eager load the images relationship)
    note = db.query(Note).options(
        joinedload(Note.images)
    ).filter(
        Note.id == note_id,
        Note.owner_id == owner_id
    ).first()

    if not note:
        raise ValueError("Note not found")

    # Use the images relationship directly
    linked_images = note.images

    if not linked_images:
        raise ValueError("No linked images found for this note. The note must be linked to at least one image.")

    # Use the first linked image
    image = linked_images[0]

    if not image.filepath:
        raise ValueError(f"Image file path not found for image ID {image.id}")

    # Check if file exists - handle both absolute and relative paths
    from pathlib import Path
    import os
    from core import config

    image_path = Path(image.filepath)

    # If path doesn't exist as-is, try with upload dir prefix
    if not image_path.exists():
        # Try as relative to upload dir
        alt_path = Path(config.UPLOAD_DIR) / image.filepath
        if alt_path.exists():
            image_path = alt_path
        else:
            # Try extracting just the filename and looking in upload dir
            filename_only = Path(image.filepath).name
            alt_path = Path(config.UPLOAD_DIR) / filename_only
            if alt_path.exists():
                image_path = alt_path
            else:
                raise ValueError(f"Image file no longer exists at path: {image.filepath}")

    # Use ModelRouter to re-analyze the image
    router = ModelRouter(ollama_host=OLLAMA_HOST)

    resolved_path = str(image_path)
    logger.info(f"Regenerating analysis for note {note_id} from image {image.id} at {resolved_path}")

    result = router.analyze_image(
        image_path=resolved_path,
        timeout=120  # Slightly longer timeout for regeneration
    )

    if result.get("status") != "success":
        error_msg = result.get("error", "Unknown error from model router")
        raise Exception(f"AI analysis failed: {error_msg}")

    new_content = result.get("response", "")

    # Extract a new title from the content
    from features.images.tasks import generate_note_title, extract_image_metadata
    metadata = extract_image_metadata(resolved_path)
    new_title = generate_note_title(new_content, image.filename, metadata)

    logger.info(f"Regenerated content for note {note_id}: {len(new_content)} chars")

    return {
        "new_content": new_content,
        "new_title": new_title,
        "image_id": image.id
    }


# ============================================
# Enhance All (Combined)
# ============================================

def enhance_note(
    db: Session,
    note_id: int,
    content: str,
    title: str,
    owner_id: int
) -> Dict:
    """Run all AI enhancements and return results."""
    results = {
        "improved_title": None,
        "summary": None,
        "suggested_wikilinks": []
    }

    try:
        results["improved_title"] = improve_title(content, title)
    except Exception as e:
        logger.error(f"Error improving title: {e}")

    try:
        results["summary"] = summarize_note(content, title)
    except Exception as e:
        logger.error(f"Error summarizing: {e}")

    try:
        results["suggested_wikilinks"] = suggest_wikilinks(
            db, note_id, content, title, owner_id
        )
    except Exception as e:
        logger.error(f"Error suggesting wikilinks: {e}")

    return results
