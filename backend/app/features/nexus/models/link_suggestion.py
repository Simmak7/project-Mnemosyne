"""
NexusLinkSuggestion model - Missing link detection results.

Suggests wikilinks between semantically similar notes
that aren't yet connected via wikilinks.
"""

from sqlalchemy import (
    Column, Integer, Float, String, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.sql import func
from core.database import Base


class NexusLinkSuggestion(Base):
    __tablename__ = "nexus_link_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    source_note_id = Column(
        Integer,
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False
    )
    target_note_id = Column(
        Integer,
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False
    )
    similarity_score = Column(Float, nullable=False)
    co_retrieval_count = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending | accepted | dismissed
    suggested_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("owner_id", "source_note_id", "target_note_id",
                         name="uq_suggestion_owner_src_tgt"),
    )
