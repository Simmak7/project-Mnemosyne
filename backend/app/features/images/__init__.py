"""
Images feature module.

Provides image upload, AI analysis, and image-note relationship management.

Key components:
- Image upload with validation
- Celery-based async AI analysis
- Image-note relationship management
- AI clustering for organization
"""

from features.images.router import router
from features.images.tasks import analyze_image_task
from features.images.service import ImageService
from features.images import schemas
from features.images.logic.clustering import (
    cluster_notes_by_embeddings,
    ClusterResult,
    get_cluster_statistics,
)

__all__ = [
    # Router
    "router",
    # Service
    "ImageService",
    # Schemas
    "schemas",
    # Tasks
    "analyze_image_task",
    # Clustering
    "cluster_notes_by_embeddings",
    "ClusterResult",
    "get_cluster_statistics",
]
