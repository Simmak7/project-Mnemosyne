"""
NEXUS Pipeline - Core retrieval pipeline logic

Extracted from router_query.py for the 250-line file limit.
Handles conversation persistence, citation saving, and multi-mode retrieval.
"""

import logging
from datetime import datetime
from typing import Tuple, List, Dict, Optional

from sqlalchemy.orm import Session

from core.model_service import get_effective_rag_model
from features.rag_chat.models import Conversation, ChatMessage
from features.rag_chat.services.title_generator import generate_conversation_title

from features.nexus.models import NexusCitation
from features.nexus.services.query_router import QueryRoute
from features.nexus.services.vector_search import nexus_vector_search
from features.nexus.services.source_chain import resolve_source_chains
from features.nexus.services.context_builder import (
    build_nexus_context,
    NexusContextConfig,
    NexusAssembledContext,
)
from features.nexus.services.graph_navigator import navigate_graph
from features.nexus.services.result_fusion import fuse_results, FusionConfig
from features.nexus.services.navigation_cache_service import get_navigation_cache
from features.nexus.services.diffusion_ranker import diffusion_rank

logger = logging.getLogger(__name__)


def run_nexus_pipeline(db, query, owner_id, body, route):
    """Execute the core NEXUS retrieval + context pipeline (FAST/STANDARD/DEEP)."""
    # Always run vector search
    vector_results = nexus_vector_search(
        db, query, owner_id,
        max_sources=body.max_sources,
        min_similarity=body.min_similarity,
        include_images=body.include_images,
        include_graph=body.include_graph,
    )

    graph_results = None
    diffusion_scores = None
    strategies = ["vector_search"]

    # STANDARD/DEEP: add graph navigation
    if route.mode in ("STANDARD", "DEEP"):
        community_map, tag_overview = get_navigation_cache(db, owner_id)
        if community_map and tag_overview:
            nav_result = navigate_graph(
                db, query, owner_id, community_map, tag_overview,
                max_results=body.max_sources,
            )
            graph_results = nav_result.results
            strategies.append("graph_navigator")

    # DEEP: add diffusion ranking
    if route.mode == "DEEP":
        from embeddings import generate_embedding
        try:
            q_emb = generate_embedding(query)
        except Exception:
            q_emb = None
        diffusion_scores = diffusion_rank(db, owner_id, q_emb)
        if diffusion_scores:
            strategies.append("diffusion_ranker")

    # Fuse results if we have multiple strategies
    if graph_results or diffusion_scores:
        ranked_results = fuse_results(
            vector_results, graph_results, diffusion_scores,
            intent=route.intent, config=FusionConfig(max_results=body.max_sources),
        )
    else:
        ranked_results = vector_results

    note_ids = [r.result.source_id for r in ranked_results
                if r.result.source_type == "note"]
    source_chains = resolve_source_chains(db, note_ids, owner_id)
    context = build_nexus_context(ranked_results, source_chains, NexusContextConfig())

    return ranked_results, context, strategies


def get_conversation_history(db: Session, conversation_id: int, owner_id: int) -> str:
    """Load recent conversation history for multi-turn context."""
    if not conversation_id:
        return ""
    messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id,
    ).order_by(ChatMessage.created_at.desc()).limit(6).all()

    if not messages:
        return ""

    messages.reverse()
    lines = []
    for msg in messages:
        role = "User" if msg.role == "user" else "Assistant"
        content = msg.content[:300] if len(msg.content) > 300 else msg.content
        lines.append(f"{role}: {content}")

    return "\n".join(lines)


def save_nexus_citations(db: Session, message_id: int, citations):
    """Persist rich citations to the nexus_citations table."""
    for c in citations:
        db.add(NexusCitation(
            message_id=message_id,
            source_type=c.source_type,
            source_id=c.source_id,
            citation_index=c.index,
            relevance_score=c.relevance_score,
            retrieval_method=c.retrieval_method,
            origin_type=c.origin_type,
            artifact_id=c.artifact_id,
            community_name=c.community_name,
            community_id=c.community_id,
            tags=c.tags,
            direct_wikilinks=[w for w in (c.direct_wikilinks or [])],
            path_to_other_results=[p for p in (c.path_to_other_results or [])],
            note_url=c.note_url,
            graph_url=c.graph_url,
            artifact_url=c.artifact_url,
        ))


def persist_conversation(db, body, owner_id, query, answer, citations, confidence):
    """Handle conversation creation/persistence. Returns (message_id, conversation_id)."""
    message_id = None
    conversation_id = body.conversation_id
    conversation = None

    try:
        if body.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == body.conversation_id,
                Conversation.owner_id == owner_id,
            ).first()
            if not conversation:
                conversation_id = None

        if not conversation and body.auto_create_conversation:
            title = generate_conversation_title(query)
            conversation = Conversation(owner_id=owner_id, title=title)
            db.add(conversation)
            db.flush()
            conversation_id = conversation.id

        if conversation:
            user_msg = ChatMessage(
                conversation_id=conversation.id, role="user", content=query
            )
            db.add(user_msg)
            db.flush()

            assistant_msg = ChatMessage(
                conversation_id=conversation.id, role="assistant",
                content=answer,
                confidence_score=confidence["confidence_score"],
            )
            db.add(assistant_msg)
            db.flush()
            message_id = assistant_msg.id

            save_nexus_citations(db, message_id, citations)
            conversation.updated_at = datetime.utcnow()
            db.commit()

    except Exception as e:
        logger.error(f"Failed to save NEXUS conversation: {e}")
        db.rollback()
        conversation_id = body.conversation_id

    return message_id, conversation_id


def type_breakdown(citations) -> dict:
    """Count source types in citations."""
    breakdown = {}
    for c in citations:
        breakdown[c.source_type] = breakdown.get(c.source_type, 0) + 1
    return breakdown
