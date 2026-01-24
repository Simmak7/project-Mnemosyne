"""
Chunking service for RAG retrieval.

Provides paragraph-based chunking for notes and images with:
- Intelligent paragraph detection
- Sentence-level splitting for long paragraphs (>500 chars)
- Chunk type detection (paragraph, heading, list, code)
- Position tracking for precise citations
"""

import re
from dataclasses import dataclass
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Configuration
MAX_CHUNK_SIZE = 500  # Characters before splitting into sentences
MIN_CHUNK_SIZE = 50   # Minimum chunk size to keep


@dataclass
class ChunkResult:
    """Result of chunking a piece of content."""
    content: str
    chunk_index: int
    chunk_type: str  # 'paragraph', 'heading', 'list', 'code'
    char_start: int
    char_end: int


def detect_chunk_type(text: str) -> str:
    """
    Detect the type of content chunk.

    Args:
        text: The chunk text to analyze

    Returns:
        One of: 'heading', 'list', 'code', 'paragraph'
    """
    text = text.strip()

    # Check for markdown headings
    if text.startswith('#'):
        return 'heading'

    # Check for code blocks
    if text.startswith('```') or text.startswith('    ') or '\t' in text[:4]:
        return 'code'

    # Check for list items (bullet or numbered)
    if re.match(r'^[-*+]\s', text) or re.match(r'^\d+\.\s', text):
        return 'list'

    return 'paragraph'


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.

    Handles common abbreviations and edge cases.

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    # Simple sentence splitter - split on sentence-ending punctuation
    # followed by whitespace and capital letter or end of string
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z]|$)', text)
    return [s.strip() for s in sentences if s.strip()]


def merge_short_sentences(sentences: List[str], target_size: int = 200) -> List[str]:
    """
    Merge very short sentences together to reach target size.

    Args:
        sentences: List of sentences
        target_size: Target character count per merged chunk

    Returns:
        List of merged sentences
    """
    if not sentences:
        return []

    merged = []
    current = ""

    for sentence in sentences:
        if not current:
            current = sentence
        elif len(current) + len(sentence) + 1 <= target_size:
            current += " " + sentence
        else:
            if current:
                merged.append(current)
            current = sentence

    if current:
        merged.append(current)

    return merged


def chunk_note_content(content: str, note_id: Optional[int] = None) -> List[ChunkResult]:
    """
    Chunk note content into meaningful segments for RAG retrieval.

    Strategy:
    1. Split by double newlines (paragraphs)
    2. Detect chunk type (heading, list, code, paragraph)
    3. Split long paragraphs (>500 chars) by sentences
    4. Track character positions for precise citations

    Args:
        content: The note content to chunk
        note_id: Optional note ID for logging

    Returns:
        List of ChunkResult objects
    """
    if not content or not content.strip():
        logger.debug(f"Empty content for note {note_id}, returning empty chunks")
        return []

    chunks: List[ChunkResult] = []

    # Split by double newlines (paragraphs) or single newline followed by special chars
    # This handles markdown structure better
    paragraphs = re.split(r'\n\n+|\n(?=[#\-*\d])', content)

    char_pos = 0
    chunk_index = 0

    for para in paragraphs:
        para_stripped = para.strip()

        if not para_stripped or len(para_stripped) < MIN_CHUNK_SIZE:
            # Skip very short chunks but track position
            if para in content[char_pos:]:
                char_pos = content.find(para, char_pos) + len(para)
            continue

        # Find actual position in original content
        para_start = content.find(para_stripped, char_pos)
        if para_start == -1:
            para_start = char_pos

        chunk_type = detect_chunk_type(para_stripped)

        # Handle long paragraphs by splitting into sentences
        if len(para_stripped) > MAX_CHUNK_SIZE and chunk_type == 'paragraph':
            sentences = split_into_sentences(para_stripped)
            merged_sentences = merge_short_sentences(sentences, target_size=400)

            sentence_pos = para_start
            for sentence in merged_sentences:
                sentence_start = content.find(sentence, sentence_pos)
                if sentence_start == -1:
                    sentence_start = sentence_pos

                chunks.append(ChunkResult(
                    content=sentence,
                    chunk_index=chunk_index,
                    chunk_type='paragraph',
                    char_start=sentence_start,
                    char_end=sentence_start + len(sentence)
                ))
                chunk_index += 1
                sentence_pos = sentence_start + len(sentence)
        else:
            # Keep as single chunk
            chunks.append(ChunkResult(
                content=para_stripped,
                chunk_index=chunk_index,
                chunk_type=chunk_type,
                char_start=para_start,
                char_end=para_start + len(para_stripped)
            ))
            chunk_index += 1

        # Update position tracker
        char_pos = para_start + len(para_stripped)

    logger.debug(f"Chunked note {note_id}: {len(chunks)} chunks from {len(content)} chars")
    return chunks


