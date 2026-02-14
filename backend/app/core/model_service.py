"""
Model Service - Get effective AI model for a user.

This service resolves which model to use for a user, considering:
1. User's preference (if set)
2. System default (from config)
3. Model availability validation
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from core import config
from core.models_registry import get_model_info, get_all_models

logger = logging.getLogger(__name__)


def get_effective_rag_model(db: Session, user_id: int) -> str:
    """
    Get the effective RAG model for a user.

    Priority:
    1. User's rag_model preference (if set and valid)
    2. System default (config.RAG_MODEL)
    """
    from models import UserPreferences

    # Try to get user preference
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()

    if prefs and prefs.rag_model:
        # Validate the model exists in registry
        model_info = get_model_info(prefs.rag_model)
        if model_info:
            logger.debug(f"Using user RAG model preference: {prefs.rag_model}")
            return prefs.rag_model
        else:
            logger.warning(
                f"User {user_id} has invalid RAG model preference: {prefs.rag_model}, "
                f"falling back to system default"
            )

    logger.debug(f"Using system default RAG model: {config.RAG_MODEL}")
    return config.RAG_MODEL


def get_effective_brain_model(db: Session, user_id: int) -> str:
    """
    Get the effective Brain model for a user.

    Priority:
    1. User's brain_model preference (if set and valid)
    2. System default (config.BRAIN_MODEL)
    """
    from models import UserPreferences

    # Try to get user preference
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()

    if prefs and prefs.brain_model:
        # Validate the model exists in registry
        model_info = get_model_info(prefs.brain_model)
        if model_info:
            logger.debug(f"Using user Brain model preference: {prefs.brain_model}")
            return prefs.brain_model
        else:
            logger.warning(
                f"User {user_id} has invalid Brain model preference: {prefs.brain_model}, "
                f"falling back to system default"
            )

    logger.debug(f"Using system default Brain model: {config.BRAIN_MODEL}")
    return config.BRAIN_MODEL


def get_effective_nexus_model(db: Session, user_id: int) -> str:
    """
    Get the effective NEXUS generation model for a user.

    Priority:
    1. User's nexus_model preference (if set and valid)
    2. User's rag_model preference (if set and valid)
    3. System default (config.RAG_MODEL)
    """
    from models import UserPreferences

    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()

    if prefs and getattr(prefs, 'nexus_model', None):
        model_info = get_model_info(prefs.nexus_model)
        if model_info:
            logger.debug(f"Using user NEXUS model preference: {prefs.nexus_model}")
            return prefs.nexus_model
        else:
            logger.warning(
                f"User {user_id} has invalid NEXUS model preference: {prefs.nexus_model}, "
                f"trying RAG model fallback"
            )

    # Fall back to RAG model
    return get_effective_rag_model(db, user_id)


def get_effective_context_budget(db: Session, user_id: int) -> int:
    """
    Compute the dynamic brain context token budget based on the user's model.

    Uses the model's context_length and BRAIN_CONTEXT_RATIO to scale the
    budget, floored at BRAIN_MIN_CONTEXT_TOKENS.

    Returns:
        Token budget for brain knowledge context
    """
    from core.models_registry import get_model_info

    brain_model_id = get_effective_brain_model(db, user_id)
    model_info = get_model_info(brain_model_id)

    min_budget = getattr(config, "BRAIN_MIN_CONTEXT_TOKENS", 4000)
    ratio = getattr(config, "BRAIN_CONTEXT_RATIO", 0.6)

    if not model_info:
        # Unknown model — fall back to legacy hardcoded budget
        fallback = getattr(config, "BRAIN_MAX_CONTEXT_TOKENS", 6000)
        logger.warning(
            f"Model '{brain_model_id}' not in registry, "
            f"using fallback budget {fallback}"
        )
        return fallback

    context_window = model_info.context_length

    # Use 60% of context window, but leave at least 2000 tokens for
    # conversation history + response generation
    budget = min(
        int(context_window * ratio),
        context_window - 2000,
    )

    budget = max(budget, min_budget)

    # Cap budget to prevent "lost in the middle" issues with smaller models
    MAX_PRACTICAL_BUDGET = 8000
    budget = min(budget, MAX_PRACTICAL_BUDGET)

    logger.debug(
        f"Context budget for model '{brain_model_id}' "
        f"(ctx={context_window}): {budget} tokens"
    )
    return budget


def get_user_model_config(db: Session, user_id: int) -> dict:
    """
    Get the complete model configuration for a user.

    Returns dict with:
    - rag_model: Effective RAG model ID
    - brain_model: Effective Brain model ID
    - rag_model_info: Model metadata (or None if not in registry)
    - brain_model_info: Model metadata (or None if not in registry)
    - user_rag_override: Whether user has custom RAG model
    - user_brain_override: Whether user has custom Brain model
    """
    from models import UserPreferences

    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()

    rag_model = get_effective_rag_model(db, user_id)
    brain_model = get_effective_brain_model(db, user_id)

    return {
        "rag_model": rag_model,
        "brain_model": brain_model,
        "rag_model_info": get_model_info(rag_model),
        "brain_model_info": get_model_info(brain_model),
        "user_rag_override": bool(prefs and prefs.rag_model),
        "user_brain_override": bool(prefs and prefs.brain_model),
    }


def validate_model_id(model_id: str) -> bool:
    """Check if a model ID is valid (exists in registry)."""
    return get_model_info(model_id) is not None


def get_available_model_ids() -> list[str]:
    """Get list of all available model IDs."""
    return [m.id for m in get_all_models()]


def get_provider_for_model(model_id: str) -> Optional[str]:
    """Determine which provider serves a model."""
    from core.models_registry import get_model_info, ProviderSource
    info = get_model_info(model_id)
    if not info:
        return None
    return info.provider.value


def get_provider_for_user(db: Session, user_id: int, use_case: str = "rag"):
    """
    Get the appropriate LLM provider and model for a user.

    Checks cloud AI preferences, validates API key availability,
    and falls back to Ollama if cloud is unavailable.

    Args:
        db: Database session
        user_id: User ID
        use_case: "rag" or "brain"

    Returns:
        Tuple of (LLMProvider, model_id, provider_type_str)
    """
    from models import UserPreferences
    from core.llm import get_default_provider, get_provider, ProviderType
    from core.llm.base import ProviderType as PT
    from features.settings.api_keys_service import get_api_key_with_url

    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()

    # Check if cloud AI is enabled
    if prefs and getattr(prefs, "cloud_ai_enabled", False):
        cloud_provider = getattr(prefs, "cloud_ai_provider", None)

        if cloud_provider:
            # Get the cloud model for this use case
            if use_case == "brain":
                cloud_model = getattr(prefs, "cloud_brain_model", None)
            else:
                cloud_model = getattr(prefs, "cloud_rag_model", None)

            if cloud_model:
                # Try to get the provider
                key_info = get_api_key_with_url(db, user_id, cloud_provider)
                if key_info:
                    try:
                        from core.llm.registry import register_cloud_provider
                        provider_map = {
                            "anthropic": PT.ANTHROPIC,
                            "openai": PT.OPENAI,
                            "custom": PT.CUSTOM,
                        }
                        ptype = provider_map.get(cloud_provider)
                        if ptype:
                            provider = register_cloud_provider(
                                ptype,
                                key_info["api_key"],
                                key_info.get("base_url"),
                            )
                            return provider, cloud_model, cloud_provider
                    except Exception as e:
                        logger.warning(
                            f"Cloud provider {cloud_provider} failed for "
                            f"user {user_id}, falling back to Ollama: {e}"
                        )

    # Fallback to Ollama
    if use_case == "brain":
        model = get_effective_brain_model(db, user_id)
    else:
        model = get_effective_rag_model(db, user_id)

    return get_default_provider(), model, "ollama"
