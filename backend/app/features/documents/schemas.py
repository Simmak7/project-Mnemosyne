"""
Documents Feature - Pydantic Schemas

Request/response models for document upload, review, and management.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============================================
# Upload Schemas
# ============================================

class DocumentUploadResponse(BaseModel):
    """Response after uploading a PDF."""
    message: str
    document_id: int
    filename: str
    task_id: Optional[str] = None
    analysis_status: str = "queued"


class TaskStatusResponse(BaseModel):
    """Celery task status polling response."""
    task_id: str
    status: str
    ready: bool = False
    message: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


# ============================================
# Document Response Schemas
# ============================================

class DocumentResponse(BaseModel):
    """Full document detail response."""
    id: int
    filename: str
    display_name: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    document_type: Optional[str] = None
    thumbnail_path: Optional[str] = None
    blur_hash: Optional[str] = None
    extraction_method: Optional[str] = None
    extracted_text_length: Optional[int] = None
    ai_summary: Optional[str] = None
    ai_analysis_status: str = "pending"
    suggested_tags: Optional[List[str]] = None
    suggested_wikilinks: Optional[List[str]] = None
    summary_note_id: Optional[int] = None
    text_appended_to_note: bool = False
    is_trashed: bool = False
    uploaded_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""
    documents: List[DocumentResponse]
    total: int
    skip: int = 0
    limit: int = 50


# ============================================
# Review & Approval Schemas
# ============================================

class ReviewApprovalRequest(BaseModel):
    """Request to approve AI suggestions and create a summary note."""
    approved_tags: List[str] = Field(default_factory=list)
    approved_wikilinks: List[str] = Field(default_factory=list)
    summary_title: Optional[str] = None
    summary_content: Optional[str] = None


class ReviewApprovalResponse(BaseModel):
    """Response after approving suggestions."""
    message: str
    document_id: int
    note_id: int
    tags_applied: List[str]
    status: str = "completed"


class SuggestionsUpdateRequest(BaseModel):
    """Edit suggestions before approval."""
    suggested_tags: Optional[List[str]] = None
    suggested_wikilinks: Optional[List[str]] = None
    ai_summary: Optional[str] = None


# ============================================
# Retry / Delete Schemas
# ============================================

class RetryResponse(BaseModel):
    """Response for retry analysis."""
    message: str
    document_id: int
    task_id: str
    analysis_status: str = "queued"


class DeleteResponse(BaseModel):
    """Response for document deletion."""
    message: str
    document_id: int


class ExtractTextToNoteResponse(BaseModel):
    """Response after appending extracted text to summary note."""
    message: str
    document_id: int
    note_id: int
    chars_appended: int
