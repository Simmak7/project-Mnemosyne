"""Celery tasks for brain indexing and training.

Tasks:
- index_brain_task: Process user content into training samples
- train_brain_task: Execute LoRA fine-tuning
- cleanup_old_adapters_task: Remove old adapter versions
"""

import logging
import asyncio
from datetime import datetime

from celery import shared_task

from core.celery_app import celery_app
from core.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=7200,  # 2 hours soft limit
    time_limit=7500,       # 2h 5min hard limit
)
def index_brain_task(self, user_id: int, full_reindex: bool = False):
    """Background task for brain indexing.

    Processes user's notes and images to extract facts and
    generate training samples.

    Args:
        user_id: User ID to index
        full_reindex: If True, reprocess all content

    Returns:
        Dict with indexing statistics
    """
    from .services import BrainIndexer
    from .models import IndexingRun

    logger.info(f"Starting brain indexing for user {user_id} (full={full_reindex})")

    db = SessionLocal()
    try:
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'step': 'Initializing'}
        )

        indexer = BrainIndexer(db, user_id)

        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'step': 'Detecting changes'}
        )

        # Run async indexing in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                indexer.index_changes(full_reindex=full_reindex)
            )
        finally:
            loop.close()

        self.update_state(
            state='PROGRESS',
            meta={'progress': 100, 'step': 'Complete'}
        )

        logger.info(
            f"Brain indexing complete for user {user_id}: "
            f"{result.stats.facts_extracted} facts, "
            f"{result.stats.samples_generated} samples"
        )

        return {
            "status": "completed",
            "run_id": result.run_id,
            "notes_processed": result.stats.notes_processed,
            "images_processed": result.stats.images_processed,
            "facts_extracted": result.stats.facts_extracted,
            "samples_generated": result.stats.samples_generated,
            "processing_time_ms": result.stats.processing_time_ms
        }

    except Exception as e:
        logger.error(f"Brain indexing failed for user {user_id}: {e}")

        # Update run record if exists
        latest_run = (
            db.query(IndexingRun)
            .filter(
                IndexingRun.owner_id == user_id,
                IndexingRun.status == "running"
            )
            .order_by(IndexingRun.started_at.desc())
            .first()
        )
        if latest_run:
            latest_run.status = "failed"
            latest_run.error_message = str(e)
            db.commit()

        raise self.retry(exc=e)
    finally:
        db.close()


@celery_app.task(
    bind=True,
    max_retries=1,
    default_retry_delay=120,
    soft_time_limit=14400,  # 4 hours soft limit (training is slow)
    time_limit=14700,       # 4h 5min hard limit
)
def train_brain_task(self, user_id: int, adapter_id: int):
    """Background task for LoRA training.

    Executes full LoRA fine-tuning using PEFT library.

    Args:
        user_id: User ID to train
        adapter_id: Adapter record ID

    Returns:
        Dict with training statistics
    """
    from .services import LoRATrainer, TrainingConfig
    from .models import BrainAdapter

    logger.info(f"Starting brain training for user {user_id}, adapter {adapter_id}")

    db = SessionLocal()
    try:
        # Progress callback for Celery state updates
        def progress_callback(pct: int, step: str):
            self.update_state(
                state='PROGRESS',
                meta={'progress': pct, 'step': step}
            )

        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'step': 'Initializing'}
        )

        # Get adapter
        adapter = db.query(BrainAdapter).filter(BrainAdapter.id == adapter_id).first()
        if not adapter:
            raise ValueError(f"Adapter {adapter_id} not found")

        # Create trainer
        trainer = LoRATrainer(db, user_id)
        config = TrainingConfig(**adapter.training_config)

        # Run training
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                trainer.train(config, adapter, progress_callback)
            )
        finally:
            loop.close()

        self.update_state(
            state='PROGRESS',
            meta={'progress': 100, 'step': 'Complete'}
        )

        logger.info(
            f"Brain training complete for user {user_id}: "
            f"adapter v{result.version}, {result.samples_trained} samples"
        )

        return {
            "status": result.status,
            "adapter_id": result.adapter_id,
            "version": result.version,
            "samples_trained": result.samples_trained,
            "training_time_seconds": result.training_time_seconds,
            "adapter_path": result.adapter_path,
            "error_message": result.error_message
        }

    except Exception as e:
        logger.error(f"Brain training failed for user {user_id}: {e}")

        # Update adapter status
        adapter = db.query(BrainAdapter).filter(BrainAdapter.id == adapter_id).first()
        if adapter:
            adapter.status = "failed"
            adapter.error_message = str(e)
            db.commit()

        raise
    finally:
        db.close()


@celery_app.task
def cleanup_old_adapters_task(user_id: int, keep_versions: int = 5):
    """Clean up old adapter versions, keeping the most recent N.

    Args:
        user_id: User ID
        keep_versions: Number of versions to keep
    """
    from .models import BrainAdapter
    from .services import AdapterStorage

    db = SessionLocal()
    try:
        # Get all adapters ordered by version
        adapters = (
            db.query(BrainAdapter)
            .filter(BrainAdapter.owner_id == user_id)
            .order_by(BrainAdapter.version.desc())
            .all()
        )

        if len(adapters) <= keep_versions:
            return {"deleted": 0}

        # Delete old adapters (keeping active and recent)
        deleted_db = 0
        storage = AdapterStorage(user_id)

        for adapter in adapters[keep_versions:]:
            if not adapter.is_active:
                # Delete from filesystem
                storage.delete_adapter(adapter.version)

                # Delete from database
                db.delete(adapter)
                deleted_db += 1

        db.commit()
        logger.info(f"Cleaned up {deleted_db} old adapters for user {user_id}")

        return {"deleted": deleted_db}

    finally:
        db.close()


@celery_app.task
def export_training_data_task(user_id: int, format_type: str = "alpaca"):
    """Export training data to JSONL file.

    Args:
        user_id: User ID
        format_type: Format type (alpaca, chatml, raw)

    Returns:
        Dict with export path and statistics
    """
    from pathlib import Path
    from .services import DatasetPreparator

    db = SessionLocal()
    try:
        preparator = DatasetPreparator(db, user_id)

        # Export to temp directory
        output_dir = Path(f"/tmp/brain_export_{user_id}")
        result = preparator.prepare_dataset(
            output_dir,
            pending_only=False,
            format_type=format_type
        )

        logger.info(f"Exported {result['count']} samples for user {user_id}")
        return result

    finally:
        db.close()
