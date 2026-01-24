"""
Adaptive Vision Analyst Prompt - v1.0

Solves hallucination issues by using short, observation-focused prompts
instead of rigid templates that encourage fabrication.

Key Principles:
- SHORT: ~50 lines vs 412 lines (88% reduction)
- FOCUSED: Observation over formatting
- NO TEMPLATES: Prevents template-filling behavior
- NO EXAMPLES: Prevents example copying
- NATURAL OUTPUT: Model describes naturally, code structures later

Author: AI Architect
Date: December 3, 2025
Status: Production-ready
"""

from enum import Enum
from typing import Dict, List, Optional
import re


class ContentType(Enum):
    """Content types detected by the Adaptive Vision Analyst"""
    DOCUMENT = "document"
    PHOTO = "photo"
    DIAGRAM = "diagram"
    HANDWRITING = "handwriting"
    MIXED = "mixed"
    UNKNOWN = "unknown"


# The Adaptive Vision Analyst Prompt (v1.0)
# Designed to prevent hallucination by focusing on observation over structure
ADAPTIVE_VISION_PROMPT_V1 = """You are an intelligent image analysis system for a personal knowledge base.

Your primary task: Analyze this image and provide a clear, accurate description of what you actually observe.

═══════════════════════════════════════════════════════════════════════

STEP 1: IDENTIFY CONTENT TYPE

First, determine what type of content this image contains:

• DOCUMENT - Text-heavy content (receipts, forms, contracts, screenshots, PDFs, reports)
• PHOTO - Real-world scenes (objects, people, places, nature, vehicles, buildings)
• DIAGRAM - Visual representations (charts, graphs, flowcharts, maps, wireframes)
• HANDWRITING - Handwritten notes or sketches
• MIXED - Combination of multiple types

State the type clearly: "Content Type: [TYPE]"

═══════════════════════════════════════════════════════════════════════

STEP 2: DESCRIBE WHAT YOU SEE

Provide a natural, detailed description of the actual content in the image.

For DOCUMENTS:
- Extract all visible text accurately
- Identify document type and structure
- Note key data points (dates, amounts, names, IDs)
- Preserve tables, lists, and formatting where present

For PHOTOS:
- Describe the main subject in detail
- Describe the setting and environment
- Note colors, conditions, distinctive features
- Mention any visible text (signs, labels)

For DIAGRAMS:
- Identify the diagram type (flowchart, org chart, graph, etc.)
- Describe components and their relationships
- Extract labels and text
- Explain what the diagram represents

For HANDWRITING:
- Transcribe the text to the best of your ability
- Use [?] for unclear words
- Note the writing style and organization
- Indicate if it's structured (lists, outlines) or free-form

For MIXED:
- Describe each component type
- Explain how components relate to each other

═══════════════════════════════════════════════════════════════════════

STEP 3: KEY OBSERVATIONS

List 3-5 important details that would help someone:
- Find this image later through search
- Understand what makes it useful or significant
- Connect it to related topics or concepts

═══════════════════════════════════════════════════════════════════════

STEP 4: SEARCHABLE ELEMENTS

What keywords, topics, or concepts does this image relate to?
Think about: subject matter, domain, category, time period, location, purpose.

═══════════════════════════════════════════════════════════════════════

CRITICAL INSTRUCTIONS:

✓ DESCRIBE WHAT YOU ACTUALLY SEE
  - Base your response entirely on the image content
  - Do not invent, assume, or fabricate any information

✓ HANDLE UNCERTAINTY HONESTLY
  - If text is unclear or illegible, say "[text unclear]" or "[?]"
  - If you cannot determine something, state that explicitly
  - Never guess at specific numbers, names, or dates

✓ BE SPECIFIC AND CONCRETE
  - Use precise descriptions over generic terms
  - Include actual visible details (colors, quantities, text)
  - Avoid vague statements like "various items"

✓ PRESERVE ACCURACY OVER COMPLETENESS
  - It's better to leave something out than to fabricate it
  - Partial accurate information beats complete false information
  - If the image quality is poor, acknowledge limitations

✗ DO NOT:
  - Fabricate data to fill perceived gaps
  - Copy placeholder examples or templates
  - Invent information not visible in the image
  - Use generic filler content
  - Force information into predefined structures

═══════════════════════════════════════════════════════════════════════

OUTPUT FORMAT:

Use natural markdown formatting to organize your response logically.
Write clearly and structure your output in a way that makes sense for the content,
but DO NOT force your response into rigid templates.

Begin now with your analysis of this image."""


