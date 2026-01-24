"""Brain feature - Semantic condensation and LoRA training.

This feature provides:
- Semantic condensation of user notes into training samples
- Memory classification (episodic/semantic/preference)
- LoRA adapter versioning and management
- Background indexing via Celery tasks

Exports:
- router: FastAPI router with /brain/* endpoints
- models: SQLAlchemy models (TrainingSample, BrainAdapter, etc.)
- schemas: Pydantic schemas for API
- tasks: Celery tasks (index_brain_task, train_brain_task)
- services: BrainIndexer, SemanticCondenser, MemoryClassifier
"""

from .router import router
from .models import (
    TrainingSample,
    CondensedFact,
    MemoryType,
    BrainAdapter,
    IndexingRun,
)
from .schemas import (
    BrainStatusResponse,
    AdapterResponse,
    TrainingSampleResponse,
    IndexingRunResponse,
)
from .tasks import index_brain_task, train_brain_task
from .services import BrainIndexer, SemanticCondenser, MemoryClassifier

__all__ = [
    # Router
    "router",
    # Models
    "TrainingSample",
    "CondensedFact",
    "MemoryType",
    "BrainAdapter",
    "IndexingRun",
    # Schemas
    "BrainStatusResponse",
    "AdapterResponse",
    "TrainingSampleResponse",
    "IndexingRunResponse",
    # Tasks
    "index_brain_task",
    "train_brain_task",
    # Services
    "BrainIndexer",
    "SemanticCondenser",
    "MemoryClassifier",
]
