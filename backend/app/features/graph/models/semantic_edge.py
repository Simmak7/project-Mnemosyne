"""
Semantic Edge Model

Stores embedding-based similarity edges between nodes.
These are auto-generated weak links based on vector similarity.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func

from core.database import Base


class SemanticEdge(Base):
    """
    Semantic similarity edge between two nodes.

    Edge is created when embedding cosine similarity exceeds threshold (e.g., 0.7).
    Source and target can be notes, images, or other content types.

    Attributes:
        source_type: 'note', 'image', 'chunk'
        target_type: 'note', 'image', 'chunk'
        similarity_score: Cosine similarity (0.0 - 1.0)
    """
    __tablename__ = "semantic_edges"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Source node
    source_type = Column(String(20), nullable=False)  # 'note', 'image', 'chunk'
    source_id = Column(Integer, nullable=False)

    # Target node
    target_type = Column(String(20), nullable=False)
    target_id = Column(Integer, nullable=False)

    # Edge weight (similarity score)
    similarity_score = Column(Float, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            'owner_id', 'source_type', 'source_id', 'target_type', 'target_id',
            name='unique_semantic_edge'
        ),
        Index('ix_semantic_edges_owner', 'owner_id'),
        Index('ix_semantic_edges_source', 'source_type', 'source_id'),
        Index('ix_semantic_edges_target', 'target_type', 'target_id'),
        Index('ix_semantic_edges_score', 'similarity_score'),
    )

    def __repr__(self):
        return f"<SemanticEdge {self.source_type}:{self.source_id} -> {self.target_type}:{self.target_id} ({self.similarity_score:.2f})>"

    @property
    def source_node_id(self) -> str:
        """Get formatted source node ID for graph visualization."""
        return f"{self.source_type}-{self.source_id}"

    @property
    def target_node_id(self) -> str:
        """Get formatted target node ID for graph visualization."""
        return f"{self.target_type}-{self.target_id}"
