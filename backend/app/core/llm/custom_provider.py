"""
Custom OpenAI-Compatible LLM Provider.

Extends OpenAIProvider for custom endpoints (Groq, Together AI, etc.).
Users provide their own endpoint URL + API key.
"""

import logging
from typing import List

from core.llm.base import ProviderType
from core.llm.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class CustomProvider(OpenAIProvider):
    """LLM provider for custom OpenAI-compatible endpoints."""

    provider_type = ProviderType.CUSTOM

    def __init__(self, api_key: str, base_url: str = None):
        if not base_url:
            raise ValueError("Custom provider requires a base_url")
        super().__init__(api_key=api_key, base_url=base_url)

    def health_check(self) -> dict:
        """Verify custom endpoint is reachable."""
        try:
            self.client.models.list()
            return {
                "provider": "custom",
                "connected": True,
                "base_url": self.base_url,
                "healthy": True,
            }
        except Exception as e:
            return {
                "provider": "custom",
                "connected": False,
                "base_url": self.base_url,
                "error": str(e),
                "healthy": False,
            }

    def list_models(self) -> List[dict]:
        """Try to list models from the custom endpoint."""
        try:
            models = self.client.models.list()
            return [
                {
                    "id": m.id,
                    "name": m.id,
                    "provider": "custom",
                }
                for m in models.data[:20]
            ]
        except Exception as e:
            logger.warning(f"Failed to list custom models: {e}")
            return []
