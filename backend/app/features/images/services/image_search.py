"""
Image Search Operations Service.

Handles text and semantic search for images.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from typing import List
import logging

import models

logger = logging.getLogger(__name__)


class ImageSearchService:
    """Service class for image search operations."""

    @staticmethod
    def search_images_text(db: Session, owner_id: int, query: str, limit: int = 50) -> List[models.Image]:
        """
        Full-text search on images using PostgreSQL tsvector.
        Searches filename, display_name, prompt, and AI analysis result.
        """
        if not query or not query.strip():
            return []

        # Parse query for tsquery (simple AND between words)
        words = query.strip().split()
        tsquery = " & ".join(word.replace("'", "''") for word in words)

        # Use raw SQL for full-text search with ranking
        sql = text("""
            SELECT i.id,
                   ts_rank(i.search_vector, to_tsquery('english', :tsquery)) as score
            FROM images i
            WHERE i.owner_id = :owner_id
              AND i.is_trashed = false
              AND i.search_vector @@ to_tsquery('english', :tsquery)
            ORDER BY score DESC
            LIMIT :limit
        """)

        result = db.execute(sql, {
            "tsquery": tsquery,
            "owner_id": owner_id,
            "limit": limit
        })

        image_ids = [row.id for row in result]

        if not image_ids:
            return []

        images = db.query(models.Image)\
            .options(joinedload(models.Image.tags), joinedload(models.Image.notes))\
            .filter(models.Image.id.in_(image_ids))\
            .all()

        id_to_image = {img.id: img for img in images}
        sorted_images = [id_to_image[id] for id in image_ids if id in id_to_image]

        logger.info(f"Text search found {len(sorted_images)} images for query: {query}")
        return sorted_images

    @staticmethod
    def search_images_smart(
        db: Session,
        owner_id: int,
        query: str,
        limit: int = 50,
        threshold: float = 0.3
    ) -> List[models.Image]:
        """
        Semantic search on images using pgvector embeddings.
        Generates embedding for query and finds similar images.
        Falls back to text search if embeddings are not available.
        """
        if not query or not query.strip():
            return []

        # Check if embedding column exists in images table
        try:
            check_sql = text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'images' AND column_name = 'embedding'
            """)
            result = db.execute(check_sql)
            has_embedding_column = result.fetchone() is not None
        except Exception:
            has_embedding_column = False
            db.rollback()

        if not has_embedding_column:
            logger.info("Image embeddings not available, falling back to text search")
            return ImageSearchService.search_images_text(db, owner_id, query, limit)

        try:
            from features.search.logic.embeddings import generate_embedding

            # Generate embedding for the query
            query_embedding = generate_embedding(query.strip())
            if not query_embedding:
                logger.warning(f"Failed to generate embedding for query: {query}")
                return ImageSearchService.search_images_text(db, owner_id, query, limit)

            # Convert embedding to PostgreSQL array format
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

            # Use raw SQL for vector similarity search
            sql = text("""
                SELECT i.id,
                       1 - (i.embedding <=> :embedding::vector) as similarity
                FROM images i
                WHERE i.owner_id = :owner_id
                  AND i.is_trashed = false
                  AND i.embedding IS NOT NULL
                  AND (1 - (i.embedding <=> :embedding::vector)) >= :threshold
                ORDER BY i.embedding <=> :embedding::vector
                LIMIT :limit
            """)

            result = db.execute(sql, {
                "embedding": embedding_str,
                "owner_id": owner_id,
                "threshold": threshold,
                "limit": limit
            })

            image_ids = [row.id for row in result]

            if not image_ids:
                logger.info(f"Smart search found no images above threshold for query: {query}")
                return ImageSearchService.search_images_text(db, owner_id, query, limit)

            images = db.query(models.Image)\
                .options(joinedload(models.Image.tags), joinedload(models.Image.notes))\
                .filter(models.Image.id.in_(image_ids))\
                .all()

            id_to_image = {img.id: img for img in images}
            sorted_images = [id_to_image[id] for id in image_ids if id in id_to_image]

            logger.info(f"Smart search found {len(sorted_images)} images for query: {query}")
            return sorted_images

        except Exception as e:
            logger.error(f"Smart search failed: {str(e)}", exc_info=True)
            db.rollback()
            return ImageSearchService.search_images_text(db, owner_id, query, limit)
