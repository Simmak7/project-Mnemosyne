"""BrainAdapter model for LoRA adapter versioning."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base


class BrainAdapter(Base):
    """LoRA adapter version for a user's personalized AI brain.

    Each adapter represents a fine-tuned version of the base model
    trained on the user's condensed knowledge.

    Storage structure:
    /data/adapters/{user_id}/
    ├── brain_v1/
    │   ├── adapter_config.json
    │   ├── adapter_model.safetensors
    │   └── metadata.json
    └── active -> brain_v1  # Symlink to active version
    """
    __tablename__ = "brain_adapters"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Version info
    version = Column(Integer, nullable=False)
    parent_version = Column(Integer, nullable=True)  # For incremental training

    # Base model
    base_model = Column(String(100), nullable=False)  # e.g., "llama3.1:8b"

    # Training statistics
    dataset_size = Column(Integer, default=0)    # Number of training samples
    notes_covered = Column(Integer, default=0)   # Notes included in training
    images_covered = Column(Integer, default=0)  # Images included
    journal_days = Column(Integer, default=0)    # Days of journal coverage

    # Training configuration
    training_config = Column(JSONB, default=dict)  # LoRA hyperparameters

    # Storage
    adapter_path = Column(String(500), nullable=True)  # Path to adapter files

    # Status
    status = Column(String(20), default="created")  # created, training, ready, failed
    is_active = Column(Boolean, default=False, index=True)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    training_started_at = Column(DateTime(timezone=True), nullable=True)
    training_completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    owner = relationship("User", backref="brain_adapters")


class IndexingRun(Base):
    """Record of a brain indexing run.

    Tracks when the indexer processed user content to generate training samples.
    Used for incremental updates - only process content changed since last run.
    """
    __tablename__ = "brain_indexing_runs"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Run statistics
    notes_processed = Column(Integer, default=0)
    images_processed = Column(Integer, default=0)
    facts_extracted = Column(Integer, default=0)
    samples_generated = Column(Integer, default=0)

    # Change detection
    notes_changed = Column(Integer, default=0)  # Notes modified since last run
    last_note_updated = Column(DateTime(timezone=True), nullable=True)

    # Status
    status = Column(String(20), default="running")  # running, completed, failed
    error_message = Column(Text, nullable=True)

    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Relationships
    owner = relationship("User", backref="indexing_runs")
