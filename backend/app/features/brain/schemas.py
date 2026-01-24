"""Pydantic schemas for Brain feature API."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class MemoryTypeEnum(str, Enum):
    """Memory type classification."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PREFERENCE = "preference"


class SampleTypeEnum(str, Enum):
    """Training sample type."""
    IDENTITY = "identity"
    INTERESTS = "interests"
    COGNITIVE_STYLE = "cognitive_style"
    PREFERENCES = "preferences"
    PROJECTS = "projects"
    BEHAVIORS = "behaviors"


# ============================================
# Brain Status Schemas
# ============================================

class BrainStatusResponse(BaseModel):
    """Current status of user's AI brain."""
    has_adapter: bool
    active_version: Optional[int] = None
    base_model: Optional[str] = None
    status: str  # ready, training, indexing, none

    # Statistics
    notes_indexed: int = 0
    images_indexed: int = 0
    samples_count: int = 0
    facts_count: int = 0

    # Last activity
    last_indexed: Optional[datetime] = None
    last_trained: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdapterResponse(BaseModel):
    """Brain adapter version details."""
    id: int
    version: int
    base_model: str
    status: str
    is_active: bool

    # Training stats
    dataset_size: int
    notes_covered: int
    images_covered: int

    # Config
    training_config: Dict[str, Any]

    # Timestamps
    created_at: datetime
    training_completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdapterListResponse(BaseModel):
    """List of adapter versions."""
    adapters: List[AdapterResponse]
    active_version: Optional[int] = None


# ============================================
# Training Sample Schemas
# ============================================

class TrainingSampleBase(BaseModel):
    """Base schema for training sample."""
    instruction: str
    input_text: Optional[str] = None
    output: str
    sample_type: str
    memory_type: MemoryTypeEnum = MemoryTypeEnum.SEMANTIC


class TrainingSampleCreate(TrainingSampleBase):
    """Schema for creating a training sample."""
    source_note_ids: List[int] = Field(default_factory=list)
    source_image_ids: List[int] = Field(default_factory=list)
    confidence: float = 0.7


class TrainingSampleResponse(TrainingSampleBase):
    """Schema for training sample response."""
    id: int
    source_note_ids: List[int]
    source_image_ids: List[int]
    confidence: float
    recurrence: int
    is_trained: str
    created_at: datetime

    class Config:
        from_attributes = True


class TrainingSampleListResponse(BaseModel):
    """List of training samples with stats."""
    samples: List[TrainingSampleResponse]
    total: int
    by_type: Dict[str, int]
    by_memory_type: Dict[str, int]


# ============================================
# Condensed Fact Schemas
# ============================================

class CondensedFactResponse(BaseModel):
    """Schema for condensed fact response."""
    id: int
    fact_text: str
    concept: str
    fact_type: str
    memory_type: MemoryTypeEnum
    confidence: float
    recurrence: int
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


# ============================================
# Indexing Schemas
# ============================================

class IndexingRunResponse(BaseModel):
    """Schema for indexing run result."""
    id: int
    status: str
    notes_processed: int
    images_processed: int
    facts_extracted: int
    samples_generated: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class TriggerIndexingResponse(BaseModel):
    """Response when triggering indexing."""
    task_id: str
    status: str
    message: str


class IndexingProgressResponse(BaseModel):
    """Progress of ongoing indexing."""
    task_id: str
    status: str
    progress: int  # 0-100
    current_step: str
    notes_processed: int = 0
    facts_extracted: int = 0


# ============================================
# Training Schemas
# ============================================

class TriggerTrainingRequest(BaseModel):
    """Request to trigger brain training."""
    base_model: str = "llama3.1:8b"
    lora_r: int = 16
    lora_alpha: int = 32
    epochs: int = 3
    learning_rate: float = 2e-4


class TriggerTrainingResponse(BaseModel):
    """Response when triggering training."""
    task_id: str
    status: str
    adapter_version: int
    message: str


class TrainingProgressResponse(BaseModel):
    """Progress of ongoing training."""
    task_id: str
    status: str
    progress: int  # 0-100
    current_step: str
    samples_processed: int = 0
    estimated_time_remaining: Optional[int] = None


# ============================================
# Graph Signal Schemas
# ============================================

class GraphSignalsResponse(BaseModel):
    """Graph analysis signals for a concept."""
    concept: str
    centrality: float  # 0.0-1.0, how connected
    recurrence: int    # How often mentioned
    cluster_id: Optional[int] = None
    related_concepts: List[str]


# ============================================
# Export Schemas
# ============================================

class ExportDatasetRequest(BaseModel):
    """Request to export training dataset."""
    format: str = "jsonl"  # jsonl, csv
    memory_types: Optional[List[MemoryTypeEnum]] = None
    sample_types: Optional[List[str]] = None


class ExportDatasetResponse(BaseModel):
    """Response with dataset export info."""
    download_url: str
    sample_count: int
    format: str
    created_at: datetime


# ============================================
# Inference Schemas
# ============================================

class BrainGenerateRequest(BaseModel):
    """Request to generate text using trained brain."""
    prompt: str
    max_length: int = 256
    temperature: float = 0.7
    top_p: float = 0.9


class BrainChatRequest(BaseModel):
    """Request for chat with trained brain."""
    messages: List[Dict[str, str]]  # [{"role": "user", "content": "..."}]
    max_length: int = 256
    temperature: float = 0.7


class BrainGenerateResponse(BaseModel):
    """Response from brain generation."""
    text: str
    adapter_version: Optional[int] = None
    model_loaded: bool = True


class BrainChatResponse(BaseModel):
    """Response from brain chat."""
    message: str
    adapter_version: Optional[int] = None
    model_loaded: bool = True


class AdapterDiskUsageResponse(BaseModel):
    """Disk usage statistics for adapters."""
    total_bytes: int
    total_mb: float
    adapter_count: int
