"""
Celery tasks for image processing and AI analysis.

Tasks:
- analyze_image_task: Analyze image with Ollama AI (30-60s async)

Workflow:
1. Image uploaded via API (instant response with task_id)
2. Celery worker picks up task from Redis queue
3. AI model analyzes image (llama3.2-vision or qwen2.5vl)
4. Note created from AI analysis with extracted tags/wikilinks
5. Image linked to note via image_note_relations table
6. User polls task status until completion

AI Models (via ModelRouter):
- llama3.2-vision:11b (stable, 4.7GB)
- qwen2.5vl:7b-q4_K_M (experimental, quantized)
"""

from celery import Task
from core.celery_app import celery_app
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from PIL import Image as PILImage
from PIL.ExifTags import TAGS

from core import database, config
import crud
from model_router import ModelRouter
from features.albums.service import AlbumService

logger = logging.getLogger(__name__)


def extract_image_metadata(image_path: str) -> Dict[str, Optional[str]]:
    """
    Extract EXIF metadata from an image file.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary with 'date' and 'location' keys (None if not found)
    """
    metadata = {"date": None, "location": None}

    try:
        with PILImage.open(image_path) as img:
            exif_data = img._getexif()

            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)

                    # Extract date/time
                    if tag_name in ("DateTime", "DateTimeOriginal", "DateTimeDigitized"):
                        try:
                            # EXIF date format: "YYYY:MM:DD HH:MM:SS"
                            date_obj = datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
                            metadata["date"] = date_obj.strftime("%B %d, %Y")
                        except (ValueError, TypeError):
                            pass

                    # Extract GPS location (if present)
                    elif tag_name == "GPSInfo" and isinstance(value, dict):
                        # Basic GPS extraction - could be enhanced
                        metadata["location"] = "Geotagged"

    except Exception as e:
        logger.debug(f"Could not extract EXIF metadata from {image_path}: {str(e)}")

    return metadata


