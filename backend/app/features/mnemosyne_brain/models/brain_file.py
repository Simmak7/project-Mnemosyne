"""BrainFile model - stores each brain markdown file per user."""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from core.database import Base


class BrainFile(Base):
    """A single brain file (e.g. soul.md, askimap.md, topic_0.md) for a user."""
    __tablename__ = "brain_files"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_key = Column(String(100), nullable=False)  # "mnemosyne", "soul", "askimap", "topic_0"
    file_type = Column(String(20), nullable=False)  # "core" or "topic"
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False, default="")
    content_hash = Column(String(64), nullable=True)  # SHA-256 for change detection
    community_id = Column(Integer, nullable=True)  # Louvain community ID (topics only)
    topic_keywords = Column(JSONB, nullable=True)  # ["python", "ml", ...]
    source_note_ids = Column(JSONB, nullable=True)  # [12, 34, 56]
    embedding = Column(Vector(768), nullable=True)  # For topic relevance matching
    version = Column(Integer, default=1, nullable=False)
    is_stale = Column(Boolean, default=False, nullable=False)
    is_user_edited = Column(Boolean, default=False, nullable=False)
    token_count_approx = Column(Integer, nullable=True)
    build_id = Column(Integer, ForeignKey("brain_build_logs.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("owner_id", "file_key", name="uq_brain_file_owner_key"),
    )
