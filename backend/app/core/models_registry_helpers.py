"""
Models Registry Helpers - Query, filter, and availability functions.

Separated from models_registry.py for file size compliance.
"""

import time
import logging
import requests
from typing import Dict, List, Optional, Set

from core import config
from core.models_registry import (
    AVAILABLE_MODELS, ModelInfo, ModelCategory, ModelUseCase, ProviderSource,
)
from core.cloud_models_registry import CLOUD_MODELS

logger = logging.getLogger(__name__)


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
    return "Randomblock1/nemotron-nano:8b"


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
    global _cached_available_models, _cache_timestamp

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
                if model_name.endswith(":latest"):
                    available.add(model_name[:-7])

        _cached_available_models = available
        _cache_timestamp = time.time()
        logger.debug(f"Ollama has {len(available)} models available")
        return available

    except Exception as e:
        logger.warning(f"Failed to get Ollama models: {e}")
        return set()


def invalidate_ollama_cache():
    """Force refresh of cached Ollama model list on next call."""
    global _cached_available_models, _cache_timestamp
    _cached_available_models = None
    _cache_timestamp = 0


def is_model_available(model_id: str) -> bool:
    """Check if a model is available in Ollama."""
    available = get_ollama_available_models()
    return model_id in available or f"{model_id}:latest" in available


def find_available_fallback(
    model_id: str, use_case: str,
) -> Optional[str]:
    """
    Find an available Ollama model that can serve as a fallback.

    Args:
        model_id: The unavailable model to replace
        use_case: "rag", "brain", or "nexus"

    Returns:
        A fallback model ID, or None if nothing is available
    """
    use_case_map = {
        "rag": ModelUseCase.RAG,
        "brain": ModelUseCase.BRAIN,
        "nexus": ModelUseCase.RAG,
    }
    target = use_case_map.get(use_case, ModelUseCase.RAG)
    available = get_ollama_available_models()

    for cid, cinfo in AVAILABLE_MODELS.items():
        if cid == model_id or cinfo.provider != ProviderSource.OLLAMA:
            continue
        if target not in cinfo.use_cases and ModelUseCase.BOTH not in cinfo.use_cases:
            continue
        if cid in available or f"{cid}:latest" in available:
            return cid
    return None


_EMBED_KEYWORDS = ["embed", "nomic-embed", "bge-", "e5-", "gte-"]
_VISION_KEYWORDS = ["vision", "-vl", "vl:", "llava", "minicpm-v"]


def _is_embedding_model(model_name: str) -> bool:
    """Check if a model is an embedding model (not usable for chat)."""
    lower = model_name.lower()
    return any(kw in lower for kw in _EMBED_KEYWORDS)


def _detect_custom_model_category(model_name: str):
    """Detect if a custom model is vision or text based on name patterns."""
    lower = model_name.lower()
    for kw in _VISION_KEYWORDS:
        if kw in lower:
            return ModelCategory.VISION, [ModelUseCase.VISION]
    return ModelCategory.BALANCED, [ModelUseCase.RAG, ModelUseCase.BOTH]


def get_all_models_with_status(user_cloud_providers: Set[str] = None) -> List[dict]:
    """
    Get all models with their availability status.
    Includes custom Ollama models not in registry.
    """
    available = get_ollama_available_models()
    user_cloud_providers = user_cloud_providers or set()
    result = []
    registry_ids = set()

    for model in AVAILABLE_MODELS.values():
        model_dict = model.model_dump()
        is_avail = model.id in available or f"{model.id}:latest" in available
        model_dict["is_available"] = is_avail
        result.append(model_dict)
        registry_ids.add(model.id)

    for model in CLOUD_MODELS.values():
        model_dict = model.model_dump()
        model_dict["is_available"] = model.provider.value in user_cloud_providers
        result.append(model_dict)

    # Add custom Ollama models not in registry (skip embedding models)
    for model_name in available:
        if model_name in registry_ids or model_name.endswith(":latest"):
            continue
        base = model_name.split(":")[0] if ":" in model_name else model_name
        if any(base == rid.split(":")[0] for rid in registry_ids):
            continue
        if _is_embedding_model(model_name):
            continue
        cat, use_cases = _detect_custom_model_category(model_name)
        result.append({
            "id": model_name,
            "name": model_name,
            "description": "Custom model pulled from Ollama",
            "size_gb": 0,
            "parameters": "",
            "category": cat.value,
            "use_cases": [u.value for u in use_cases],
            "context_length": 4096,
            "features": [],
            "recommended_for": None,
            "is_default_rag": False,
            "is_default_brain": False,
            "provider": ProviderSource.OLLAMA.value,
            "is_available": True,
        })

    return result