def generate_note_title(ai_analysis: str, image_filename: str, metadata: Dict[str, Optional[str]]) -> str:
    """
    Generate a short, meaningful title for a note based on AI analysis and metadata.

    Strategy priority:
    1. Extract subject from descriptive patterns ("shows a X", "depicts X")
    2. Extract noun phrase from first sentence
    3. Look for "shows", "contains" patterns
    4. Use EXIF metadata (date, location)
    5. Clean up filename as fallback

    Args:
        ai_analysis: AI-generated analysis text
        image_filename: Original image filename
        metadata: Dictionary with 'date' and 'location' from EXIF

    Returns:
        Generated title (preferably 15-30 characters, max 60)
    """
    # Strategy 1: Extract subject from descriptive patterns
    subject_patterns = [
        r'(?:shows?|depicts?|features?|contains?|presents?)\s+(?:an?\s+)?([^,.]+?)(?:\s+(?:in|on|at|with|and|parked|standing|sitting|located))',
        r'(?:image|photo|picture)\s+(?:shows?|of)\s+(?:an?\s+)?([^,.]+?)(?:\s+(?:in|on|at|with|and))',
        r'This\s+is\s+(?:an?\s+)?([^,.]+?)(?:\s+(?:in|on|at|with|and|that))',
        r'(?:an?\s+)?([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){0,3})(?:\s+(?:in|on|at|with|and|parked))',
    ]

    for pattern in subject_patterns:
        match = re.search(pattern, ai_analysis, re.IGNORECASE)
        if match:
            subject = match.group(1).strip()
            # Clean up common leading words
            subject = re.sub(r'^(?:the|an?|this|that|these|those)\s+', '', subject, flags=re.IGNORECASE)
            subject = subject.strip()
            if 3 < len(subject) <= 50:
                return ' '.join(word.capitalize() for word in subject.split())

    # Strategy 2: Extract noun phrase from first sentence
    for line in ai_analysis.split('\n'):
        line = line.strip()
        if (line and
            not line.startswith('#') and
            not line.startswith('**') and
            not line.startswith('Content Type:') and
            len(line) > 20):

            noun_match = re.search(
                r'(?:image|photo|picture|this)\s+(?:shows?|depicts?|features?|contains?|is)\s+(?:an?\s+)?(.+?)(?:[,.]|$)',
                line,
                re.IGNORECASE
            )
            if noun_match:
                subject = noun_match.group(1).strip()
                words = subject.split()[:5]
                subject = ' '.join(words)
                if 3 < len(subject) <= 50:
                    return ' '.join(word.capitalize() for word in subject.split())
            break

    # Strategy 3: Look for "shows", "contains", "depicts" patterns
    patterns = [
        r'(?:shows?|contains?|depicts?|features?|presents?)\s+(.+?)(?:[.!?]|$)',
        r'(?:image|photo|picture)\s+(?:of|shows?)\s+(.+?)(?:[.!?]|$)',
        r'(?:is|are)\s+(?:a|an)\s+(.+?)(?:[.!?]|$)'
    ]

    for pattern in patterns:
        match = re.search(pattern, ai_analysis, re.IGNORECASE)
        if match:
            title_candidate = match.group(1).strip()
            title_candidate = title_candidate.replace('\n', ' ').strip()
            if title_candidate and len(title_candidate) <= 60:
                return title_candidate.capitalize()
            elif title_candidate:
                return title_candidate[:57].rsplit(' ', 1)[0].capitalize() + "..."

    # Strategy 4: Use metadata if available
    if metadata.get("date"):
        location_part = f" - {metadata['location']}" if metadata.get("location") else ""
        return f"Image from {metadata['date']}{location_part}"[:60]

    # Fallback: Use filename without UUID
    filename_stem = Path(image_filename).stem
    clean_name = re.sub(r'^[a-f0-9-]{36}_?', '', filename_stem, flags=re.IGNORECASE)
    if clean_name:
        clean_name = clean_name.replace('_', ' ').replace('-', ' ').title()
        if len(clean_name) <= 60:
            return clean_name
        return clean_name[:57].rsplit(' ', 1)[0] + "..."

    # Ultimate fallback
    if metadata.get("date"):
        return f"Image Analysis - {metadata['date']}"
    return "Image Analysis"


def extract_summary_from_analysis(ai_analysis: str) -> str:
    """
    Extract just the summary section from AI analysis.

    Args:
        ai_analysis: Full AI analysis text

    Returns:
        Cleaned summary text
    """
    return ai_analysis.strip()


def format_note_content(ai_analysis: str, tags: List[str], wikilinks: List[str] = None) -> str:
    """
    Format note content with summary, tags, and wikilinks.

    Args:
        ai_analysis: AI analysis result
        tags: List of extracted tags
        wikilinks: List of suggested wikilink topics (optional)

    Returns:
        Formatted note content with wikilinks and tags
    """
    summary = extract_summary_from_analysis(ai_analysis)

    # Add wikilinks section if available
    wikilink_section = ""
    if wikilinks and len(wikilinks) > 0:
        formatted_links = [f"[[{link}]]" for link in wikilinks]
        wikilink_section = "\n\n**Related Topics:** " + " • ".join(formatted_links)

    # Format tags as hashtags
    tag_line = ""
    if tags:
        tag_line = "\n\n**Tags:** " + " ".join(f"#{tag.replace(' ', '-')}" for tag in tags)

    return f"{summary}{wikilink_section}{tag_line}"


