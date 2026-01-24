"""
Clustering Service

Community detection using Louvain/Leiden algorithms.
Assigns community_id to notes for clustered visualization.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
import math
import random

import models
from core.logging_config import get_logger

logger = get_logger(__name__)

# Import networkx and community detection
try:
    import networkx as nx
    from community import community_louvain
    CLUSTERING_AVAILABLE = True
except ImportError:
    CLUSTERING_AVAILABLE = False
    logger.warning("networkx or python-louvain not installed. Clustering disabled.")


@dataclass
class ClusterResult:
    """Result of community detection."""
    node_to_community: Dict[str, int]  # node_id -> community_id
    community_count: int
    modularity: float
    node_count: int


class ClusteringService:
    """
    Community detection for knowledge graph.

    Uses Louvain algorithm to detect communities/clusters of related notes.
    Results are stored in notes.community_id for stable visualization.
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def detect_communities(self, algorithm: str = "louvain") -> ClusterResult:
        """
        Run community detection on user's knowledge graph.

        Args:
            algorithm: 'louvain' or 'leiden' (leiden falls back to louvain)

        Returns:
            ClusterResult with node-to-community mapping
        """
        if not CLUSTERING_AVAILABLE:
            logger.warning("Clustering libraries not available")
            return ClusterResult({}, 0, 0.0, 0)

        logger.info(f"Running {algorithm} community detection for user {self.user_id}")

        # Build networkx graph from database
        graph = self._build_graph()

        if graph.number_of_nodes() == 0:
            logger.info("No nodes to cluster")
            return ClusterResult({}, 0, 0.0, 0)

        # Run Louvain community detection
        partition = community_louvain.best_partition(graph, random_state=42)

        # Calculate modularity
        modularity = community_louvain.modularity(partition, graph)

        community_count = len(set(partition.values()))
        logger.info(f"Detected {community_count} communities (modularity: {modularity:.3f})")

        return ClusterResult(
            node_to_community=partition,
            community_count=community_count,
            modularity=modularity,
            node_count=len(partition)
        )

    def _build_graph(self) -> "nx.Graph":
        """Build networkx graph from database."""
        graph = nx.Graph()

        # Get all notes for user
        notes = self.db.query(models.Note).filter(
            models.Note.owner_id == self.user_id,
            models.Note.is_trashed == False
        ).all()

        # Add note nodes
        for note in notes:
            node_id = f"note-{note.id}"
            graph.add_node(node_id, type="note", title=note.title)

        # Add wikilink edges
        self._add_wikilink_edges(graph, notes)

        # Add tag edges (notes sharing tags are connected)
        self._add_tag_edges(graph)

        return graph

    def _add_wikilink_edges(self, graph: "nx.Graph", notes: List[models.Note]):
        """Add edges for wikilinks between notes."""
        from features.graph import extract_wikilinks

        for note in notes:
            if not note.content:
                continue

            source_id = f"note-{note.id}"
            wikilinks = extract_wikilinks(note.content)

            for wikilink in wikilinks:
                # Find target note by title (case-insensitive)
                target = self.db.query(models.Note).filter(
                    models.Note.owner_id == self.user_id,
                    models.Note.title.ilike(wikilink),
                    models.Note.is_trashed == False
                ).first()

                if target:
                    target_id = f"note-{target.id}"
                    if graph.has_node(target_id):
                        graph.add_edge(source_id, target_id, weight=1.0, type="wikilink")

    def _add_tag_edges(self, graph: "nx.Graph"):
        """Add edges between notes sharing tags."""
        # Get all note-tag relationships for user
        notes = self.db.query(models.Note).filter(
            models.Note.owner_id == self.user_id,
            models.Note.is_trashed == False
        ).all()

        # Build tag -> notes mapping
        tag_to_notes: Dict[int, List[int]] = {}
        for note in notes:
            for tag in note.tags:
                if tag.id not in tag_to_notes:
                    tag_to_notes[tag.id] = []
                tag_to_notes[tag.id].append(note.id)

        # Create edges between notes sharing tags
        for tag_id, note_ids in tag_to_notes.items():
            for i, note_id1 in enumerate(note_ids):
                for note_id2 in note_ids[i+1:]:
                    source_id = f"note-{note_id1}"
                    target_id = f"note-{note_id2}"
                    if graph.has_node(source_id) and graph.has_node(target_id):
                        # Add or update edge (increase weight if already exists)
                        if graph.has_edge(source_id, target_id):
                            graph[source_id][target_id]["weight"] += 0.5
                        else:
                            graph.add_edge(source_id, target_id, weight=0.5, type="tag")

    def save_communities(self, result: ClusterResult) -> int:
        """
        Save community assignments to database.

        Updates notes.community_id for each note.

        Returns:
            Number of notes updated
        """
        updated = 0

        for node_id, community_id in result.node_to_community.items():
            if not node_id.startswith("note-"):
                continue

            note_id = int(node_id.replace("note-", ""))

            note = self.db.query(models.Note).filter(
                models.Note.id == note_id,
                models.Note.owner_id == self.user_id
            ).first()

            if note:
                note.community_id = community_id
                updated += 1

        self.db.commit()
        logger.info(f"Updated community_id for {updated} notes")

        return updated

    def compute_stable_positions(self, result: ClusterResult) -> Dict[str, Tuple[float, float]]:
        """
        Compute stable positions for Map view.

        Uses force-directed layout with community-based initial positions.

        Returns:
            Dict of node_id -> (x, y) positions
        """
        if not CLUSTERING_AVAILABLE:
            return {}

        # Rebuild graph for layout computation
        graph = self._build_graph()

        if graph.number_of_nodes() == 0:
            return {}

        # Initial positions based on community
        pos = {}
        community_centers = self._compute_community_centers(result)

        for node_id in graph.nodes():
            community_id = result.node_to_community.get(node_id, 0)
            center = community_centers.get(community_id, (0.0, 0.0))

            # Add jitter within community
            jitter_x = random.uniform(-0.2, 0.2)
            jitter_y = random.uniform(-0.2, 0.2)
            pos[node_id] = (center[0] + jitter_x, center[1] + jitter_y)

        # Refine with spring layout
        try:
            pos = nx.spring_layout(
                graph,
                pos=pos,
                k=1.0 / math.sqrt(graph.number_of_nodes()),
                iterations=50,
                seed=42
            )
            # Convert numpy arrays to tuples
            pos = {k: (float(v[0]), float(v[1])) for k, v in pos.items()}
        except Exception as e:
            logger.warning(f"Spring layout failed: {e}")

        return pos

    def _compute_community_centers(self, result: ClusterResult) -> Dict[int, Tuple[float, float]]:
        """Compute center positions for each community."""
        centers = {}

        # Arrange communities in a circle
        n_communities = result.community_count or 1
        for i in range(n_communities):
            angle = 2 * math.pi * i / n_communities
            x = math.cos(angle) * 2.0
            y = math.sin(angle) * 2.0
            centers[i] = (x, y)

        return centers

    def save_positions(self, positions: Dict[str, Tuple[float, float]]) -> int:
        """
        Save computed positions to database.

        Returns:
            Number of positions saved
        """
        from features.graph.models import GraphPosition

        saved = 0

        for node_id, (x, y) in positions.items():
            parts = node_id.split("-", 1)
            if len(parts) != 2:
                continue

            node_type, id_str = parts
            try:
                db_node_id = int(id_str)
            except ValueError:
                continue

            # Upsert position
            existing = self.db.query(GraphPosition).filter(
                GraphPosition.owner_id == self.user_id,
                GraphPosition.node_type == node_type,
                GraphPosition.node_id == db_node_id,
                GraphPosition.view_type == "map"
            ).first()

            if existing:
                existing.x = x
                existing.y = y
            else:
                position = GraphPosition(
                    owner_id=self.user_id,
                    node_type=node_type,
                    node_id=db_node_id,
                    x=x,
                    y=y,
                    view_type="map"
                )
                self.db.add(position)

            saved += 1

        self.db.commit()
        logger.info(f"Saved {saved} graph positions")

        return saved
