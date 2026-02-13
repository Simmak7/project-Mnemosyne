"""
NexusImportanceScore model - PageRank and access-based importance per note.

Updated during consolidation. Used by DiffusionRanker for DEEP mode.
"""

from sqlalchemy import (
    Column, Integer, Float, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.sql import func
from core.database import Base


class NexusImportanceScore(Base):
    __tablename__ = "nexus_importance_scores"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    note_id = Column(
        Integer,
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False
    )
    pagerank_score = Column(Float, default=0.0)
    access_count = Column(Integer, default=0)
    retrieval_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("owner_id", "note_id", name="uq_importance_owner_note"),
    )