def extract_tags_from_ai_response(ai_text: str) -> List[str]:
    """
    Extract keywords/tags from AI analysis response.

    Uses pattern matching to identify common objects, subjects, and concepts.

    Args:
        ai_text: AI-generated analysis text

    Returns:
        List of extracted tags (lowercase, max 5)
    """
    if not ai_text:
        return []

    ai_text_lower = ai_text.lower()
    keywords = set()

    # Pattern 1: Look for "contains", "shows", "depicts", "features" patterns
    contains_patterns = [
        r'(?:contains?|shows?|depicts?|features?|includes?)\s+(?:a|an|the|some|several)?\s*([a-z]+(?:\s+[a-z]+)?)',
        r'(?:image|photo|picture)\s+of\s+(?:a|an|the)?\s*([a-z]+(?:\s+[a-z]+)?)',
        r'(?:is|are)\s+(?:a|an|the)?\s*([a-z]+(?:\s+[a-z]+)?)'
    ]

    for pattern in contains_patterns:
        matches = re.findall(pattern, ai_text_lower)
        for match in matches:
            tag = match.strip()
            if len(tag) > 2 and len(tag) < 20:
                keywords.add(tag)

    # Pattern 2: Common image content categories
    categories = {
        'document': ['document', 'text', 'writing', 'letter', 'form', 'paper'],
        'nature': ['tree', 'forest', 'mountain', 'landscape', 'sky', 'water', 'ocean', 'river', 'plant'],
        'people': ['person', 'people', 'man', 'woman', 'child', 'face', 'portrait'],
        'food': ['food', 'meal', 'dish', 'plate', 'restaurant', 'cooking'],
        'technology': ['computer', 'phone', 'screen', 'device', 'laptop', 'keyboard'],
        'architecture': ['building', 'house', 'architecture', 'structure', 'room', 'interior'],
        'vehicle': ['car', 'vehicle', 'bike', 'bicycle', 'truck', 'automobile'],
        'animal': ['animal', 'dog', 'cat', 'bird', 'pet'],
        'art': ['painting', 'art', 'drawing', 'artwork', 'illustration'],
        'diagram': ['diagram', 'chart', 'graph', 'flowchart', 'schematic'],
        'screenshot': ['screenshot', 'interface', 'ui', 'application'],
        'outdoor': ['outdoor', 'outside', 'park', 'street'],
        'indoor': ['indoor', 'inside', 'room']
    }

    for category, terms in categories.items():
        for term in terms:
            if term in ai_text_lower:
                keywords.add(category)
                break

    # Pattern 3: Extract nouns after common verbs
    action_patterns = [
        r'(?:see|sees|seeing|visible|looking at)\s+(?:a|an|the)?\s*([a-z]+)',
    ]

    for pattern in action_patterns:
        matches = re.findall(pattern, ai_text_lower)
        for match in matches:
            tag = match.strip()
            if len(tag) > 2 and len(tag) < 15:
                keywords.add(tag)

    # Limit to top 5 tags, prioritize shorter tags
    keywords_list = sorted(list(keywords), key=len)
    return keywords_list[:5]


class DatabaseTask(Task):
    """Base task that provides database session with proper lifecycle management."""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = database.SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Close database session after task completes."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(bind=True, base=DatabaseTask, name="features.images.tasks.analyze_image")
