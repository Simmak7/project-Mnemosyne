"""
Documents Feature - Service Layer

Business logic for document upload, validation, and CRUD operations.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy.orm import Session
from fastapi import HTTPException

from core import config
from models import Document, DocumentCollectionDocument

logger = logging.getLogger(__name__)

# Allowed document MIME types
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf": ".pdf",
}

MAX_PDF_SIZE_BYTES = int(os.getenv("MAX_PDF_SIZE_MB", "50")) * 1024 * 1024
DOCUMENT_UPLOAD_DIR = os.getenv("DOCUMENT_UPLOAD_DIR", "uploaded_documents")
DOCUMENT_THUMBNAIL_DIR = os.getenv("DOCUMENT_THUMBNAIL_DIR", "uploaded_documents/thumbnails")


class DocumentService:
    """Service class for document operations."""

    @staticmethod
    def validate_file(
        content_type: str, file_size: int, filename: str
    ) -> Tuple[bool, Optional[str]]:
        """Validate uploaded document file."""
        if content_type not in ALLOWED_DOCUMENT_TYPES:
            allowed = ", ".join(ALLOWED_DOCUMENT_TYPES.keys())
            return False, f"Unsupported file type: {content_type}. Allowed: {allowed}"

        if file_size > MAX_PDF_SIZE_BYTES:
            max_mb = MAX_PDF_SIZE_BYTES // (1024 * 1024)
            return False, f"File too large. Maximum size: {max_mb}MB"

        if file_size == 0:
            return False, "File is empty"

        return True, None

    @staticmethod
    def save_file(contents: bytes, filename: str) -> str:
        """Save document file to disk."""
        os.makedirs(DOCUMENT_UPLOAD_DIR, exist_ok=True)
        filepath = os.path.join(DOCUMENT_UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(contents)
        return filepath

    @staticmethod
    def create_document(
        db: Session,
        filename: str,
        filepath: str,
        owner_id: int,
        file_size: int,
        display_name: Optional[str] = None,
    ) -> Document:
        """Create a new document record in the database."""
        doc = Document(
            filename=filename,
            filepath=filepath,
            display_name=display_name or filename,
            file_size=file_size,
            owner_id=owner_id,
            ai_analysis_status="queued",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        logger.info(f"Document created: ID {doc.id}, file {filename}")
        return doc

    @staticmethod
    def get_document(db: Session, doc_id: int, owner_id: int) -> Optional[Document]:
        """Get a single document by ID, owned by user."""
        return db.query(Document).filter(
            Document.id == doc_id,
            Document.owner_id == owner_id,
        ).first()

    # Map frontend sort keys to model columns
    SORT_COLUMNS = {
        "uploaded_at": Document.uploaded_at,
        "name": Document.display_name,
        "file_size": Document.file_size,
        "page_count": Document.page_count,
        "status": Document.ai_analysis_status,
    }

    @staticmethod
    def get_documents_by_user(
        db: Session,
        owner_id: int,
        status_filter: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
        include_trashed: bool = False,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "desc",
        collection_id: Optional[int] = None,
    ) -> Tuple[List[Document], int]:
        """Get paginated documents for a user with optional status filter and sorting."""
        query = db.query(Document).filter(Document.owner_id == owner_id)

        if not include_trashed:
            query = query.filter(Document.is_trashed == False)

        if status_filter:
            query = query.filter(Document.ai_analysis_status == status_filter)

        if collection_id:
            query = query.join(
                DocumentCollectionDocument,
                Document.id == DocumentCollectionDocument.document_id
            ).filter(DocumentCollectionDocument.collection_id == collection_id)

        total = query.count()

        # Apply sorting
        col = DocumentService.SORT_COLUMNS.get(sort_by, Document.uploaded_at)
        order = col.asc() if sort_order == "asc" else col.desc()
        docs = query.order_by(order).offset(skip).limit(limit).all()
        return docs, total

    @staticmethod
    def update_analysis_status(
        db: Session,
        doc_id: int,
        status: str,
        result: Optional[str] = None,
    ):
        """Update document analysis status."""
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.ai_analysis_status = status
            if result:
                doc.ai_analysis_result = result
            if status == "completed":
                doc.processed_at = datetime.now(timezone.utc)
            db.commit()

    @staticmethod
    def move_to_trash(db: Session, doc_id: int, owner_id: int) -> bool:
        """Soft-delete a document."""
        doc = db.query(Document).filter(
            Document.id == doc_id, Document.owner_id == owner_id
        ).first()
        if not doc:
            return False
        doc.is_trashed = True
        doc.trashed_at = datetime.now(timezone.utc)
        db.commit()
        return True

    @staticmethod
    def restore_from_trash(db: Session, doc_id: int, owner_id: int) -> bool:
        """Restore a document from trash."""
        doc = db.query(Document).filter(
            Document.id == doc_id, Document.owner_id == owner_id
        ).first()
        if not doc:
            return False
        doc.is_trashed = False
        doc.trashed_at = None
        db.commit()
        return True

    @staticmethod
    def file_exists(filepath: str) -> bool:
        """Check if document file exists on disk."""
        return os.path.exists(filepath)