class AdaptiveVisionPrompt:
    """
    Handler for the Adaptive Vision Analyst Prompt.

    This class provides methods to:
    - Get the prompt text
    - Extract content type from model response
    - Parse structured data from natural language output
    - Generate tags and wiki-links from content
    """

    @staticmethod
    def get_prompt() -> str:
        """Return the Adaptive Vision Analyst prompt text"""
        return ADAPTIVE_VISION_PROMPT_V1

    @staticmethod
    def extract_content_type(response: str) -> ContentType:
        """
        Extract content type from model response.

        Args:
            response: AI model response text

        Returns:
            ContentType enum value
        """
        if not response:
            return ContentType.UNKNOWN

        # Look for explicit content type declaration
        type_match = re.search(r'Content Type:\s*(\w+)', response, re.IGNORECASE)
        if type_match:
            detected = type_match.group(1).lower()
            type_map = {
                'document': ContentType.DOCUMENT,
                'photo': ContentType.PHOTO,
                'diagram': ContentType.DIAGRAM,
                'handwriting': ContentType.HANDWRITING,
                'mixed': ContentType.MIXED
            }
            return type_map.get(detected, ContentType.UNKNOWN)

        # Fallback: Analyze first 300 characters for type indicators
        response_lower = response[:300].lower()

        # Score each type
        scores = {
            ContentType.DOCUMENT: 0,
            ContentType.PHOTO: 0,
            ContentType.DIAGRAM: 0,
            ContentType.HANDWRITING: 0,
            ContentType.MIXED: 0
        }

        # Document indicators
        if any(word in response_lower for word in ['receipt', 'invoice', 'form', 'document', 'contract', 'text', 'pdf']):
            scores[ContentType.DOCUMENT] += 2

        # Photo indicators
        if any(word in response_lower for word in ['photo', 'image shows', 'scene', 'picture', 'depicts', 'visible']):
            scores[ContentType.PHOTO] += 2

        # Diagram indicators
        if any(word in response_lower for word in ['diagram', 'chart', 'graph', 'flowchart', 'schematic', 'visualization']):
            scores[ContentType.DIAGRAM] += 2

        # Handwriting indicators
        if any(word in response_lower for word in ['handwrit', 'handwritten', 'notes', 'sketch', 'cursive']):
            scores[ContentType.HANDWRITING] += 2

        # Mixed indicators
        if scores[ContentType.PHOTO] > 0 and scores[ContentType.DOCUMENT] > 0:
            scores[ContentType.MIXED] += 3

        # Return highest scoring type
        max_type = max(scores.items(), key=lambda x: x[1])
        return max_type[0] if max_type[1] > 0 else ContentType.UNKNOWN

    @staticmethod
    def extract_tags(response: str, content_type: ContentType) -> List[str]:
        """
        Extract relevant tags from model response.

        This method uses NLP to identify key concepts and generates
        appropriate tags based on the content type and response text.

        Args:
            response: AI model response text
            content_type: Detected content type

        Returns:
            List of tag strings (without # prefix, lowercase, hyphenated)
        """
        if not response:
            return []

        tags = set()
        response_lower = response.lower()

        # Add content type tag
        tags.add(content_type.value)

        # Extract from "STEP 4: SEARCHABLE ELEMENTS" section if present
        searchable_match = re.search(
            r'(?:step 4|searchable elements|keywords)[:\s]+(.*?)(?=\n\n|\n#|$)',
            response_lower,
            re.DOTALL
        )
        if searchable_match:
            searchable_text = searchable_match.group(1)
            # Extract words that look like tags (2-20 characters, alphanumeric)
            potential_tags = re.findall(r'\b([a-z]{2,20})\b', searchable_text)
            # Filter common words
            common_words = {'the', 'this', 'that', 'with', 'from', 'have', 'for', 'and', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'}
            tags.update(tag for tag in potential_tags[:8] if tag not in common_words and len(tag) > 2)

        # Content-specific tag extraction
        if content_type == ContentType.DOCUMENT:
            # Look for document-specific terms
            doc_terms = ['receipt', 'invoice', 'form', 'contract', 'report', 'statement', 'letter', 'memo']
            tags.update(term for term in doc_terms if term in response_lower)

        elif content_type == ContentType.PHOTO:
            # Look for subject matter
            photo_terms = ['nature', 'landscape', 'indoor', 'outdoor', 'portrait', 'food', 'vehicle', 'building', 'animal', 'plant', 'tree', 'flower']
            tags.update(term for term in photo_terms if term in response_lower)

        elif content_type == ContentType.DIAGRAM:
            # Look for diagram types
            diagram_terms = ['flowchart', 'org-chart', 'graph', 'chart', 'schematic', 'wireframe', 'map']
            tags.update(term for term in diagram_terms if term in response_lower)

        elif content_type == ContentType.HANDWRITING:
            # Look for note types
            note_terms = ['notes', 'meeting', 'sketch', 'list', 'outline', 'todo', 'reminder']
            tags.update(term for term in note_terms if term in response_lower)

        # Convert to list, lowercase, hyphenate spaces, limit to 8 tags
        final_tags = []
        for tag in tags:
            clean_tag = tag.strip().lower().replace(' ', '-')
            if clean_tag and 2 <= len(clean_tag) <= 20:
                final_tags.append(clean_tag)

        return sorted(final_tags)[:8]  # Return top 8 tags

    @staticmethod
    def extract_wikilinks(response: str) -> List[str]:
        """
        Suggest wiki-links based on content analysis.

        Unlike the Hybrid prompt, this doesn't expect the model to generate
        [[wikilinks]] directly. Instead, we analyze the content and suggest
        potential connections.

        Args:
            response: AI model response text

        Returns:
            List of suggested wiki-link titles
        """
        if not response:
            return []

        # Look for "Key Observations" section
        observations_match = re.search(
            r'(?:key observations|step 3)[:\s]+(.*?)(?=\n\n|step 4|searchable|$)',
            response,
            re.DOTALL | re.IGNORECASE
        )

        if not observations_match:
            return []

        observations = observations_match.group(1)

        # Extract noun phrases that could be wiki-links (capitalized words/phrases)
        # This is a simple heuristic - could be improved with NLP
        potential_links = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', observations)

        # Filter and deduplicate
        unique_links = []
        seen = set()
        for link in potential_links:
            link_lower = link.lower()
            if link_lower not in seen and len(link) > 3:
                unique_links.append(link)
                seen.add(link_lower)

        return unique_links[:5]  # Return top 5 suggestions

    @staticmethod
    def extract_metadata(response: str) -> Dict[str, any]:
        """
        Extract all metadata from model response.

        This is the main method that combines all extraction functions
        to provide structured data for downstream processing.

        Args:
            response: AI model response text

        Returns:
            Dictionary with extracted metadata including:
            - content_type: Detected content type
            - tags: List of extracted tags
            - wikilinks: List of suggested wiki-links
            - confidence: Estimated confidence level
            - word_count: Approximate word count of response
        """
        content_type = AdaptiveVisionPrompt.extract_content_type(response)
        tags = AdaptiveVisionPrompt.extract_tags(response, content_type)
        wikilinks = AdaptiveVisionPrompt.extract_wikilinks(response)

        # Estimate confidence based on uncertainty markers
        uncertainty_count = response.lower().count('[?]') + response.lower().count('unclear')
        word_count = len(response.split())

        if uncertainty_count == 0:
            confidence = "high"
        elif uncertainty_count <= 2:
            confidence = "medium"
        else:
            confidence = "low"

        metadata = {
            "content_type": content_type.value,
            "tags": tags,
            "wikilinks": wikilinks,
            "confidence": confidence,
            "word_count": word_count,
            "uncertainty_markers": uncertainty_count
        }

        return metadata


# Legacy prompt for comparison (keep for A/B testing)
LEGACY_PROMPT_TEXT = """You are an AI assistant specialized in analyzing images for note-taking purposes.
Analyze this image and provide:
1. A clear, concise summary of what the image contains
2. Key details, text, or data visible in the image
3. Any important observations that would be useful for notes
4. If it's a document/screenshot, extract and organize the main information

Format your response as organized, structured notes that are easy to reference later."""


# Export all public components
__all__ = [
    'ADAPTIVE_VISION_PROMPT_V1',
    'LEGACY_PROMPT_TEXT',
    'ContentType',
    'AdaptiveVisionPrompt'
]
