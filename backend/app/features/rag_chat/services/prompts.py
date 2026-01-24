"""
RAG prompt templates for citation-aware responses.

Provides carefully crafted prompts that:
- Enforce citation usage
- Prevent hallucination
- Structure responses appropriately
- Handle different query types
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RAGPromptConfig:
    """Configuration for RAG prompt generation."""
    require_citations: bool = True
    allow_no_context_response: bool = True
    suggest_follow_ups: bool = True
    confidence_instruction: bool = True


# ============================================
# System Prompts
# ============================================

RAG_SYSTEM_PROMPT = """You are an AI assistant for Mnemosyne, a personal knowledge management system.

Your role is to answer questions using ONLY the context provided from the user's notes and images.

## CRITICAL RULES

1. **USE ONLY PROVIDED CONTEXT**
   - Only use information from the numbered sources [1], [2], etc.
   - Never invent facts or use information from your training data
   - If the context doesn't contain an answer, say so clearly

2. **ALWAYS CITE YOUR SOURCES**
   - Use [N] notation to cite sources inline
   - Every fact or claim must have a citation
   - Multiple sources can be combined: [1][2]
   - Place citations immediately after the relevant information

3. **HANDLE UNCERTAINTY**
   - If information is incomplete, acknowledge it: "Based on [1], it seems..."
   - If sources conflict, mention both: "Source [1] says X, while [2] suggests Y"
   - Never guess or fill gaps with assumptions

4. **BE CONCISE AND HELPFUL**
   - Answer the question directly first
   - Provide supporting details with citations
   - Suggest related topics the user might explore

## CITATION FORMAT

Correct: "The project uses FastAPI [1] for the backend."
Correct: "Authentication is handled via JWT tokens [1][3]."
Incorrect: "The project uses FastAPI." (missing citation)
Incorrect: "Based on my knowledge, the project uses FastAPI." (using external knowledge)

## RESPONSE STRUCTURE

1. Direct answer to the question
2. Supporting details with citations
3. (Optional) Related topics to explore
4. (If uncertain) Acknowledgment of limitations

## WHEN CONTEXT IS INSUFFICIENT

If the provided context doesn't contain enough information:
- Say: "I don't have enough information in your notes about [topic]."
- Suggest: "You might want to create a note about [topic]."
- Do NOT make up information

Remember: It's better to say "I don't know from your notes" than to hallucinate."""


RAG_SYSTEM_PROMPT_CONCISE = """You are a knowledge assistant for a personal note-taking app.

RULES:
1. ONLY use information from the provided sources [1], [2], etc.
2. ALWAYS cite sources using [N] notation
3. If info isn't in context, say "I don't have that in your notes"
4. Be concise and direct

CITATION: Every fact needs [N] citation. Example: "The API uses FastAPI [1]."
"""


# ============================================
# User Message Templates
# ============================================

def format_user_message_with_context(
    query: str,
    context: str,
    source_count: int,
    config: RAGPromptConfig = None
) -> str:
    """
    Format the user message with context for RAG.

    Args:
        query: User's question
        context: Formatted context from context_builder
        source_count: Number of sources provided
        config: Prompt configuration

    Returns:
        Formatted user message
    """
    if config is None:
        config = RAGPromptConfig()

    message_parts = []

    # Context section
    message_parts.append("## CONTEXT FROM YOUR NOTES\n")
    message_parts.append(f"I found {source_count} relevant sources:\n")
    message_parts.append(context)
    message_parts.append("\n## YOUR QUESTION\n")
    message_parts.append(query)

    if config.require_citations:
        message_parts.append(
            "\n\n(Remember to cite sources using [1], [2], etc.)"
        )

    if config.confidence_instruction:
        message_parts.append(
            "\n(If you're uncertain, express that uncertainty.)"
        )

    return '\n'.join(message_parts)


def format_no_context_message(query: str) -> str:
    """
    Format message when no relevant context is found.

    Args:
        query: User's question

    Returns:
        Formatted message
    """
    return f"""## YOUR QUESTION
{query}

## CONTEXT
I searched your notes but didn't find any content directly related to this question.

Please respond by:
1. Acknowledging that you don't have relevant notes on this topic
2. Suggesting that the user might want to create a note about this
3. Offering to help if they provide more context"""


