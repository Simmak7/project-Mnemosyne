"""Pydantic schemas for Mnemosyne Brain API."""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================
# Brain File Schemas
# ============================================

class BrainFileResponse(BaseModel):
    """Response for a single brain file."""
    file_key: str
    file_type: str
    title: str
    content: str
    content_hash: Optional[str] = None
    token_count_approx: Optional[int] = None
    is_stale: bool = False
    is_user_edited: bool = False
    version: int = 1
    topic_keywords: Optional[List[str]] = None
    source_note_ids: Optional[List[int]] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BrainFileSummary(BaseModel):
    """Summary (without full content) for listing brain files."""
    file_key: str
    file_type: str
    title: str
    token_count_approx: Optional[int] = None
    is_stale: bool = False
    is_user_edited: bool = False
    version: int = 1
    topic_keywords: Optional[List[str]] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BrainFileUpdate(BaseModel):
    """Request to update a brain file's content."""
    content: str = Field(..., min_length=1, max_length=50000)


# ============================================
# Brain Build Schemas
# ============================================

class BrainBuildRequest(BaseModel):
    """Request to trigger a brain build."""
    full_rebuild: bool = True


class BrainBuildStatusResponse(BaseModel):
    """Current build progress."""
    build_id: Optional[int] = None
    build_type: Optional[str] = None
    status: str  # "running", "completed", "failed", "none"
    progress_pct: int = 0
    current_step: Optional[str] = None
    notes_processed: int = 0
    communities_detected: int = 0
    topic_files_generated: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BrainBuildHistoryItem(BaseModel):
    """A past build entry."""
    id: int
    build_type: str
    status: str
    notes_processed: int = 0
    communities_detected: int = 0
    topic_files_generated: int = 0
    total_tokens_generated: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# Brain Status
# ============================================

class BrainStatusResponse(BaseModel):
    """Overall brain status."""
    has_brain: bool = False
    is_ready: bool = False
    is_building: bool = False
    is_stale: bool = False
    total_files: int = 0
    core_files: int = 0
    topic_files: int = 0
    stale_files: int = 0
    total_tokens: int = 0
    last_build_at: Optional[datetime] = None
    notes_count: int = 0
    min_notes_required: int = 3


# ============================================
# Brain Chat Schemas
# ============================================

class BrainQueryRequest(BaseModel):
    """Request for a brain-mode query."""
    query: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[int] = None
    auto_create_conversation: bool = True


class BrainQueryResponse(BaseModel):
    """Response from a brain-mode query."""
    answer: str
    brain_files_used: List[str] = []
    topics_matched: List[dict] = []
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None


class TopicMatch(BaseModel):
    """A matched topic with relevance score."""
    file_key: str
    title: str
    score: float
    match_method: str  # "keyword", "embedding", "both"


# ============================================
# Brain Conversation Schemas
# ============================================

class BrainConversationCreate(BaseModel):
    """Request to create a brain conversation."""
    title: Optional[str] = None


class BrainConversationResponse(BaseModel):
    """Response for a brain conversation."""
    id: int
    title: Optional[str] = None
    brain_files_used: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_archived: bool = False

    class Config:
        from_attributes = True


class BrainMessageResponse(BaseModel):
    """Response for a brain message."""
    id: int
    role: str
    content: str
    brain_files_loaded: Optional[List[str]] = None
    topics_matched: Optional[List[dict]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BrainConversationWithMessages(BaseModel):
    """Full conversation with messages."""
    id: int
    title: Optional[str] = None
    brain_files_used: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_archived: bool = False
    messages: List[BrainMessageResponse] = []

    class Config:
        from_attributes = True


class BrainConversationUpdate(BaseModel):
    """Request to update a brain conversation."""
    title: Optional[str] = None
    is_archived: Optional[bool] = None