def chunk_image_analysis(
    analysis_result: str,
    image_id: Optional[int] = None
) -> List[ChunkResult]:
    """
    Chunk AI analysis result from an image for RAG retrieval.

    Image analysis typically has structured sections:
    - Content Type
    - Key Observations
    - Searchable Elements

    Strategy:
    1. Split by section markers (**, ##, etc.)
    2. Keep logical sections together
    3. Split very long sections by sentences

    Args:
        analysis_result: The AI analysis text to chunk
        image_id: Optional image ID for logging

    Returns:
        List of ChunkResult objects
    """
    if not analysis_result or not analysis_result.strip():
        logger.debug(f"Empty analysis for image {image_id}, returning empty chunks")
        return []

    chunks: List[ChunkResult] = []

    # Split by markdown sections (## or **Section:**)
    # Keep section headers with their content
    sections = re.split(r'\n(?=##|\*\*[A-Z])', analysis_result)

    char_pos = 0
    chunk_index = 0

    for section in sections:
        section_stripped = section.strip()

        if not section_stripped or len(section_stripped) < MIN_CHUNK_SIZE:
            if section in analysis_result[char_pos:]:
                char_pos = analysis_result.find(section, char_pos) + len(section)
            continue

        # Find position in original
        section_start = analysis_result.find(section_stripped, char_pos)
        if section_start == -1:
            section_start = char_pos

        # Determine chunk type based on content
        chunk_type = 'paragraph'
        if section_stripped.startswith('##') or section_stripped.startswith('**'):
            chunk_type = 'heading'
        elif re.match(r'^[-*]\s', section_stripped):
            chunk_type = 'list'

        # Split very long sections
        if len(section_stripped) > MAX_CHUNK_SIZE:
            # Split by bullet points or sentences
            if '\n-' in section_stripped or '\n*' in section_stripped:
                # Split by list items, keeping header with first item
                lines = section_stripped.split('\n')
                header = ""
                items = []

                for line in lines:
                    if line.strip().startswith('-') or line.strip().startswith('*'):
                        items.append(line.strip())
                    else:
                        if not items:
                            header = line.strip()
                        else:
                            items[-1] += " " + line.strip()

                # Create chunk for header + first few items
                current_chunk = header
                item_pos = section_start

                for item in items:
                    if len(current_chunk) + len(item) + 1 <= MAX_CHUNK_SIZE:
                        current_chunk += "\n" + item
                    else:
                        if current_chunk:
                            chunks.append(ChunkResult(
                                content=current_chunk,
                                chunk_index=chunk_index,
                                chunk_type='list' if items else chunk_type,
                                char_start=item_pos,
                                char_end=item_pos + len(current_chunk)
                            ))
                            chunk_index += 1
                            item_pos += len(current_chunk)
                        current_chunk = item

                if current_chunk:
                    chunks.append(ChunkResult(
                        content=current_chunk,
                        chunk_index=chunk_index,
                        chunk_type='list',
                        char_start=item_pos,
                        char_end=item_pos + len(current_chunk)
                    ))
                    chunk_index += 1
            else:
                # Split by sentences
                sentences = split_into_sentences(section_stripped)
                merged = merge_short_sentences(sentences, target_size=400)

                sent_pos = section_start
                for sent in merged:
                    sent_start = analysis_result.find(sent, sent_pos)
                    if sent_start == -1:
                        sent_start = sent_pos

                    chunks.append(ChunkResult(
                        content=sent,
                        chunk_index=chunk_index,
                        chunk_type='paragraph',
                        char_start=sent_start,
                        char_end=sent_start + len(sent)
                    ))
                    chunk_index += 1
                    sent_pos = sent_start + len(sent)
        else:
            # Keep as single chunk
            chunks.append(ChunkResult(
                content=section_stripped,
                chunk_index=chunk_index,
                chunk_type=chunk_type,
                char_start=section_start,
                char_end=section_start + len(section_stripped)
            ))
            chunk_index += 1

        char_pos = section_start + len(section_stripped)

    logger.debug(f"Chunked image {image_id} analysis: {len(chunks)} chunks")
    return chunks


def get_chunk_preview(chunk: ChunkResult, max_length: int = 100) -> str:
    """
    Get a preview of a chunk for display.

    Args:
        chunk: The chunk to preview
        max_length: Maximum preview length

    Returns:
        Truncated content with ellipsis if needed
    """
    content = chunk.content.strip()
    if len(content) <= max_length:
        return content
    return content[:max_length - 3] + "..."
