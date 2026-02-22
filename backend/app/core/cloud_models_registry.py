"""
Cloud AI Models Registry - Definitions for cloud provider models.

Separated from models_registry.py for file size compliance.
"""

from typing import Dict

from core.models_registry import ModelInfo, ModelCategory, ModelUseCase, ProviderSource


CLOUD_MODELS: Dict[str, ModelInfo] = {
    # Anthropic Claude models
    "claude-sonnet-4-20250514": ModelInfo(
        id="claude-sonnet-4-20250514",
        name="Claude Sonnet 4",
        description="Fast, intelligent model for everyday tasks",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.BALANCED,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BRAIN, ModelUseCase.BOTH],
        context_length=200000,
        features=["200K context", "Strong reasoning", "Cloud AI"],
        recommended_for="Fast cloud RAG and Brain queries",
        provider=ProviderSource.ANTHROPIC,
    ),
    "claude-sonnet-4-5-20250929": ModelInfo(
        id="claude-sonnet-4-5-20250929",
        name="Claude Sonnet 4.5",
        description="Most capable balanced model with hybrid reasoning",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.POWERFUL,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BRAIN, ModelUseCase.BOTH],
        context_length=200000,
        features=["200K context", "Hybrid reasoning", "Extended thinking", "Cloud AI"],
        recommended_for="Best quality cloud responses",
        provider=ProviderSource.ANTHROPIC,
    ),
    "claude-opus-4-0520": ModelInfo(
        id="claude-opus-4-0520",
        name="Claude Opus 4",
        description="Most capable model for complex tasks",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.POWERFUL,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BRAIN, ModelUseCase.BOTH],
        context_length=200000,
        features=["200K context", "Strongest reasoning", "Cloud AI"],
        recommended_for="Most demanding analysis tasks",
        provider=ProviderSource.ANTHROPIC,
    ),
    "claude-haiku-4-5-20251001": ModelInfo(
        id="claude-haiku-4-5-20251001",
        name="Claude Haiku 4.5",
        description="Fastest Claude model, great for quick tasks",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.FAST,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BOTH],
        context_length=200000,
        features=["200K context", "Ultra-fast", "Cost-effective", "Cloud AI"],
        recommended_for="Quick searches and simple Q&A",
        provider=ProviderSource.ANTHROPIC,
    ),

    # OpenAI GPT models
    "gpt-4o": ModelInfo(
        id="gpt-4o",
        name="GPT-4o",
        description="OpenAI's flagship multimodal model",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.POWERFUL,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BRAIN, ModelUseCase.BOTH],
        context_length=128000,
        features=["128K context", "Multimodal", "Cloud AI"],
        recommended_for="Versatile cloud AI for all tasks",
        provider=ProviderSource.OPENAI,
    ),
    "gpt-4o-mini": ModelInfo(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        description="Fast and cost-effective GPT model",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.FAST,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BOTH],
        context_length=128000,
        features=["128K context", "Fast inference", "Cost-effective", "Cloud AI"],
        recommended_for="Quick cloud queries on a budget",
        provider=ProviderSource.OPENAI,
    ),
    "o1": ModelInfo(
        id="o1",
        name="o1",
        description="OpenAI reasoning model with chain-of-thought",
        size_gb=0,
        parameters="Cloud",
        category=ModelCategory.POWERFUL,
        use_cases=[ModelUseCase.RAG, ModelUseCase.BRAIN, ModelUseCase.BOTH],
        context_length=200000,
        features=["200K context", "Deep reasoning", "Chain-of-thought", "Cloud AI"],
        recommended_for="Complex analysis requiring deep reasoning",
        provider=ProviderSource.OPENAI,
    ),
}
