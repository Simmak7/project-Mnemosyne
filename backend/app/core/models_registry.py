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


class ProviderSource(str, Enum):
    """Which provider serves this model."""
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    CUSTOM = "custom"


class ModelInfo(BaseModel):
    """Model metadata and capabilities."""
    id: str                          # Model identifier
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
    provider: ProviderSource = ProviderSource.OLLAMA


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

# ============================================================================
# CLOUD AI MODELS
# ============================================================================

CLOUD_MODELS: Dict[str, ModelInfo] = {
    # Anthropic Claude models
    "claude-sonnet-4-20250514": ModelInfo(
        id="claude-sonnet-4-20250514",
        name="Claude Sonnet 4",
        description="Fast, intelligent model for everyday tasks",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.BALANCED,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BRAIN, ModelUseCase.BOTH],
        context_length=200000,
        features=["200K context", "Strong reasoning", "Cloud AI"],
        recommended_for="Fast cloud RAG and Brain queries",
        provider=ProviderSource.ANTHROPIC,
    ),
    "claude-sonnet-4-5-20250929": ModelInfo(
        id="claude-sonnet-4-5-20250929",
        name="Claude Sonnet 4.5",
        description="Most capable balanced model with hybrid reasoning",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.POWERFUL,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BRAIN, ModelUseCase.BOTH],
        context_length=200000,
        features=["200K context", "Hybrid reasoning", "Extended thinking", "Cloud AI"],
        recommended_for="Best quality cloud responses",
        provider=ProviderSource.ANTHROPIC,
    ),
    "claude-opus-4-0520": ModelInfo(
        id="claude-opus-4-0520",
        name="Claude Opus 4",
        description="Most capable model for complex tasks",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.POWERFUL,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BRAIN, ModelUseCase.BOTH],
        context_length=200000,
        features=["200K context", "Strongest reasoning", "Cloud AI"],
        recommended_for="Most demanding analysis tasks",
        provider=ProviderSource.ANTHROPIC,
    ),
    "claude-haiku-4-5-20251001": ModelInfo(
        id="claude-haiku-4-5-20251001",
        name="Claude Haiku 4.5",
        description="Fastest Claude model, great for quick tasks",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.FAST,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BOTH],
        context_length=200000,
        features=["200K context", "Ultra-fast", "Cost-effective", "Cloud AI"],
        recommended_for="Quick searches and simple Q&A",
        provider=ProviderSource.ANTHROPIC,
    ),

    # OpenAI GPT models
    "gpt-4o": ModelInfo(
        id="gpt-4o",
        name="GPT-4o",
        description="OpenAI's flagship multimodal model",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.POWERFUL,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BRAIN, ModelUseCase.BOTH],
        context_length=128000,
        features=["128K context", "Multimodal", "Cloud AI"],
        recommended_for="Versatile cloud AI for all tasks",
        provider=ProviderSource.OPENAI,
    ),
    "gpt-4o-mini": ModelInfo(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        description="Fast and cost-effective GPT model",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.FAST,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BOTH],
        context_length=128000,
        features=["128K context", "Fast inference", "Cost-effective", "Cloud AI"],
        recommended_for="Quick cloud queries on a budget",
        provider=ProviderSource.OPENAI,
    ),
    "o1": ModelInfo(
        id="o1",
        name="o1",
        description="OpenAI reasoning model with chain-of-thought",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.POWERFUL,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BRAIN, ModelUseCase.BOTH],
        context_length=200000,
        features=["200K context", "Deep reasoning", "Chain-of-thought", "Cloud AI"],
        recommended_for="Complex analysis requiring deep reasoning",
        provider=ProviderSource.OPENAI,
    ),
}


def get_model_info(model_id: str) -> Optional[ModelInfo]:
    """Get model information by ID (local + cloud)."""
    return AVAILABLE_MODELS.get(model_id) or CLOUD_MODELS.get(model_id)


def get_models_for_use_case(use_case: ModelUseCase) -> List[ModelInfo]:
    """Get all models suitable for a specific use case (local + cloud)."""
    all_models = {**AVAILABLE_MODELS, **CLOUD_MODELS}
    return [
        model for model in all_models.values()
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
    """Get all available models (local + cloud)."""
    return list(AVAILABLE_MODELS.values()) + list(CLOUD_MODELS.values())


def get_local_models() -> List[ModelInfo]:
    """Get only local Ollama models."""
    return list(AVAILABLE_MODELS.values())


def get_cloud_models() -> List[ModelInfo]:
    """Get only cloud AI models."""
    return list(CLOUD_MODELS.values())


def get_models_by_category(category: ModelCategory) -> List[ModelInfo]:
    """Get models by category (local + cloud)."""
    all_models = {**AVAILABLE_MODELS, **CLOUD_MODELS}
    return [m for m in all_models.values() if m.category == category]


def get_cloud_models_for_provider(provider: str) -> List[ModelInfo]:
    """Get cloud models for a specific provider."""
    provider_map = {"anthropic": ProviderSource.ANTHROPIC, "openai": ProviderSource.OPENAI}
    source = provider_map.get(provider)
    if not source:
        return []
    return [m for m in CLOUD_MODELS.values() if m.provider == source]


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


def get_all_models_with_status(user_cloud_providers: Set[str] = None) -> List[dict]:
    """
    Get all models with their availability status.

    Args:
        user_cloud_providers: Set of provider names the user has API keys for
                              (e.g., {"anthropic", "openai"})
    """
    available = get_ollama_available_models()
    user_cloud_providers = user_cloud_providers or set()
    result = []

    # Local models
    for model in AVAILABLE_MODELS.values():
        model_dict = model.model_dump()
        is_available = model.id in available or f"{model.id}:latest" in available
        model_dict["is_available"] = is_available
        result.append(model_dict)

    # Cloud models
    for model in CLOUD_MODELS.values():
        model_dict = model.model_dump()
        # Cloud model is available if user has an API key for its provider
        model_dict["is_available"] = model.provider.value in user_cloud_providers
        result.append(model_dict)

    return result
