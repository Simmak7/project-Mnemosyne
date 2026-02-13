"""
NexusNavigationCache model - Pre-built community maps and tag overviews.

Stores compact representations of the user's knowledge graph that
the GraphNavigator can include in a single LLM call.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.sql import func
from core.database import Base


class NexusNavigationCache(Base):
    __tablename__ = "nexus_navigation_cache"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    cache_type = Column(String(30), nullable=False)  # community_map | tag_overview
    content = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("owner_id", "cache_type", name="uq_nav_cache_owner_type"),
    )
