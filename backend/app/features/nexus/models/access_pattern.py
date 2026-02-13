"""
NexusAccessPattern model - Co-retrieval tracking between notes.

Records when two notes are retrieved together in the same query,
enabling discovery of implicit relationships.
"""

from sqlalchemy import (
    Column, Integer, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.sql import func
from core.database import Base


class NexusAccessPattern(Base):
    __tablename__ = "nexus_access_patterns"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    note_id_a = Column(Integer, nullable=False)
    note_id_b = Column(Integer, nullable=False)
    co_retrieval_count = Column(Integer, default=1)
    last_co_retrieved_at = Column(DateTime(timezone=True),
                                  server_default=func.now())

    __table_args__ = (
        UniqueConstraint("owner_id", "note_id_a", "note_id_b",
                         name="uq_access_owner_a_b"),
    )
