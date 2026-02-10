"""
Documents Feature - Celery Tasks

Async document processing pipeline:
1. Extract text via pdfplumber
2. Generate thumbnail + blur hash
3. If scanned -> vision OCR fallback
4. AI enrichment via Qwen3:8b
5. Store results, set status to needs_review
"""

from celery import Task
from core.celery_app import celery_app
import logging

from core import database


def sanitize_text(text: str) -> str:
    """Strip NUL bytes and other chars PostgreSQL rejects."""
    if not text:
        return text
    return text.replace("\x00", "")

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session lifecycle."""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = database.SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="features.documents.tasks.analyze_document",
    max_retries=2,
    default_retry_delay=60,
)
def analyze_document_task(self, document_id: int, filepath: str, user_instructions: str = None):
    """
    Celery task: full document analysis pipeline.

    Steps:
    1. Update status to 'processing'
    2. Extract text with pdfplumber
    3. Generate thumbnail from first page
    4. If scanned (sparse text) -> OCR fallback with Llama Vision
    5. AI enrichment with Qwen3:8b (summary, tags, wikilinks)
    6. Store results and set status to 'needs_review'
    """
    logger.info(f"[Task {self.request.id}] Starting analysis for document {document_id}")

    try:
        from models import Document
        from features.documents.services.extraction import PDFExtractor
        from features.documents.services.enrichment import DocumentEnricher

        # 1. Update status
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"[Task {self.request.id}] Document {document_id} not found")
            return {"status": "failed", "error": "Document not found"}

        doc.ai_analysis_status = "processing"
        self.db.commit()

        # 2. Extract text
        extractor = PDFExtractor()
        extraction = extractor.extract_text(filepath)

        doc.extracted_text = sanitize_text(extraction["text"])
        doc.page_count = extraction["page_count"]
        doc.extraction_method = "pdfplumber"
        self.db.commit()

        # 3. Generate thumbnail
        try:
            thumb_result = extractor.generate_thumbnail(
                filepath, "uploaded_documents/thumbnails", document_id
            )
            doc.thumbnail_path = thumb_result.get("thumbnail_path")
            doc.blur_hash = thumb_result.get("blur_hash")
            self.db.commit()
        except Exception as thumb_err:
            logger.warning(f"[Task {self.request.id}] Thumbnail generation failed: {thumb_err}")

        # 4. Vision OCR fallback for scanned PDFs
        text_for_enrichment = sanitize_text(extraction["text"])
        if extraction.get("is_scanned") and not text_for_enrichment.strip():
            logger.info(f"[Task {self.request.id}] Scanned PDF detected, trying vision OCR")
            try:
                enricher = DocumentEnricher()
                ocr_text = sanitize_text(enricher.ocr_with_vision(filepath))
                if ocr_text:
                    text_for_enrichment = ocr_text
                    doc.extracted_text = ocr_text
                    doc.extraction_method = "vision_ocr"
                    self.db.commit()
            except Exception as ocr_err:
                logger.warning(f"[Task {self.request.id}] Vision OCR failed: {ocr_err}")

        # 5. AI enrichment
        if text_for_enrichment.strip():
            try:
                enricher = DocumentEnricher()
                enrichment = enricher.enrich_document(
                    text_for_enrichment, user_instructions=user_instructions
                )

                doc.ai_summary = enrichment.get("summary", "")
                doc.document_type = enrichment.get("document_type", "unknown")
                doc.suggested_tags = enrichment.get("tags", [])
                doc.suggested_wikilinks = enrichment.get("wikilinks", [])
                doc.ai_analysis_result = enrichment.get("raw_response", "")
                self.db.commit()
            except Exception as enrich_err:
                logger.error(f"[Task {self.request.id}] Enrichment failed: {enrich_err}")
                doc.ai_analysis_result = f"Enrichment failed: {enrich_err}"
                self.db.commit()
        else:
            doc.ai_summary = "No text could be extracted from this document."
            doc.suggested_tags = []
            doc.suggested_wikilinks = []
            self.db.commit()

        # 6. Set final status
        doc.ai_analysis_status = "needs_review"
        self.db.commit()

        logger.info(f"[Task {self.request.id}] Document {document_id} analysis complete")
        return {
            "status": "completed",
            "document_id": document_id,
            "page_count": doc.page_count,
            "extraction_method": doc.extraction_method,
        }

    except Exception as e:
        logger.error(f"[Task {self.request.id}] Document analysis failed: {e}", exc_info=True)
        try:
            self.db.rollback()
            from models import Document
            doc = self.db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.ai_analysis_status = "failed"
                doc.ai_analysis_result = sanitize_text(str(e))
                self.db.commit()
        except Exception:
            self.db.rollback()
        return {"status": "failed", "error": str(e)}


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="features.documents.tasks.generate_document_embeddings",
    max_retries=2,
    default_retry_delay=60,
)
def generate_document_embeddings_task(self, document_id: int):
    """
    Celery task: chunk document text and generate embeddings.

    Steps:
    1. Load document and its extracted text
    2. Chunk text into smaller pieces with page/offset metadata
    3. Save chunks to document_chunks table
    4. Generate embedding for each chunk via Ollama
    5. Generate embedding for the document summary
    """
    logger.info(f"[Task {self.request.id}] Generating embeddings for document {document_id}")

    try:
        from models import Document, DocumentChunk
        from features.documents.services.chunking import chunk_document, save_chunks
        from features.search.logic.embeddings import generate_embedding

        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found")
            return {"status": "failed", "error": "Document not found"}

        # 1. Chunk the extracted text
        text = doc.extracted_text or ""
        if not text.strip():
            logger.warning(f"Document {document_id} has no extracted text")
            return {"status": "skipped", "reason": "No text"}

        chunks = chunk_document(text)
        saved = save_chunks(self.db, document_id, chunks)
        logger.info(f"Saved {saved} chunks for document {document_id}")

        # 2. Generate embeddings for each chunk
        embedded_count = 0
        db_chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()

        for db_chunk in db_chunks:
            try:
                embedding = generate_embedding(db_chunk.content)
                if embedding:
                    db_chunk.embedding = embedding
                    embedded_count += 1
            except Exception as emb_err:
                logger.warning(f"Chunk {db_chunk.id} embedding failed: {emb_err}")

        # 3. Generate embedding for document summary
        if doc.ai_summary:
            try:
                summary_embedding = generate_embedding(doc.ai_summary)
                if summary_embedding:
                    doc.embedding = summary_embedding
            except Exception as emb_err:
                logger.warning(f"Document summary embedding failed: {emb_err}")

        self.db.commit()

        logger.info(
            f"Document {document_id}: {embedded_count}/{len(db_chunks)} "
            f"chunk embeddings generated"
        )
        return {
            "status": "completed",
            "document_id": document_id,
            "chunks": len(db_chunks),
            "embedded": embedded_count,
        }

    except Exception as e:
        logger.error(f"Document embedding task failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
