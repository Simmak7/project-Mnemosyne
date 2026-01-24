"""
Semantic Edges Service

Generates embedding-based similarity edges between notes.
Uses cosine similarity on note embeddings to find semantically related content.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import and_, text

import models
from features.graph.models import SemanticEdge
from core.logging_config import get_logger

logger = get_logger(__name__)

# Import numpy for cosine similarity
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("numpy not installed. Semantic edges disabled.")


@dataclass
class SemanticEdgeResult:
    """Result of semantic edge generation."""
    edges_created: int
    edges_deleted: int
    notes_processed: int
    threshold: float


class SemanticEdgesService:
    """
    Generate semantic similarity edges between notes.

    Uses note embeddings (768-dim vectors from nomic-embed-text) to compute
    pairwise cosine similarity. Creates edges where similarity > threshold.
    """

    DEFAULT_THRESHOLD = 0.7  # Minimum similarity for edge creation
    MAX_EDGES_PER_NOTE = 10  # Limit edges per note to avoid clutter

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def generate_edges(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        max_per_note: int = MAX_EDGES_PER_NOTE
    ) -> SemanticEdgeResult:
        """
        Generate semantic edges for all notes with embeddings.

        Args:
            threshold: Minimum cosine similarity (0.0 - 1.0)
            max_per_note: Maximum edges to create per note

        Returns:
            SemanticEdgeResult with statistics
        """
        if not NUMPY_AVAILABLE:
            logger.warning("numpy not available for semantic edge generation")
            return SemanticEdgeResult(0, 0, 0, threshold)

        logger.info(f"Generating semantic edges for user {self.user_id} (threshold={threshold})")

        # Get notes with embeddings
        notes = self._get_notes_with_embeddings()

        if len(notes) < 2:
            logger.info("Not enough notes with embeddings for semantic edges")
            return SemanticEdgeResult(0, 0, len(notes), threshold)

        # Delete existing semantic edges for user
        deleted = self._delete_existing_edges()

        # Compute similarity matrix
        similarity_pairs = self._compute_similarities(notes, threshold)

        # Create edges for top similarities
        created = self._create_edges(similarity_pairs, max_per_note)

        self.db.commit()

        logger.info(f"Created {created} semantic edges, deleted {deleted}")
        return SemanticEdgeResult(
            edges_created=created,
            edges_deleted=deleted,
            notes_processed=len(notes),
            threshold=threshold
        )

    def _get_notes_with_embeddings(self) -> List[Tuple[int, str, np.ndarray]]:
        """Get all notes with valid embeddings."""
        notes = self.db.query(models.Note).filter(
            models.Note.owner_id == self.user_id,
            models.Note.is_trashed == False,
            models.Note.embedding.isnot(None)
        ).all()

        result = []
        for note in notes:
            if note.embedding is not None:
                # Convert from pgvector to numpy array
                try:
                    embedding = np.array(note.embedding)
                    if embedding.shape == (768,):
                        result.append((note.id, note.title, embedding))
                except Exception as e:
                    logger.warning(f"Failed to process embedding for note {note.id}: {e}")

        logger.info(f"Found {len(result)} notes with valid embeddings")
        return result

    def _compute_similarities(
        self,
        notes: List[Tuple[int, str, np.ndarray]],
        threshold: float
    ) -> List[Tuple[int, int, float]]:
        """
        Compute pairwise cosine similarities above threshold.

        Returns list of (note1_id, note2_id, similarity) tuples.
        """
        pairs = []

        # Stack embeddings into matrix for efficient computation
        embeddings = np.array([n[2] for n in notes])

        # Normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / (norms + 1e-8)

        # Compute similarity matrix
        similarity_matrix = np.dot(normalized, normalized.T)

        # Extract pairs above threshold
        for i in range(len(notes)):
            for j in range(i + 1, len(notes)):
                sim = similarity_matrix[i, j]
                if sim >= threshold:
                    pairs.append((notes[i][0], notes[j][0], float(sim)))

        # Sort by similarity descending
        pairs.sort(key=lambda x: x[2], reverse=True)

        logger.info(f"Found {len(pairs)} similarity pairs above threshold {threshold}")
        return pairs

    def _delete_existing_edges(self) -> int:
        """Delete all existing semantic edges for user."""
        deleted = self.db.query(SemanticEdge).filter(
            SemanticEdge.owner_id == self.user_id
        ).delete()

        return deleted

    def _create_edges(
        self,
        pairs: List[Tuple[int, int, float]],
        max_per_note: int
    ) -> int:
        """
        Create semantic edge records in database.

        Limits edges per note to avoid cluttering the graph.
        """
        # Track edges per note
        edges_per_note: dict = {}
        created = 0

        for note1_id, note2_id, similarity in pairs:
            # Check limits
            count1 = edges_per_note.get(note1_id, 0)
            count2 = edges_per_note.get(note2_id, 0)

            if count1 >= max_per_note or count2 >= max_per_note:
                continue

            # Create edge
            edge = SemanticEdge(
                owner_id=self.user_id,
                source_type="note",
                source_id=note1_id,
                target_type="note",
                target_id=note2_id,
                similarity_score=similarity
            )
            self.db.add(edge)

            edges_per_note[note1_id] = count1 + 1
            edges_per_note[note2_id] = count2 + 1
            created += 1

        return created

    def get_semantic_neighbors(
        self,
        note_id: int,
        limit: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Get semantically similar notes for a given note.

        Returns:
            List of (note_id, similarity_score) tuples
        """
        edges = self.db.query(SemanticEdge).filter(
            SemanticEdge.owner_id == self.user_id,
            (
                (SemanticEdge.source_type == "note") &
                (SemanticEdge.source_id == note_id)
            ) |
            (
                (SemanticEdge.target_type == "note") &
                (SemanticEdge.target_id == note_id)
            )
        ).order_by(SemanticEdge.similarity_score.desc()).limit(limit).all()

        result = []
        for edge in edges:
            if edge.source_id == note_id:
                result.append((edge.target_id, edge.similarity_score))
            else:
                result.append((edge.source_id, edge.similarity_score))

        return result

    def get_all_edges(self) -> List[SemanticEdge]:
        """Get all semantic edges for user."""
        return self.db.query(SemanticEdge).filter(
            SemanticEdge.owner_id == self.user_id
        ).all()

    def get_edge_count(self) -> int:
        """Get count of semantic edges for user."""
        return self.db.query(SemanticEdge).filter(
            SemanticEdge.owner_id == self.user_id
        ).count()
