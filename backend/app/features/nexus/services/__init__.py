"""NEXUS services - Graph-native adaptive retrieval pipeline."""

from .query_router import QueryRoute, route_query
from .vector_search import nexus_vector_search
from .source_chain import resolve_source_chains
from .context_builder import build_nexus_context
from .response_generator import generate_nexus_response, stream_nexus_response
from .prompts import NEXUS_SYSTEM_PROMPT

__all__ = [
    "QueryRoute",
    "route_query",
    "nexus_vector_search",
    "resolve_source_chains",
    "build_nexus_context",
    "generate_nexus_response",
    "stream_nexus_response",
    "NEXUS_SYSTEM_PROMPT",
]
