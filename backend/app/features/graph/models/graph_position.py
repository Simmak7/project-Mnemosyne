"""
Graph Position Model

Stores stable node positions for Map view to prevent layout jitter.
Also tracks user-pinned positions.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func

from core.database import Base


class GraphPosition(Base):
    """
    Stable position for a node in graph visualization.

    Positions are precomputed for Map view and cached to avoid
    re-randomization on each page load. Users can also manually
    pin nodes to specific positions.

    Attributes:
        node_type: 'note', 'tag', 'image', 'cluster'
        node_id: ID of the node
        x, y: Canvas coordinates
        is_pinned: True if user manually pinned this position
        view_type: 'map', 'explore', 'media'
    """
    __tablename__ = "graph_positions"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Node identification
    node_type = Column(String(20), nullable=False)  # 'note', 'tag', 'image', 'cluster'
    node_id = Column(Integer, nullable=False)

    # Position
    x = Column(Float, nullable=False, default=0.0)
    y = Column(Float, nullable=False, default=0.0)

    # User pin status
    is_pinned = Column(Boolean, default=False)

    # View context (positions may differ between views)
    view_type = Column(String(20), default='map')  # 'map', 'explore', 'media'

    # Timestamps
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            'owner_id', 'node_type', 'node_id', 'view_type',
            name='unique_graph_position'
        ),
        Index('ix_graph_positions_owner', 'owner_id'),
        Index('ix_graph_positions_node', 'node_type', 'node_id'),
        Index('ix_graph_positions_view', 'view_type'),
    )

    def __repr__(self):
        pinned = " (pinned)" if self.is_pinned else ""
        return f"<GraphPosition {self.node_type}:{self.node_id} ({self.x:.1f}, {self.y:.1f}){pinned}>"

    @property
    def node_graph_id(self) -> str:
        """Get formatted node ID for graph visualization."""
        return f"{self.node_type}-{self.node_id}"

    def to_dict(self) -> dict:
        """Export position data for frontend."""
        return {
            "node_id": self.node_graph_id,
            "x": self.x,
            "y": self.y,
            "is_pinned": self.is_pinned,
        }