def format_follow_up_message(
    query: str,
    previous_context: str,
    previous_response: str
) -> str:
    """
    Format a follow-up question in a conversation.

    Args:
        query: Follow-up question
        previous_context: Context from previous turn
        previous_response: AI's previous response

    Returns:
        Formatted follow-up message
    """
    return f"""## PREVIOUS CONTEXT
{previous_context}

## PREVIOUS RESPONSE
{previous_response}

## FOLLOW-UP QUESTION
{query}

Use the same sources if relevant, or indicate if you need different information."""


# ============================================
# Response Parsing
# ============================================

def extract_confidence_signals(response: str) -> Dict[str, Any]:
    """
    Extract confidence signals from the response.

    Looks for uncertainty markers like:
    - "seems", "appears", "might", "could"
    - "based on limited information"
    - "I'm not certain"

    Args:
        response: LLM response text

    Returns:
        Dictionary with confidence analysis
    """
    uncertainty_markers = [
        'seems', 'appears', 'might', 'could', 'possibly',
        'uncertain', 'not sure', 'limited information',
        "don't have", "couldn't find", 'unclear'
    ]

    response_lower = response.lower()
    found_markers = [
        marker for marker in uncertainty_markers
        if marker in response_lower
    ]

    # Simple confidence heuristic
    if not found_markers:
        confidence = 0.9
        confidence_level = 'high'
    elif len(found_markers) <= 2:
        confidence = 0.7
        confidence_level = 'medium'
    else:
        confidence = 0.4
        confidence_level = 'low'

    return {
        'confidence_score': confidence,
        'confidence_level': confidence_level,
        'uncertainty_markers': found_markers,
        'marker_count': len(found_markers)
    }


def validate_citations(response: str, source_count: int) -> Dict[str, Any]:
    """
    Validate that citations in the response are valid.

    Args:
        response: LLM response text
        source_count: Number of sources that were provided

    Returns:
        Validation results
    """
    import re

    # Find all citation patterns
    pattern = r'\[(\d+)\]'
    matches = re.findall(pattern, response)

    valid_citations = []
    invalid_citations = []

    for match in matches:
        try:
            index = int(match)
            if 1 <= index <= source_count:
                valid_citations.append(index)
            else:
                invalid_citations.append(index)
        except ValueError:
            invalid_citations.append(match)

    # Check if response has any citations
    has_citations = len(valid_citations) > 0

    # Check citation coverage (rough heuristic)
    unique_citations = set(valid_citations)
    coverage = len(unique_citations) / source_count if source_count > 0 else 0

    return {
        'has_citations': has_citations,
        'valid_citations': sorted(list(unique_citations)),
        'invalid_citations': invalid_citations,
        'citation_count': len(valid_citations),
        'unique_sources_cited': len(unique_citations),
        'source_coverage': round(coverage, 2)
    }


# ============================================
# Query Type Detection
# ============================================

def detect_query_type(query: str) -> str:
    """
    Detect the type of query for prompt optimization.

    Types:
    - factual: "What is X?" / "How does X work?"
    - comparison: "What's the difference between X and Y?"
    - exploratory: "Tell me about X" / "Explain X"
    - procedural: "How do I X?" / "Steps to X"
    - meta: About the notes themselves

    Args:
        query: User query text

    Returns:
        Query type string
    """
    query_lower = query.lower().strip()

    # Procedural queries
    if query_lower.startswith(('how do i', 'how can i', 'steps to', 'how to')):
        return 'procedural'

    # Comparison queries
    if 'difference between' in query_lower or 'compare' in query_lower:
        return 'comparison'

    # Meta queries (about notes)
    meta_patterns = ['what notes', 'which notes', 'find notes', 'search for']
    if any(p in query_lower for p in meta_patterns):
        return 'meta'

    # Factual queries
    if query_lower.startswith(('what is', 'what are', 'who is', 'when did', 'where is')):
        return 'factual'

    # Default to exploratory
    return 'exploratory'


def get_query_specific_instructions(query_type: str) -> str:
    """
    Get additional instructions based on query type.

    Args:
        query_type: Type of query

    Returns:
        Additional instructions string
    """
    instructions = {
        'factual': "Provide a direct, concise answer with citations.",
        'comparison': "Compare the items systematically, citing sources for each point.",
        'exploratory': "Provide a comprehensive overview, citing multiple sources.",
        'procedural': "List the steps clearly, citing sources for each step.",
        'meta': "Focus on which notes contain relevant information and why."
    }

    return instructions.get(query_type, "")
