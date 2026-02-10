"""
Typed Graph Builder Service

Builds typed graph data from database models.
Converts notes, tags, images, and their relationships into TypedNode/TypedEdge format.
"""

from typing import List, Dict, Optional, Set
from collections import deque
from sqlalchemy.orm import Session
from sqlalchemy import or_

import models
from features.graph.wikilink_parser import extract_wikilinks, parse_wikilink, create_slug
from .graph_index import TypedNode, TypedEdge, TypedGraphData
from .graph_factories import (
    note_to_typed_node,
    tag_to_typed_node,
    image_to_typed_node,
    document_to_typed_node,
    create_wikilink_edge,
    create_tag_edge,
    create_image_edge,
    create_source_edge,
    create_semantic_edge,
)


class TypedGraphBuilder:
    """
    Builds typed graph data from database models.

    Converts:
    - Notes -> TypedNode(type='note')
    - Tags -> TypedNode(type='tag')
    - Images -> TypedNode(type='image')
    - Wikilinks -> TypedEdge(type='wikilink')
    - Note-Tag relations -> TypedEdge(type='tag')
    - Note-Image relations -> TypedEdge(type='image')
    - Semantic similarities -> TypedEdge(type='semantic')

    Usage:
        builder = TypedGraphBuilder(db, user_id)
        graph = builder.build_full_graph()
        graph = builder.build_local_graph("note-123", depth=2)
    """

    def __init__(self, db: Session, user_id: int):
        """Initialize builder for a user."""
        self.db = db
        self.user_id = user_id
        self._wikilink_cache: Dict[int, List[int]] = {}

    def build_full_graph(
        self,
        include_semantic: bool = False,
        min_semantic_weight: float = 0.5
    ) -> TypedGraphData:
        """
        Build complete typed graph for user.

        Args:
            include_semantic: Include embedding-based edges
            min_semantic_weight: Minimum similarity for semantic edges

        Returns:
            TypedGraphData with all nodes and edges
        """
        nodes: List[TypedNode] = []
        edges: List[TypedEdge] = []

        # Load all data
        notes = self.db.query(models.Note).filter(
            models.Note.owner_id == self.user_id,
            models.Note.is_trashed == False
        ).all()

        tags = self.db.query(models.Tag).filter(
            models.Tag.owner_id == self.user_id
        ).all()

        images = self.db.query(models.Image).filter(
            models.Image.owner_id == self.user_id,
            models.Image.is_trashed == False
        ).all()

        # Build node lookup sets
        note_ids = {note.id for note in notes}
        tag_ids = {tag.id for tag in tags}
        image_ids = {image.id for image in images}

        # Count tags for each note
        tag_note_counts: Dict[int, int] = {}
        for note in notes:
            for tag in note.tags:
                tag_note_counts[tag.id] = tag_note_counts.get(tag.id, 0) + 1

        # Create note nodes and edges
        for note in notes:
            nodes.append(note_to_typed_node(note))

            # Wikilink edges
            linked_ids = self._resolve_wikilinks(note)
            for target_id in linked_ids:
                if target_id in note_ids and target_id != note.id:
                    edges.append(create_wikilink_edge(note.id, target_id))

            # Tag edges
            for tag in note.tags:
                if tag.id in tag_ids:
                    edges.append(create_tag_edge(note.id, tag.id))

            # Image edges
            for image in note.images:
                if image.id in image_ids:
                    edges.append(create_image_edge(note.id, image.id))

        # Create tag nodes
        for tag in tags:
            nodes.append(tag_to_typed_node(tag, tag_note_counts.get(tag.id, 0)))

        # Create image nodes
        for image in images:
            nodes.append(image_to_typed_node(image))

        # Add reverse image edges (image → note) for bidirectional visualization
        for image in images:
            for note in image.notes:
                if note.id in note_ids and note.owner_id == self.user_id:
                    edges.append(create_image_edge(note.id, image.id, reverse=True))

        # Load completed documents with summary notes
        documents = self.db.query(models.Document).filter(
            models.Document.owner_id == self.user_id,
            models.Document.is_trashed == False,
            models.Document.ai_analysis_status == "completed",
            models.Document.summary_note_id.isnot(None),
        ).all()

        for doc in documents:
            nodes.append(document_to_typed_node(doc))
            if doc.summary_note_id in note_ids:
                edges.append(create_source_edge(doc.id, doc.summary_note_id))

        # Add semantic edges if requested
        if include_semantic:
            semantic_edges = self._get_semantic_edges(min_semantic_weight)
            edges.extend(semantic_edges)

        return TypedGraphData(
            nodes=nodes,
            edges=edges,
            metadata={
                "include_semantic": include_semantic,
                "min_semantic_weight": min_semantic_weight,
                "node_count": len(nodes),
                "edge_count": len(edges),
            }
        )

    def build_local_graph(
        self,
        center_node_id: str,
        depth: int = 2,
        layers: Optional[List[str]] = None,
        min_weight: float = 0.0
    ) -> TypedGraphData:
        """
        Build local neighborhood graph around a center node using BFS.

        Args:
            center_node_id: Node ID to center on (e.g., 'note-123')
            depth: How many hops to include (1-3)
            layers: Which node types to include

        Returns:
            TypedGraphData with neighborhood nodes and edges
        """
        if layers is None:
            layers = ["notes", "tags", "documents"]

        # Parse center node ID
        node_type, node_db_id = self._parse_node_id(center_node_id)
        if node_type is None or node_db_id is None:
            return TypedGraphData(
                nodes=[],
                edges=[],
                metadata={"error": f"Invalid node ID: {center_node_id}"}
            )

        # BFS traversal
        visited_nodes: Set[str] = set()
        nodes: List[TypedNode] = []
        edges: List[TypedEdge] = []

        # Queue: (node_id, current_depth)
        queue: deque = deque([(center_node_id, 0)])

        while queue:
            current_id, current_depth = queue.popleft()

            if current_id in visited_nodes:
                continue
            if current_depth > depth:
                continue

            visited_nodes.add(current_id)

            # Get node and its neighbors
            node = self._get_node_by_id(current_id)
            if node is None:
                continue

            # Check if layer is included
            if not self._is_layer_included(node.type.value, layers):
                continue

            nodes.append(node)

            # Get neighbors and add edges
            if current_depth < depth:
                neighbors = self._get_neighbors(current_id, layers, min_weight)
                for neighbor_id, edge in neighbors:
                    if neighbor_id not in visited_nodes:
                        queue.append((neighbor_id, current_depth + 1))
                    # Add edge if both nodes will be in result
                    if edge.weight >= min_weight:
                        edges.append(edge)

        # Deduplicate edges
        seen_edges: Set[tuple] = set()
        unique_edges: List[TypedEdge] = []
        for edge in edges:
            edge_key = (edge.source, edge.target, edge.type.value)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                unique_edges.append(edge)

        return TypedGraphData(
            nodes=nodes,
            edges=unique_edges,
            metadata={
                "center": center_node_id,
                "depth": depth,
                "layers": layers,
                "min_weight": min_weight,
                "node_count": len(nodes),
                "edge_count": len(unique_edges),
            }
        )

    def _parse_node_id(self, node_id: str) -> tuple:
        """Parse node ID into (type, db_id)."""
        parts = node_id.split("-", 1)
        if len(parts) != 2:
            return None, None
        try:
            return parts[0], int(parts[1])
        except ValueError:
            return None, None

    def _get_node_by_id(self, node_id: str) -> Optional[TypedNode]:
        """Get a TypedNode by its ID string."""
        node_type, db_id = self._parse_node_id(node_id)
        if node_type is None:
            return None

        if node_type == "note":
            note = self.db.query(models.Note).filter(
                models.Note.id == db_id,
                models.Note.owner_id == self.user_id
            ).first()
            return note_to_typed_node(note) if note else None

        elif node_type == "tag":
            tag = self.db.query(models.Tag).filter(
                models.Tag.id == db_id,
                models.Tag.owner_id == self.user_id
            ).first()
            if tag:
                note_count = self.db.query(models.Note).join(
                    models.Note.tags
                ).filter(
                    models.Tag.id == db_id,
                    models.Note.owner_id == self.user_id
                ).count()
                return tag_to_typed_node(tag, note_count)
            return None

        elif node_type == "image":
            image = self.db.query(models.Image).filter(
                models.Image.id == db_id,
                models.Image.owner_id == self.user_id
            ).first()
            return image_to_typed_node(image) if image else None

        elif node_type == "document":
            doc = self.db.query(models.Document).filter(
                models.Document.id == db_id,
                models.Document.owner_id == self.user_id
            ).first()
            return document_to_typed_node(doc) if doc else None

        return None

    def _get_neighbors(
        self,
        node_id: str,
        layers: List[str],
        min_weight: float
    ) -> List[tuple]:
        """Get neighbors of a node with their connecting edges."""
        neighbors: List[tuple] = []
        node_type, db_id = self._parse_node_id(node_id)

        if node_type == "note":
            note = self.db.query(models.Note).filter(
                models.Note.id == db_id,
                models.Note.owner_id == self.user_id
            ).first()
            if not note:
                return neighbors

            # Wikilink targets (outgoing)
            if "notes" in layers:
                linked_ids = self._resolve_wikilinks(note)
                for target_id in linked_ids:
                    edge = create_wikilink_edge(note.id, target_id)
                    neighbors.append((f"note-{target_id}", edge))

                # Backlinks (incoming)
                backlink_ids = self._get_backlinks(note)
                for source_id in backlink_ids:
                    edge = create_wikilink_edge(source_id, note.id)
                    neighbors.append((f"note-{source_id}", edge))

            # Tags
            if "tags" in layers:
                for tag in note.tags:
                    edge = create_tag_edge(note.id, tag.id)
                    neighbors.append((f"tag-{tag.id}", edge))

            # Images
            if "images" in layers:
                for image in note.images:
                    edge = create_image_edge(note.id, image.id)
                    neighbors.append((f"image-{image.id}", edge))

            # Source documents (reverse lookup: documents that created this note)
            if "documents" in layers:
                source_docs = self.db.query(models.Document).filter(
                    models.Document.summary_note_id == db_id,
                    models.Document.owner_id == self.user_id,
                    models.Document.is_trashed == False,
                ).all()
                for doc in source_docs:
                    edge = create_source_edge(doc.id, note.id)
                    neighbors.append((f"document-{doc.id}", edge))

        elif node_type == "tag":
            # Notes with this tag
            if "notes" in layers:
                notes = self.db.query(models.Note).join(
                    models.Note.tags
                ).filter(
                    models.Tag.id == db_id,
                    models.Note.owner_id == self.user_id
                ).all()
                for note in notes:
                    edge = create_tag_edge(note.id, db_id)
                    neighbors.append((f"note-{note.id}", edge))

        elif node_type == "image":
            # Notes referencing this image
            if "notes" in layers:
                notes = self.db.query(models.Note).join(
                    models.Note.images
                ).filter(
                    models.Image.id == db_id,
                    models.Note.owner_id == self.user_id
                ).all()
                for note in notes:
                    # Use reverse=True to create image→note edge (bidirectional)
                    edge = create_image_edge(note.id, db_id, reverse=True)
                    neighbors.append((f"note-{note.id}", edge))

        elif node_type == "document":
            # Summary note linked to this document
            if "notes" in layers:
                doc = self.db.query(models.Document).filter(
                    models.Document.id == db_id,
                    models.Document.owner_id == self.user_id
                ).first()
                if doc and doc.summary_note_id:
                    edge = create_source_edge(db_id, doc.summary_note_id)
                    neighbors.append((f"note-{doc.summary_note_id}", edge))

        # Semantic neighbors (for any node type)
        if "semantic" in layers:
            semantic_neighbors = self._get_semantic_neighbors(node_id, min_weight)
            neighbors.extend(semantic_neighbors)

        return neighbors

    def _get_semantic_neighbors(
        self,
        node_id: str,
        min_weight: float
    ) -> List[tuple]:
        """Get semantically similar nodes from the semantic_edges table."""
        neighbors: List[tuple] = []

        try:
            from features.graph.models import SemanticEdge

            node_type, db_id = self._parse_node_id(node_id)
            if not node_type or not db_id:
                return neighbors

            # Find edges where this node is source or target
            edges = self.db.query(SemanticEdge).filter(
                SemanticEdge.owner_id == self.user_id,
                SemanticEdge.similarity_score >= min_weight,
                or_(
                    (SemanticEdge.source_type == node_type) &
                    (SemanticEdge.source_id == db_id),
                    (SemanticEdge.target_type == node_type) &
                    (SemanticEdge.target_id == db_id)
                )
            ).all()

            for edge in edges:
                if edge.source_type == node_type and edge.source_id == db_id:
                    # This node is source, neighbor is target
                    neighbor_id = f"{edge.target_type}-{edge.target_id}"
                else:
                    # This node is target, neighbor is source
                    neighbor_id = f"{edge.source_type}-{edge.source_id}"

                typed_edge = create_semantic_edge(
                    edge.source_type,
                    edge.source_id,
                    edge.target_type,
                    edge.target_id,
                    edge.similarity_score
                )
                neighbors.append((neighbor_id, typed_edge))

        except Exception:
            pass

        return neighbors

    def _resolve_wikilinks(self, note: models.Note) -> List[int]:
        """Resolve wikilinks in note content to note IDs."""
        if note.id in self._wikilink_cache:
            return self._wikilink_cache[note.id]

        if not note.content:
            return []

        wikilinks = extract_wikilinks(note.content)
        linked_ids: Set[int] = set()

        for wikilink in wikilinks:
            target, _ = parse_wikilink(wikilink)
            if not target:
                continue

            target_slug = create_slug(target)
            linked_note = self.db.query(models.Note).filter(
                models.Note.owner_id == self.user_id,
                or_(
                    models.Note.slug == target_slug,
                    models.Note.title.ilike(target)
                )
            ).first()

            if linked_note and linked_note.id != note.id:
                linked_ids.add(linked_note.id)

        result = list(linked_ids)
        self._wikilink_cache[note.id] = result
        return result

    def _get_backlinks(self, note: models.Note) -> List[int]:
        """Find notes that link TO this note."""
        if not note.title:
            return []

        search_patterns = [f"[[{note.title}]]"]
        if note.slug:
            search_patterns.append(f"[[{note.slug}]]")

        backlink_ids: Set[int] = set()

        for pattern in search_patterns:
            notes = self.db.query(models.Note).filter(
                models.Note.owner_id == self.user_id,
                models.Note.id != note.id,
                models.Note.content.contains(pattern)
            ).all()
            for n in notes:
                backlink_ids.add(n.id)

        return list(backlink_ids)

    def _get_semantic_edges(self, min_weight: float) -> List[TypedEdge]:
        """Get semantic edges from the semantic_edges table."""
        try:
            from features.graph.models import SemanticEdge

            edges = self.db.query(SemanticEdge).filter(
                SemanticEdge.owner_id == self.user_id,
                SemanticEdge.similarity_score >= min_weight
            ).all()

            return [
                create_semantic_edge(
                    edge.source_type,
                    edge.source_id,
                    edge.target_type,
                    edge.target_id,
                    edge.similarity_score
                )
                for edge in edges
            ]
        except Exception:
            return []

    def _is_layer_included(self, node_type: str, layers: List[str]) -> bool:
        """Check if a node type is included in the layers filter."""
        layer_map = {
            "note": "notes",
            "tag": "tags",
            "image": "images",
            "document": "documents",
            "collection": "collections",
        }
        layer_name = layer_map.get(node_type, node_type + "s")
        return layer_name in layers
