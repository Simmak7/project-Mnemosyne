"""
AI Models Registry - Central configuration for all available AI models.

This module defines enums, ModelInfo class, and local Ollama model definitions.
Cloud models are in cloud_models_registry.py.
Helper functions are in models_registry_helpers.py.

All symbols are re-exported here for backward compatibility.
"""

import logging
from typing import Dict, List, Optional, Set
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)


class ModelCategory(str, Enum):
    """Model capability categories."""
    FAST = "fast"
    BALANCED = "balanced"
    POWERFUL = "powerful"
    VISION = "vision"


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
    id: str
    name: str
    description: str
    size_gb: float
    parameters: str
    category: ModelCategory
    use_cases: List[ModelUseCase]
    context_length: int
    features: List[str]
    recommended_for: Optional[str]
    is_default_rag: bool = False
    is_default_brain: bool = False
    provider: ProviderSource = ProviderSource.OLLAMA


# ============================================================================
# LOCAL OLLAMA MODELS
# ============================================================================

AVAILABLE_MODELS: Dict[str, ModelInfo] = {
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
    "Randomblock1/nemotron-nano:8b": ModelInfo(
        id="Randomblock1/nemotron-nano:8b",
        name="Nemotron Nano 8B",
        description="NVIDIA reasoning model, strong for RAG and tool calling",
        size_gb=4.9,
        parameters="8B",
        category=ModelCategory.POWERFUL,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BRAIN, ModelUseCase.BOTH],
        context_length=16384,
        features=["Reasoning mode", "Tool calling", "RAG optimized"],
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
    "qwen3-vl:8b": ModelInfo(
        id="qwen3-vl:8b",
        name="Qwen3 VL 8B",
        description="Latest Qwen vision model, faster and more accurate",
        size_gb=6.1,
        parameters="8B",
        category=ModelCategory.VISION,
        use_cases=[ModelUseCase.VISION],
        context_length=16384,
        features=["Image understanding", "Fast inference", "Long context"],
        recommended_for="Best speed/quality for image analysis",
    ),
}


# ============================================================================
# RE-EXPORTS for backward compatibility
# ============================================================================
# All helper functions and cloud models are imported from their new homes
# so existing `from core.models_registry import X` still works.

from core.cloud_models_registry import CLOUD_MODELS  # noqa: E402, F401
from core.models_registry_helpers import (  # noqa: E402, F401
    get_model_info,
    get_models_for_use_case,
    get_default_rag_model,
    get_default_brain_model,
    get_all_models,
    get_local_models,
    get_cloud_models,
    get_models_by_category,
    get_cloud_models_for_provider,
    get_ollama_available_models,
    invalidate_ollama_cache,
    is_model_available,
    find_available_fallback,
    get_all_models_with_status,
)
