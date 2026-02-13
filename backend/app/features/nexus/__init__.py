"""
NEXUS Feature - Graph-Native Adaptive Retrieval.

Provides intelligent 3-stage query pipeline:
  Stage 1: Heuristic routing (FAST/STANDARD/DEEP)
  Stage 2: Multi-strategy retrieval + graph navigation
  Stage 3: Graph-aware generation with rich citations
"""

from features.nexus.router import router
from features.nexus import models
from features.nexus import schemas

__all__ = ["router", "models", "schemas"]
