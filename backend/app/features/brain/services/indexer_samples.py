"""Brain Indexer - Training Sample Generation.

Functions for generating training samples from classified facts.
"""

from typing import List, Dict

from .classifier import ClassifiedFact


# Training sample templates by type
SAMPLE_TEMPLATES = {
    "identity": [
        ("Who am I?", "You are {content}"),
        ("Tell me about myself.", "{content}"),
    ],
    "interests": [
        ("What topics am I interested in?", "You frequently explore: {content}"),
        ("What are my main interests?", "{content}"),
    ],
    "cognitive_style": [
        ("How do I organize my thoughts?", "{content}"),
        ("What's my thinking style?", "{content}"),
    ],
    "preferences": [
        ("What are my preferences?", "{content}"),
        ("How do I like things done?", "{content}"),
    ],
    "projects": [
        ("What am I working on?", "{content}"),
        ("What are my current projects?", "{content}"),
    ],
    "behaviors": [
        ("What are my habits?", "{content}"),
        ("What do I typically do?", "{content}"),
    ],
}


def determine_sample_type(facts: List[ClassifiedFact]) -> str:
    """Determine the sample type based on facts."""
    # Check classification reasons and fact types
    reasons = [f.classification_reason for f in facts]
    fact_types = [f.fact.fact_type for f in facts]

    if any("identity" in r for r in reasons):
        return "identity"
    if any("preference" in r for r in reasons):
        return "preferences"
    if "relation" in fact_types:
        return "projects"
    if "entity" in fact_types:
        return "interests"

    return "behaviors"


def combine_facts_for_sample(facts: List[ClassifiedFact]) -> str:
    """Combine multiple facts into a coherent training output."""
    if not facts:
        return ""

    # Simple combination - join fact texts
    fact_texts = [f.fact.fact_text for f in facts if f.fact.fact_text]

    if len(fact_texts) == 1:
        return fact_texts[0]

    # Combine with semicolons for multiple facts
    return "; ".join(fact_texts[:5])  # Limit to 5 facts per sample
