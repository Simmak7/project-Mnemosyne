"""
Documents Feature - Celery Tasks.

Pipeline: extract text -> thumbnail -> OCR fallback -> AI enrichment -> embeddings.
Error categories: transient (retry w/ backoff), permanent (fail now), unknown (retry then fail).
"""

from celery import Task
from core.celery_app import celery_app
import logging
from requests.exceptions import ConnectionError, Timeout

from core import database
from features.documents.tasks_helpers import (
    sanitize_text,
    mark_document_failed,
    generate_thumbnail,
    try_vision_ocr,
    run_enrichment,
    trigger_embeddings,
)

logger = logging.getLogger(__name__)

# Errors that should never be retried
PERMANENT_ERRORS = (FileNotFoundError, ValueError, PermissionError)


class DatabaseTask(Task):
    """Base task with database session lifecycle."""
    _db = None

    @property
    def db(self) -> "database.SessionLocal":
        if self._db is None:
            self._db = database.SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs) -> None:
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="features.documents.tasks.analyze_document",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    reject_on_worker_lost=True,
)
def analyze_document_task(
    self, document_id: int, filepath: str, user_instructions: str = None,
) -> dict:
    """Full document analysis pipeline. Auto-triggers embeddings on completion.
    Embeddings are also re-triggered on approval (see approval.py)."""
    logger.info(f"[Task {self.request.id}] Starting analysis for document {document_id}")

    try:
        from models import Document
        from features.documents.services.extraction import PDFExtractor

        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"[Task {self.request.id}] Document {document_id} not found")
            return {"status": "failed", "error": "Document not found"}

        doc.ai_analysis_status = "processing"
        self.db.commit()

        # Extract text
        extractor = PDFExtractor()
        extraction = extractor.extract_text(filepath)
        doc.extracted_text = sanitize_text(extraction["text"])
        doc.page_count = extraction["page_count"]
        doc.extraction_method = "pdfplumber"
        self.db.commit()

        # Generate thumbnail (best-effort)
        generate_thumbnail(self.db, self.request.id, extractor, filepath, doc, document_id)

        # Vision OCR fallback for scanned PDFs
        text_for_enrichment = sanitize_text(extraction["text"])
        text_for_enrichment = try_vision_ocr(
            self.db, self.request.id, extraction, text_for_enrichment, filepath, doc,
        )

        # AI enrichment
        run_enrichment(self.db, self.request.id, doc, text_for_enrichment, user_instructions)

        # Set final status
        doc.ai_analysis_status = "needs_review"
        self.db.commit()

        logger.info(f"[Task {self.request.id}] Document {document_id} analysis complete")

        # Auto-trigger embedding generation for RAG searchability.
        # Makes document searchable immediately. The approval flow also
        # re-triggers embeddings with the final summary note included.
        trigger_embeddings(document_id, doc.owner_id)

        return {
            "status": "completed",
            "document_id": document_id,
            "page_count": doc.page_count,
            "extraction_method": doc.extraction_method,
        }

    except PERMANENT_ERRORS as e:
        error_msg = f"Permanent error: {e}"
        logger.error(f"[Task {self.request.id}] {error_msg}")
        mark_document_failed(self.db, document_id, error_msg)
        return {"status": "failed", "error": error_msg}

    except (ConnectionError, Timeout, OSError) as e:
        error_msg = f"Transient error: {e}"
        logger.warning(f"[Task {self.request.id}] {error_msg}, scheduling retry")
        mark_document_failed(self.db, document_id, error_msg)
        raise self.retry(exc=e, countdown=120 * (self.request.retries + 1))

    except Exception as e:
        logger.error(f"[Task {self.request.id}] Document analysis failed: {e}", exc_info=True)
        mark_document_failed(self.db, document_id, str(e))
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=120 * (self.request.retries + 1))
        return {"status": "failed", "error": str(e)}


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="features.documents.tasks.generate_document_embeddings",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    reject_on_worker_lost=True,
)
def generate_document_embeddings_task(
    self, document_id: int, owner_id: int = None,
) -> dict:
    """Chunk document text and generate embeddings. Defensively checks analysis status.
    Failure here does not affect document readability, only RAG search."""
    logger.info(f"[Task {self.request.id}] Generating embeddings for document {document_id}")

    try:
        from models import Document, DocumentChunk
        from features.documents.services.chunking import chunk_document, save_chunks
        from features.search.logic.embeddings import generate_embedding

        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found")
            return {"status": "failed", "error": "Document not found"}

        # Defensive: analysis must have produced text before embedding
        if doc.ai_analysis_status in ("pending", "queued", "processing"):
            logger.warning(
                f"Document {document_id} analysis not complete "
                f"(status={doc.ai_analysis_status}), skipping embeddings"
            )
            return {"status": "skipped", "reason": "Analysis not complete"}

        text = doc.extracted_text or ""
        if not text.strip():
            logger.warning(f"Document {document_id} has no extracted text")
            return {"status": "skipped", "reason": "No text"}

        chunks = chunk_document(text)
        saved = save_chunks(self.db, document_id, chunks)
        logger.info(f"Saved {saved} chunks for document {document_id}")

        # Generate embeddings for each chunk
        embedded_count = _embed_chunks(self.db, document_id)

        # Generate embedding for document summary
        _embed_summary(doc)

        self.db.commit()

        logger.info(f"Document {document_id}: {embedded_count} chunk embeddings generated")
        return {"status": "completed", "document_id": document_id, "embedded": embedded_count}

    except PERMANENT_ERRORS as e:
        logger.error(f"Document embedding permanent failure: {e}")
        return {"status": "failed", "error": str(e)}

    except (ConnectionError, Timeout, OSError) as e:
        logger.warning(f"Document embedding transient error: {e}, scheduling retry")
        raise self.retry(exc=e, countdown=120 * (self.request.retries + 1))

    except Exception as e:
        logger.error(f"Document embedding task failed: {e}", exc_info=True)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=120 * (self.request.retries + 1))
        return {"status": "failed", "error": str(e)}


# ── Private helpers ───────────────────────────────────────────────


def _embed_chunks(db, document_id: int) -> int:
    """Generate embeddings for all document chunks. Returns count."""
    from models import DocumentChunk
    from features.search.logic.embeddings import generate_embedding

    db_chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).order_by(DocumentChunk.chunk_index).all()

    embedded = 0
    for chunk in db_chunks:
        try:
            embedding = generate_embedding(chunk.content)
            if embedding:
                chunk.embedding = embedding
                embedded += 1
        except Exception as e:
            logger.warning(f"Chunk {chunk.id} embedding failed: {e}")
    return embedded


def _embed_summary(doc) -> None:
    """Generate embedding for the document summary."""
    if not doc.ai_summary:
        return
    try:
        from features.search.logic.embeddings import generate_embedding
        summary_embedding = generate_embedding(doc.ai_summary)
        if summary_embedding:
            doc.embedding = summary_embedding
    except Exception as e:
        logger.warning(f"Document summary embedding failed: {e}")
