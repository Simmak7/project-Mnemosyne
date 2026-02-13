"""
NexusCitation model - Rich citation tracking with graph metadata.

Extends the basic MessageCitation with origin tracing, community info,
wikilink connections, and deep link URLs.
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, JSON
)
from sqlalchemy.sql import func
from core.database import Base


class NexusCitation(Base):
    __tablename__ = "nexus_citations"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(
        Integer,
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    source_type = Column(String(20), nullable=False)
    source_id = Column(Integer, nullable=False)
    citation_index = Column(Integer, nullable=False)
    relevance_score = Column(Float)
    retrieval_method = Column(String(30))

    # Origin tracing
    origin_type = Column(String(30))  # manual | image_analysis | document_analysis | journal
    artifact_id = Column(Integer)  # Image or document ID that created this note

    # Graph context
    community_name = Column(String(255))
    community_id = Column(Integer)
    tags = Column(JSON, default=list)
    direct_wikilinks = Column(JSON, default=list)
    path_to_other_results = Column(JSON, default=list)

    # Deep link URLs
    note_url = Column(String(500))
    graph_url = Column(String(500))
    artifact_url = Column(String(500))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
