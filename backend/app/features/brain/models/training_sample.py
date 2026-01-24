"""TrainingSample model for storing condensed knowledge for LoRA training."""

import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base


class MemoryType(str, enum.Enum):
    """Classification of knowledge by memory type.

    - EPISODIC: Time-bound, specific events - RAG only (not trained)
    - SEMANTIC: Stable concepts and facts - training candidate
    - PREFERENCE: High recurrence patterns - LoRA priority
    """
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PREFERENCE = "preference"


class TrainingSample(Base):
    """Training sample generated from user's notes for LoRA fine-tuning.

    Each sample represents condensed knowledge extracted from user content,
    formatted as instruction-output pairs for instruction tuning.

    Types of samples:
    - identity: Who the user is, their context
    - interests: Topics they frequently engage with
    - cognitive_style: How they organize thoughts
    - preferences: Writing style, formats preferred
    - projects: Ongoing work and collaborations
    - behaviors: Common patterns and habits
    """
    __tablename__ = "brain_training_samples"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Sample content (instruction tuning format)
    instruction = Column(Text, nullable=False)  # The question/prompt
    input_text = Column(Text, nullable=True)    # Optional context
    output = Column(Text, nullable=False)       # The expected response

    # Classification
    sample_type = Column(String(50), nullable=False, index=True)  # identity, interests, etc.
    memory_type = Column(Enum(MemoryType), nullable=False, default=MemoryType.SEMANTIC)

    # Provenance tracking
    source_note_ids = Column(JSONB, default=list)    # List[int] - notes that informed this
    source_image_ids = Column(JSONB, default=list)   # List[int] - images that informed this
    source_chunk_ids = Column(JSONB, default=list)   # List[int] - specific chunks used

    # Quality signals
    confidence = Column(Float, default=0.7)          # 0.0-1.0 extraction confidence
    recurrence = Column(Integer, default=1)          # How many times this concept appeared
    stability_score = Column(Float, default=0.5)     # How stable this fact is (0.0-1.0)
    centrality_score = Column(Float, default=0.0)    # Graph centrality of concept

    # Training metadata
    is_trained = Column(String(20), default="pending")  # pending, trained, skipped
    adapter_version = Column(Integer, nullable=True)     # Which adapter version used this

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", backref="training_samples")


class CondensedFact(Base):
    """Individual fact extracted during semantic condensation.

    Facts are atomic pieces of knowledge extracted from notes.
    Multiple facts can be combined into training samples.
    """
    __tablename__ = "brain_condensed_facts"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Fact content
    fact_text = Column(Text, nullable=False)
    concept = Column(String(255), nullable=False, index=True)  # Main concept/entity

    # Source tracking
    source_note_id = Column(Integer, ForeignKey("notes.id", ondelete="SET NULL"), nullable=True)
    source_chunk_id = Column(Integer, nullable=True)

    # Classification
    fact_type = Column(String(50), nullable=False)  # entity, relation, attribute, event
    memory_type = Column(Enum(MemoryType), nullable=False, default=MemoryType.SEMANTIC)

    # Quality signals
    confidence = Column(Float, default=0.7)
    recurrence = Column(Integer, default=1)
    stability_score = Column(Float, default=0.5)

    # Timestamps
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", backref="condensed_facts")
