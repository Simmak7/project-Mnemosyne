"""
Document Chunking Service

Splits extracted document text into smaller chunks for RAG retrieval.
Each chunk includes page number and character offset metadata.

Chunking strategy:
- Split on paragraph boundaries (double newlines)
- Merge small paragraphs up to chunk_size
- Split large paragraphs at sentence boundaries
- Track char_start/char_end for each chunk
"""

import re
import logging
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from models import DocumentChunk

logger = logging.getLogger(__name__)

# Sentence boundary pattern
SENTENCE_RE = re.compile(r'(?<=[.!?])\s+')

# Page marker pattern (from pdfplumber output)
PAGE_MARKER_RE = re.compile(r'\n--- Page (\d+) ---\n')


def chunk_document(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[Dict]:
    """
    Split document text into chunks with metadata.

    Args:
        text: Full extracted text (may contain page markers)
        chunk_size: Target characters per chunk
        overlap: Character overlap between chunks

    Returns:
        List of dicts: {content, chunk_index, chunk_type, page_number,
                        char_start, char_end}
    """
    if not text or not text.strip():
        return []

    # Parse pages from text (page markers inserted by PDFExtractor)
    pages = _parse_pages(text)
    chunks = []
    chunk_index = 0
    global_offset = 0

    for page_num, page_text in pages:
        paragraphs = _split_paragraphs(page_text)

        buffer = ""
        buffer_start = global_offset

        for para in paragraphs:
            para_len = len(para)

            # If adding paragraph stays under limit, accumulate
            if len(buffer) + para_len + 1 <= chunk_size:
                if buffer:
                    buffer += "\n\n"
                buffer += para
            else:
                # Flush buffer if non-empty
                if buffer.strip():
                    chunks.append(_make_chunk(
                        buffer.strip(), chunk_index, page_num,
                        buffer_start, buffer_start + len(buffer)
                    ))
                    chunk_index += 1

                # Handle oversized paragraphs
                if para_len > chunk_size:
                    for sub in _split_sentences(para, chunk_size, overlap):
                        chunks.append(_make_chunk(
                            sub.strip(), chunk_index, page_num,
                            global_offset, global_offset + len(sub)
                        ))
                        chunk_index += 1
                    buffer = ""
                    buffer_start = global_offset + para_len
                else:
                    buffer = para
                    buffer_start = global_offset

            global_offset += para_len + 2  # +2 for \n\n separator

        # Flush remaining buffer for this page
        if buffer.strip():
            chunks.append(_make_chunk(
                buffer.strip(), chunk_index, page_num,
                buffer_start, buffer_start + len(buffer)
            ))
            chunk_index += 1

    logger.info(f"Chunked document into {len(chunks)} chunks")
    return chunks


def save_chunks(
    db: Session,
    document_id: int,
    chunks: List[Dict],
) -> int:
    """
    Save chunks to the database, replacing any existing chunks.

    Args:
        db: Database session
        document_id: ID of the document
        chunks: List of chunk dicts from chunk_document()

    Returns:
        Number of chunks saved
    """
    # Delete existing chunks for this document
    db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).delete()

    for chunk_data in chunks:
        db_chunk = DocumentChunk(
            document_id=document_id,
            content=chunk_data["content"],
            chunk_index=chunk_data["chunk_index"],
            chunk_type=chunk_data["chunk_type"],
            page_number=chunk_data["page_number"],
            char_start=chunk_data["char_start"],
            char_end=chunk_data["char_end"],
        )
        db.add(db_chunk)

    db.commit()
    logger.info(f"Saved {len(chunks)} chunks for document {document_id}")
    return len(chunks)


def _parse_pages(text: str) -> List[tuple]:
    """Parse text with page markers into (page_num, page_text) pairs."""
    parts = PAGE_MARKER_RE.split(text)

    if len(parts) == 1:
        # No page markers found - treat as single page
        return [(1, text)]

    pages = []
    # parts alternates: [pre_text, page_num, page_text, page_num, ...]
    for i in range(1, len(parts), 2):
        page_num = int(parts[i])
        page_text = parts[i + 1] if i + 1 < len(parts) else ""
        if page_text.strip():
            pages.append((page_num, page_text.strip()))

    # Include any text before the first page marker
    if parts[0].strip():
        pages.insert(0, (1, parts[0].strip()))

    return pages or [(1, text)]


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs on double newlines."""
    paras = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paras if p.strip()]


def _split_sentences(
    text: str, chunk_size: int, overlap: int
) -> List[str]:
    """Split long text at sentence boundaries."""
    sentences = SENTENCE_RE.split(text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= chunk_size:
            current = f"{current} {sentence}".strip() if current else sentence
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks or [text[:chunk_size]]


def _make_chunk(
    content: str,
    index: int,
    page_number: Optional[int],
    char_start: int,
    char_end: int,
) -> Dict:
    """Create a chunk dict with metadata."""
    # Detect chunk type from content
    chunk_type = "paragraph"
    if content.startswith("#"):
        chunk_type = "heading"
    elif content.startswith(("-", "*", "1.")):
        chunk_type = "list"
    elif "```" in content:
        chunk_type = "code"

    return {
        "content": content,
        "chunk_index": index,
        "chunk_type": chunk_type,
        "page_number": page_number,
        "char_start": char_start,
        "char_end": char_end,
    }
