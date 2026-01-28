"""
Celery application configuration for background task processing.

Handles AI image analysis and embedding generation tasks.
"""

from celery import Celery
import os

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Create Celery app
celery_app = Celery(
    "ai_notes_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "tasks",
        "tasks_embeddings",
        "features.search.tasks",
        "features.rag_chat.tasks",
        "features.images.tasks",
        "features.brain.tasks",
        "features.graph.tasks",  # Phase 2: Semantic edges and clustering
        "features.settings.tasks",  # Phase 4: Data export tasks
        "features.mnemosyne_brain.tasks",  # Mnemosyne Brain build & evolution
    ]  # Import tasks modules
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task (for first model loading)
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    result_expires=3600,  # Keep results for 1 hour
)

# Task routing (can be expanded later)
celery_app.conf.task_routes = {
    "tasks.analyze_image_task": {"queue": "ai_analysis"},
    "tasks_embeddings.generate_note_embedding": {"queue": "ai_analysis"},
    "tasks_embeddings.regenerate_all_embeddings": {"queue": "ai_analysis"},
}

if __name__ == "__main__":
    celery_app.start()
