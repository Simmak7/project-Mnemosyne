"""
Document task helper functions.

Extracted from tasks.py to keep files under 250 lines.
Handles thumbnail generation, OCR fallback, enrichment, and
status management for the document analysis pipeline.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def sanitize_text(text: str) -> str:
    """Strip NUL bytes and other chars PostgreSQL rejects."""
    if not text:
        return text
    return text.replace("\x00", "")


def mark_document_failed(db, document_id: int, error_msg: str) -> None:
    """Safely mark document as failed, tolerating DB errors."""
    try:
        db.rollback()
        from models import Document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.ai_analysis_status = "failed"
            doc.ai_analysis_result = sanitize_text(str(error_msg)[:500])
            db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass


def generate_thumbnail(
    db, task_id: str, extractor, filepath: str, doc, doc_id: int,
) -> None:
    """Generate thumbnail from first PDF page. Best-effort."""
    try:
        thumb_result = extractor.generate_thumbnail(
            filepath, "uploaded_documents/thumbnails", doc_id,
        )
        doc.thumbnail_path = thumb_result.get("thumbnail_path")
        doc.blur_hash = thumb_result.get("blur_hash")
        db.commit()
    except Exception as thumb_err:
        logger.warning(f"[Task {task_id}] Thumbnail generation failed: {thumb_err}")


def try_vision_ocr(
    db, task_id: str, extraction: dict, text: str, filepath: str, doc,
) -> str:
    """Attempt vision OCR for scanned PDFs. Returns best available text."""
    if not (extraction.get("is_scanned") and not text.strip()):
        return text
    logger.info(f"[Task {task_id}] Scanned PDF detected, trying vision OCR")
    try:
        from features.documents.services.enrichment import DocumentEnricher
        ocr_text = sanitize_text(DocumentEnricher().ocr_with_vision(filepath))
        if ocr_text:
            doc.extracted_text = ocr_text
            doc.extraction_method = "vision_ocr"
            db.commit()
            return ocr_text
    except Exception as ocr_err:
        logger.warning(f"[Task {task_id}] Vision OCR failed: {ocr_err}")
    return text


def run_enrichment(
    db, task_id: str, doc, text: str, user_instructions: Optional[str] = None,
) -> None:
    """Run AI enrichment on extracted text. Updates doc in-place."""
    if not text.strip():
        doc.ai_summary = "No text could be extracted from this document."
        doc.suggested_tags = []
        doc.suggested_wikilinks = []
        db.commit()
        return

    try:
        from features.documents.services.enrichment import DocumentEnricher
        enrichment = DocumentEnricher().enrich_document(
            text, user_instructions=user_instructions,
        )
        doc.ai_summary = enrichment.get("summary", "")
        doc.document_type = enrichment.get("document_type", "unknown")
        doc.suggested_tags = enrichment.get("tags", [])
        doc.suggested_wikilinks = enrichment.get("wikilinks", [])
        doc.ai_analysis_result = enrichment.get("raw_response", "")
        db.commit()
    except Exception as enrich_err:
        logger.error(f"[Task {task_id}] Enrichment failed: {enrich_err}")
        doc.ai_analysis_result = f"Enrichment failed: {enrich_err}"
        db.commit()


def trigger_embeddings(document_id: int, owner_id: int) -> None:
    """Queue embedding generation after successful analysis."""
    try:
        from features.documents.tasks import generate_document_embeddings_task
        logger.info(
            f"Document {document_id} analysis complete, triggering embedding generation"
        )
        generate_document_embeddings_task.delay(document_id, owner_id)
    except Exception as e:
        logger.warning(f"Failed to queue embeddings for document {document_id}: {e}")
