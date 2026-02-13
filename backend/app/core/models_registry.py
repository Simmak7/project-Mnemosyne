"""
AI Models Registry - Central configuration for all available AI models.

This module provides metadata about available models, their capabilities,
and recommended use cases. Models can be used interchangeably for RAG and Brain.
"""

import logging
import requests
from typing import Dict, List, Optional, Set
from pydantic import BaseModel
from enum import Enum

from core import config

logger = logging.getLogger(__name__)


class ModelCategory(str, Enum):
    """Model capability categories."""
    FAST = "fast"           # Quick responses, lower resource usage
    BALANCED = "balanced"   # Good balance of speed and quality
    POWERFUL = "powerful"   # Best quality, higher resource usage
    VISION = "vision"       # Multimodal with image understanding


class ModelUseCase(str, Enum):
    """Recommended use cases."""
    RAG = "rag"
    BRAIN = "brain"
    BOTH = "both"
    VISION = "vision"


class ModelInfo(BaseModel):
    """Model metadata and capabilities."""
    id: str                          # Ollama model identifier
    name: str                        # Display name
    description: str                 # Short description
    size_gb: float                   # Approximate size in GB
    parameters: str                  # Parameter count (e.g., "8B")
    category: ModelCategory
    use_cases: List[ModelUseCase]
    context_length: int              # Max context tokens
    features: List[str]              # Special features
    recommended_for: Optional[str]   # Recommendation text
    is_default_rag: bool = False
    is_default_brain: bool = False


# ============================================================================
# MODEL REGISTRY
# ============================================================================

AVAILABLE_MODELS: Dict[str, ModelInfo] = {
    # Fast models - good for quick responses
    "llama3.2:3b": ModelInfo(
        id="llama3.2:3b",
        name="Llama 3.2 3B",
        description="Fast and efficient, good for simple queries",
        size_gb=2.0,
        parameters="3B",
        category=ModelCategory.FAST,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BOTH],
        context_length=4096,
        features=["Fast inference", "Low VRAM"],
        recommended_for="Quick searches and simple Q&A",
    ),

    # Balanced models - good quality with reasonable speed
    "qwen3:8b": ModelInfo(
        id="qwen3:8b",
        name="Qwen3 8B",
        description="Excellent reasoning with thinking mode, great for RAG",
        size_gb=5.2,
        parameters="8B",
        category=ModelCategory.BALANCED,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BOTH],
        context_length=32768,
        features=["Thinking mode", "Strong reasoning", "Long context"],
        recommended_for="RAG queries requiring analysis and synthesis",
        is_default_rag=True,
    ),

    # Powerful models - best quality
    "mirage335/NVIDIA-Nemotron-Nano-9B-v2-virtuoso:latest": ModelInfo(
        id="mirage335/NVIDIA-Nemotron-Nano-9B-v2-virtuoso:latest",
        name="Nemotron Nano 9B v2",
        description="NVIDIA's hybrid architecture, excellent for creative tasks",
        size_gb=9.1,
        parameters="9B",
        category=ModelCategory.POWERFUL,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BRAIN, ModelUseCase.BOTH],
        context_length=128000,
        features=["128K context", "Hybrid Mamba-2 architecture", "Creative writing"],
        recommended_for="Best quality responses for NEXUS and Brain",
        is_default_brain=True,
    ),

    # Vision models
    "llama3.2-vision:11b": ModelInfo(
        id="llama3.2-vision:11b",
        name="Llama 3.2 Vision 11B",
        description="Multimodal model for image understanding",
        size_gb=7.8,
        parameters="11B",
        category=ModelCategory.VISION,
        use_cases=[ModelUseCase.VISION],
        context_length=8192,
        features=["Image understanding", "Visual Q&A"],
        recommended_for="Image analysis and visual content",
    ),

    "qwen2.5vl:7b-q4_K_M": ModelInfo(
        id="qwen2.5vl:7b-q4_K_M",
        name="Qwen 2.5 VL 7B",
        description="Vision-language model with good accuracy",
        size_gb=6.0,
        parameters="7B",
        category=ModelCategory.VISION,
        use_cases=[ModelUseCase.VISION],
        context_length=8192,
        features=["Image understanding", "Quantized for efficiency"],
        recommended_for="Image analysis with lower VRAM",
    ),
}


def get_model_info(model_id: str) -> Optional[ModelInfo]:
    """Get model information by ID."""
    return AVAILABLE_MODELS.get(model_id)


def get_models_for_use_case(use_case: ModelUseCase) -> List[ModelInfo]:
    """Get all models suitable for a specific use case."""
    return [
        model for model in AVAILABLE_MODELS.values()
        if use_case in model.use_cases or ModelUseCase.BOTH in model.use_cases
    ]


def get_default_rag_model() -> str:
    """Get the default RAG model ID."""
    for model_id, info in AVAILABLE_MODELS.items():
        if info.is_default_rag:
            return model_id
    return "qwen3:8b"


def get_default_brain_model() -> str:
    """Get the default Brain model ID."""
    for model_id, info in AVAILABLE_MODELS.items():
        if info.is_default_brain:
            return model_id
    return "mirage335/NVIDIA-Nemotron-Nano-9B-v2-virtuoso:latest"


def get_all_models() -> List[ModelInfo]:
    """Get all available models."""
    return list(AVAILABLE_MODELS.values())


def get_models_by_category(category: ModelCategory) -> List[ModelInfo]:
    """Get models by category."""
    return [m for m in AVAILABLE_MODELS.values() if m.category == category]


# ============================================================================
# MODEL AVAILABILITY CHECK
# ============================================================================

_cached_available_models: Optional[Set[str]] = None
_cache_timestamp: float = 0


def get_ollama_available_models() -> Set[str]:
    """
    Get set of model IDs that are actually downloaded in Ollama.
    Results are cached for 60 seconds.
    """
    import time
    global _cached_available_models, _cache_timestamp

    # Use cache if fresh (60 seconds)
    if _cached_available_models is not None and (time.time() - _cache_timestamp) < 60:
        return _cached_available_models

    try:
        ollama_host = getattr(config, "OLLAMA_HOST", "http://ollama:11434")
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()

        available = set()
        for model in data.get("models", []):
            model_name = model.get("name", "")
            if model_name:
                available.add(model_name)
                # Also add without :latest suffix for matching
                if model_name.endswith(":latest"):
                    available.add(model_name[:-7])

        _cached_available_models = available
        _cache_timestamp = time.time()
        logger.debug(f"Ollama has {len(available)} models available")
        return available

    except Exception as e:
        logger.warning(f"Failed to get Ollama models: {e}")
        return set()


def is_model_available(model_id: str) -> bool:
    """Check if a model is available in Ollama."""
    available = get_ollama_available_models()
    # Check exact match or with :latest suffix
    return model_id in available or f"{model_id}:latest" in available


def get_all_models_with_status() -> List[dict]:
    """Get all models with their availability status."""
    available = get_ollama_available_models()
    result = []

    for model in AVAILABLE_MODELS.values():
        model_dict = model.model_dump()
        # Check availability
        is_available = model.id in available or f"{model.id}:latest" in available
        model_dict["is_available"] = is_available
        result.append(model_dict)

    return result
