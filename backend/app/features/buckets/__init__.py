"""
Buckets Feature Module.

Provides Smart Buckets functionality:
- AI Clusters (K-means clustering on note embeddings)
- Orphan notes (notes with no wikilinks)
- Inbox (recently created notes)
- Daily notes (get/create daily notes)
"""

from features.buckets.router import router as buckets_router
from features.buckets.service import (
    ClusterService,
    OrphanService,
    InboxService,
    DailyNoteService
)
from features.buckets import schemas

__all__ = [
    "buckets_router",
    "ClusterService",
    "OrphanService",
    "InboxService",
    "DailyNoteService",
    "schemas"
]