def analyze_image_task(self, image_id: int, image_path: str, prompt: str, album_id: int = None):
    """
    Celery task to analyze an image with Ollama AI in the background.

    Task flow:
    1. Update image status to 'processing'
    2. Call AI model via ModelRouter (handles model selection)
    3. Extract tags and wikilinks from AI response
    4. Create note with formatted content
    5. Link image to note
    6. Add tags to both image and note
    7. Add image to album (if album_id provided)

    Args:
        image_id: Database ID of the image
        image_path: File system path to the image
        prompt: Analysis prompt for the AI (optional, router selects if empty)
        album_id: Album ID to add image to after analysis (optional)

    Returns:
        dict: Task result with status and analysis text
    """
    logger.info(f"[Task {self.request.id}] Starting AI analysis for image {image_id}")

    try:
        # Update image status to processing
        crud.update_image_analysis_result(
            db=self.db,
            image_id=image_id,
            status="processing"
        )
        logger.debug(f"[Task {self.request.id}] Image {image_id} status updated to processing")

        # Initialize model router
        router = ModelRouter(ollama_host=config.OLLAMA_HOST)

        logger.debug(f"[Task {self.request.id}] Routing analysis request for image {image_id}")

        try:
            # Call model router (handles model selection, prompt selection, and API call)
            if prompt:
                result = router.analyze_image(
                    image_path=image_path,
                    custom_prompt=prompt,
                    timeout=300
                )
            else:
                # No custom prompt - let router select based on PROMPT_ROLLOUT_PERCENT
                result = router.analyze_image(
                    image_path=image_path,
                    timeout=300
                )

            # Check if analysis was successful
            if result.get("status") == "success":
                analysis_text = result.get("response", "No response from AI")
                logger.info(f"[Task {self.request.id}] AI analysis successful for image {image_id}")

                # Update image analysis result
                crud.update_image_analysis_result(
                    db=self.db,
                    image_id=image_id,
                    status="completed",
                    result=analysis_text
                )

                # Extract tags and wikilinks from AI response
                extracted_tags = []
                extracted_wikilinks = []

                try:
                    # Use adaptive prompt metadata if available
                    content_metadata = result.get("content_metadata", {})

                    if content_metadata and content_metadata.get("tags"):
                        extracted_tags = content_metadata["tags"]
                        logger.info(f"[Task {self.request.id}] Using adaptive prompt tags: {len(extracted_tags)} tags")
                    else:
                        extracted_tags = extract_tags_from_ai_response(analysis_text)
                        logger.info(f"[Task {self.request.id}] Using legacy tag extraction: {len(extracted_tags)} tags")

                    # Extract wikilinks from metadata
                    extracted_wikilinks = content_metadata.get("wikilinks", []) if content_metadata else []
                    if extracted_wikilinks:
                        logger.info(f"[Task {self.request.id}] Extracted {len(extracted_wikilinks)} wikilinks")

                    image = crud.get_image(self.db, image_id=image_id)

                    if image and extracted_tags:
                        logger.info(f"[Task {self.request.id}] Extracted {len(extracted_tags)} tags: {extracted_tags}")

                        for tag_name in extracted_tags:
                            try:
                                crud.add_tag_to_image(
                                    db=self.db,
                                    image_id=image_id,
                                    tag_name=tag_name,
                                    owner_id=image.owner_id
                                )
                            except Exception as tag_err:
                                logger.warning(f"[Task {self.request.id}] Failed to add tag '{tag_name}': {str(tag_err)}")
                                self.db.rollback()

                        logger.info(f"[Task {self.request.id}] Tags added to image {image_id}")
                except Exception as e:
                    logger.warning(f"[Task {self.request.id}] Failed to extract/add tags: {str(e)}")
                    self.db.rollback()

                # Create note with analysis
                try:
                    image = crud.get_image(self.db, image_id=image_id)

                    # Extract EXIF metadata for better title generation
                    metadata = extract_image_metadata(image_path)

                    # Generate meaningful title from AI analysis
                    note_title = generate_note_title(
                        ai_analysis=analysis_text,
                        image_filename=Path(image_path).name,
                        metadata=metadata
                    )

                    # Format note content with tags and wikilinks
                    note_content = format_note_content(
                        ai_analysis=analysis_text,
                        tags=extracted_tags,
                        wikilinks=extracted_wikilinks
                    )

                    note = crud.create_note(
                        db=self.db,
                        title=note_title,
                        content=note_content,
                        owner_id=image.owner_id if image else None
                    )
                    logger.info(f"[Task {self.request.id}] Note created: ID {note.id}, title '{note_title}'")

                    # Auto-set image display_name from note title
                    try:
                        crud.update_image_display_name(
                            db=self.db,
                            image_id=image_id,
                            display_name=note_title
                        )
                        logger.info(f"[Task {self.request.id}] Image display_name set to '{note_title}'")
                    except Exception as name_err:
                        logger.warning(f"[Task {self.request.id}] Failed to set display_name: {str(name_err)}")
                        self.db.rollback()

                    # Link the note to the image
                    try:
                        crud.add_image_to_note(db=self.db, image_id=image_id, note_id=note.id)
                        logger.info(f"[Task {self.request.id}] Linked note {note.id} to image {image_id}")
                    except Exception as link_err:
                        logger.warning(f"[Task {self.request.id}] Failed to link note to image: {str(link_err)}")
                        self.db.rollback()

                    # Add tags to the note
                    if extracted_tags:
                        for tag_name in extracted_tags:
                            try:
                                crud.add_tag_to_note(
                                    db=self.db,
                                    note_id=note.id,
                                    tag_name=tag_name,
                                    owner_id=image.owner_id
                                )
                            except Exception as tag_err:
                                logger.warning(f"[Task {self.request.id}] Failed to add tag '{tag_name}' to note: {str(tag_err)}")
                                self.db.rollback()
                except Exception as e:
                    logger.error(f"[Task {self.request.id}] Failed to create note: {str(e)}", exc_info=True)
                    self.db.rollback()

                # Add image to album if album_id was provided
                if album_id:
                    try:
                        image = crud.get_image(self.db, image_id=image_id)
                        if image:
                            added = AlbumService.add_images_to_album(
                                db=self.db,
                                album_id=album_id,
                                owner_id=image.owner_id,
                                image_ids=[image_id]
                            )
                            if added > 0:
                                logger.info(f"[Task {self.request.id}] Added image {image_id} to album {album_id}")
                            else:
                                logger.warning(f"[Task {self.request.id}] Image {image_id} already in album {album_id} or album not found")
                    except Exception as album_err:
                        logger.warning(f"[Task {self.request.id}] Failed to add image to album {album_id}: {str(album_err)}")
                        self.db.rollback()

                return {
                    "status": "completed",
                    "analysis": analysis_text,
                    "image_id": image_id
                }

            else:
                # Handle router error response
                error_msg = result.get("error", "Unknown error from model router")
                model_used = result.get("model", "unknown")
                logger.error(f"[Task {self.request.id}] Model router error ({model_used}): {error_msg}")

                crud.update_image_analysis_result(
                    db=self.db,
                    image_id=image_id,
                    status="failed",
                    result=f"Model: {model_used} - {error_msg}"
                )

                # Retry if connection error detected
                if "connect" in error_msg.lower() or "connection" in error_msg.lower():
                    logger.info(f"[Task {self.request.id}] Connection error detected, retrying in 60s")
                    raise self.retry(exc=Exception(error_msg), countdown=60, max_retries=3)

                return {"status": "failed", "error": error_msg}

        except FileNotFoundError as e:
            error_msg = f"Image file not found: {str(e)}"
            logger.error(f"[Task {self.request.id}] {error_msg}")
            crud.update_image_analysis_result(
                db=self.db,
                image_id=image_id,
                status="failed",
                result=error_msg
            )
            return {"status": "failed", "error": error_msg}

        except Exception as e:
            error_msg = f"Unexpected error during analysis: {str(e)}"
            logger.error(f"[Task {self.request.id}] {error_msg}", exc_info=True)
            crud.update_image_analysis_result(
                db=self.db,
                image_id=image_id,
                status="failed",
                result=error_msg
            )
            return {"status": "failed", "error": error_msg}

    except Exception as e:
        error_msg = f"Unexpected error during AI analysis: {str(e)}"
        logger.error(f"[Task {self.request.id}] {error_msg}", exc_info=True)
        crud.update_image_analysis_result(
            db=self.db,
            image_id=image_id,
            status="failed",
            result=error_msg
        )
        return {"status": "failed", "error": error_msg}
