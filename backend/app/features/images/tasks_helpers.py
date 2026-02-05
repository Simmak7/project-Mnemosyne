"""
Image Tasks - Helper Functions.

Utilities for EXIF metadata extraction, note title generation,
content formatting, and tag extraction from AI responses.
"""

import re
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from PIL import Image as PILImage
from PIL.ExifTags import TAGS

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
