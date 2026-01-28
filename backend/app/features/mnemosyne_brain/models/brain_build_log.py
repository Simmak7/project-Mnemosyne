"""BrainBuildLog model - tracks brain build operations."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from core.database import Base


class BrainBuildLog(Base):
    """Tracks brain build operations (full, partial, evolution)."""
    __tablename__ = "brain_build_logs"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    build_type = Column(String(20), nullable=False)  # "full", "partial", "evolution"
    notes_processed = Column(Integer, default=0)
    communities_detected = Column(Integer, default=0)
    topic_files_generated = Column(Integer, default=0)
    total_tokens_generated = Column(Integer, default=0)
    status = Column(String(20), default="running", nullable=False)  # "running", "completed", "failed"
    progress_pct = Column(Integer, default=0)
    current_step = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
