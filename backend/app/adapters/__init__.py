"""
Model adapters for different vision AI models.
"""
from .qwen_vision_adapter import QwenVisionAdapter
from .llama_vision_adapter import LlamaVisionAdapter

__all__ = [
    "QwenVisionAdapter",
    "LlamaVisionAdapter"
]
