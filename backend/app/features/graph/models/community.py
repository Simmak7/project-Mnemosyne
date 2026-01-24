"""
Community Metadata Model

Stores metadata about detected communities (clusters) from Louvain/Leiden.
Used for Map view cluster labels and summaries.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func

from core.database import Base


class CommunityMetadata(Base):
    """
    Metadata for a detected community/cluster in the knowledge graph.

    Communities are detected using Louvain or Leiden algorithms.
    This table stores summary information for each cluster.

    Attributes:
        community_id: Cluster ID assigned by algorithm
        label: Auto-generated or user-assigned cluster name
        node_count: Number of nodes in cluster
        top_terms: Comma-separated frequent terms in cluster
        center_x, center_y: Precomputed cluster center for Map view
    """
    __tablename__ = "community_metadata"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Community identification
    community_id = Column(Integer, nullable=False)

    # Descriptive metadata
    label = Column(String(255), nullable=True)  # e.g., "Project Ideas", "Research Notes"
    node_count = Column(Integer, default=0)
    top_terms = Column(Text, nullable=True)  # Comma-separated: "python, api, backend"

    # Precomputed center position for Map view
    center_x = Column(Float, default=0.0)
    center_y = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('owner_id', 'community_id', name='unique_community'),
        Index('ix_community_metadata_owner', 'owner_id'),
        Index('ix_community_metadata_community', 'community_id'),
    )

    def __repr__(self):
        label = self.label or f"Cluster {self.community_id}"
        return f"<CommunityMetadata '{label}' ({self.node_count} nodes)>"

    def to_dict(self) -> dict:
        """Export community data for frontend."""
        return {
            "id": self.community_id,
            "label": self.label or f"Cluster {self.community_id}",
            "node_count": self.node_count,
            "top_terms": self.top_terms.split(",") if self.top_terms else [],
            "center": {"x": self.center_x, "y": self.center_y},
        }
