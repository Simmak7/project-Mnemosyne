"""
RAG Query execution service.

Handles the retrieval, ranking, and context building for RAG queries.
Uses ThreadPoolExecutor for parallel retrieval from multiple sources.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable

from sqlalchemy.orm import Session

from models import Note, Image
from embeddings import generate_embedding

from features.rag_chat.services import (
    RetrievalConfig,
    semantic_search_notes,
    semantic_search_chunks,
    fulltext_search_notes,
    combined_image_retrieval,
    GraphTraversalConfig,
    graph_traversal,
    RankingConfig,
    merge_and_rank,
    get_retrieval_summary,
    ContextConfig,
    build_context,
    detect_intent,
    should_skip_rag_search,
    should_include_conversation_context,
)
from features.rag_chat.services.cache import (
    get_cached_retrieval_results,
    cache_retrieval_results,
)
from features.nexus.services.vector_search import _title_search


@dataclass
class QueryExecutionConfig:
    """Configuration for query execution."""
    min_similarity: float = 0.3
    max_sources: int = 10
    include_images: bool = True
    include_graph: bool = True
    max_context_tokens: int = 4000
    max_content_per_source: int = 800


@dataclass
class QueryExecutionResult:
    """Result of query execution."""
    assembled_context: Any
    ranked_results: List[Any]
    retrieval_summary: Dict[str, Any]
    intent_result: Any
    skip_rag: bool
    conversation_context: str


def load_conversation_history(
    db: Session,
    conversation_id: int,
    user_id: int,
    limit: int = 10
) -> tuple[List[Dict], List[Dict]]:
    """
    Load conversation history and previous citations.

    Returns:
        Tuple of (conversation_history, previous_citations)
    """
    from features.rag_chat.models import Conversation, ChatMessage, MessageCitation

    conversation_history = []
    previous_citations = []

    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.owner_id == user_id
    ).first()

    if conv:
        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conv.id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

        conversation_history = [
            {"role": m.role, "content": m.content}
            for m in reversed(messages)
        ]

        last_assistant = next((m for m in messages if m.role == "assistant"), None)
        if last_assistant:
            prev_cites = db.query(MessageCitation).filter(
                MessageCitation.message_id == last_assistant.id
            ).all()
            previous_citations = [
                {"index": c.citation_index, "source_type": c.source_type, "source_id": c.source_id}
                for c in prev_cites
            ]

    return conversation_history, previous_citations


def execute_retrieval(
    db: Session,
    query: str,
    query_embedding: List[float],
    user_id: int,
    config: QueryExecutionConfig,
    skip_rag: bool = False
) -> tuple[List, List, List, List, List, List]:
    """
    Execute multi-source retrieval in parallel using ThreadPoolExecutor.

    Runs semantic, chunk, fulltext, and title searches concurrently.
    Image and graph searches depend on semantic results, so run sequentially after.

    Returns:
        Tuple of (semantic, chunk, fulltext, image, graph, title) results
    """
    if skip_rag:
        return [], [], [], [], [], []

    retrieval_config = RetrievalConfig(
        min_similarity=config.min_similarity,
        max_results=config.max_sources,
        include_notes=True,
        include_chunks=True,
        include_images=config.include_images
    )

    logger = logging.getLogger(__name__)

    # Run primary searches in parallel (including title search)
    semantic_results = []
    chunk_results = []
    fulltext_results = []
    title_results = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(semantic_search_notes, db, query_embedding, user_id, retrieval_config): 'semantic',
            executor.submit(semantic_search_chunks, db, query_embedding, user_id, retrieval_config): 'chunk',
            executor.submit(fulltext_search_notes, db, query, user_id, 10): 'fulltext',
            executor.submit(_title_search, db, query, user_id): 'title',
        }

        for future in as_completed(futures):
            search_type = futures[future]
            try:
                result = future.result()
                if search_type == 'semantic':
                    semantic_results = result
                elif search_type == 'chunk':
                    chunk_results = result
                elif search_type == 'fulltext':
                    fulltext_results = result
                elif search_type == 'title':
                    title_results = result
            except Exception as e:
                logger.warning(f"Parallel {search_type} search failed: {e}")

    # Image and graph searches depend on semantic results, run sequentially
    image_results = []
    graph_results = []

    if config.include_images and semantic_results:
        try:
            semantic_note_ids = [r.source_id for r in semantic_results if r.source_type == 'note']
            image_results = combined_image_retrieval(db, query, user_id, semantic_note_ids, limit=5)
        except Exception as e:
            logger.warning(f"Image retrieval failed: {e}")

    if config.include_graph and semantic_results:
        try:
            seed_ids = [r.source_id for r in semantic_results[:3] if r.source_type == 'note']
            if seed_ids:
                graph_config = GraphTraversalConfig(max_hops=2, max_results_per_hop=3, relevance_decay=0.5)
                graph_results = graph_traversal(db, seed_ids, user_id, graph_config)
        except Exception as e:
            logger.warning(f"Graph traversal failed: {e}")

    return semantic_results, chunk_results, fulltext_results, image_results, graph_results, title_results


def build_context_from_previous_citations(
    db: Session,
    previous_citations: List[Dict]
) -> Any:
    """Build context from previous conversation citations."""
    prev_context_parts = []

    for i, cite in enumerate(previous_citations, 1):
        if cite["source_type"] == "note":
            note = db.query(Note).filter(Note.id == cite["source_id"]).first()
            if note:
                prev_context_parts.append(f"[{i}] {note.title}:\n{note.content[:800]}")
        elif cite["source_type"] == "image":
            img = db.query(Image).filter(Image.id == cite["source_id"]).first()
            if img and img.ai_analysis_result:
                prev_context_parts.append(f"[{i}] Image: {img.original_filename}:\n{img.ai_analysis_result[:800]}")

    return type('Context', (), {
        'sources': previous_citations,
        'formatted_context': "\n\n".join(prev_context_parts),
        'total_tokens_approx': sum(len(p) // 4 for p in prev_context_parts),
        'truncated': False
    })()


def format_conversation_context(
    conversation_history: List[Dict],
    max_messages: int = 6
) -> str:
    """Format conversation history for context."""
    if not conversation_history:
        return ""

    conv_parts = [
        f"{m['role'].upper()}: {m['content'][:300]}"
        for m in conversation_history[-max_messages:]
    ]
    return "PREVIOUS CONVERSATION:\n" + "\n".join(conv_parts) + "\n\n"


def execute_query(
    db: Session,
    query: str,
    user_id: int,
    config: QueryExecutionConfig,
    conversation_id: Optional[int] = None
) -> QueryExecutionResult:
    """
    Execute the full RAG query pipeline.

    This handles:
    1. Loading conversation history
    2. Intent detection
    3. Multi-source retrieval
    4. Ranking and context building
    """
    logger = logging.getLogger(__name__)

    # Load conversation history
    conversation_history = []
    previous_citations = []
    if conversation_id:
        conversation_history, previous_citations = load_conversation_history(
            db, conversation_id, user_id
        )

    # Detect intent
    intent_result = detect_intent(query, conversation_history, previous_citations)
    logger.info(f"Query intent: {intent_result.intent.value} (confidence={intent_result.confidence:.2f})")

    # Check if we should skip RAG search
    skip_rag = should_skip_rag_search(intent_result) and bool(previous_citations)

    # Check cache first for non-skip queries
    cached_results = None
    if not skip_rag:
        cached_results = get_cached_retrieval_results(user_id, query, config)
        if cached_results:
            logger.info(f"Cache hit for query: {query[:50]}...")
            if len(cached_results) == 6:
                semantic_results, chunk_results, fulltext_results, image_results, graph_results, title_results = cached_results
            else:
                semantic_results, chunk_results, fulltext_results, image_results, graph_results = cached_results
                title_results = []
        else:
            logger.debug(f"Cache miss for query: {query[:50]}...")

    # Execute retrieval if not cached
    if cached_results is None:
        # Generate embedding
        query_embedding = generate_embedding(query)
        if not query_embedding:
            raise ValueError("Failed to generate query embedding")

        # Execute retrieval
        semantic_results, chunk_results, fulltext_results, image_results, graph_results, title_results = execute_retrieval(
            db, query, query_embedding, user_id, config, skip_rag
        )

        # Cache results for future queries (only if not skipping RAG)
        if not skip_rag:
            cache_retrieval_results(
                user_id, query, config,
                (semantic_results, chunk_results, fulltext_results, image_results, graph_results, title_results)
            )

    # Rank results
    ranking_config = RankingConfig(max_results=config.max_sources)
    ranked_results = merge_and_rank(
        semantic_results=semantic_results,
        chunk_results=chunk_results,
        graph_results=graph_results,
        fulltext_results=fulltext_results,
        image_results=image_results,
        config=ranking_config,
        query=query,
        title_results=title_results
    )

    # Build context
    if skip_rag and previous_citations:
        assembled_context = build_context_from_previous_citations(db, previous_citations)
    else:
        context_config = ContextConfig(
            max_tokens=config.max_context_tokens,
            max_content_per_source=config.max_content_per_source
        )
        assembled_context = build_context(ranked_results, context_config)

    # Format conversation context
    conv_context = ""
    if should_include_conversation_context(intent_result) and conversation_history:
        conv_context = format_conversation_context(conversation_history)

    # Get retrieval summary
    retrieval_summary = get_retrieval_summary(ranked_results)

    return QueryExecutionResult(
        assembled_context=assembled_context,
        ranked_results=ranked_results,
        retrieval_summary=retrieval_summary,
        intent_result=intent_result,
        skip_rag=skip_rag,
        conversation_context=conv_context
    )
