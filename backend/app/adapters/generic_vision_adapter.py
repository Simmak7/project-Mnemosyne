"""
Generic Vision Adapter - Model-agnostic Ollama vision adapter.

Calls Ollama /api/generate with base64 image and any vision model name.
Works with Llama, Qwen, and any future Ollama vision models.
"""

import requests
import base64
import logging
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class GenericVisionAdapter:
    """
    Model-agnostic adapter for any Ollama vision model.

    Unlike LlamaVisionAdapter/QwenVisionAdapter which are model-specific,
    this adapter works with any model name passed at init time.
    """

    def __init__(self, ollama_host: str, model_name: str):
        self.ollama_host = ollama_host
        self.model_name = model_name
        self.api_url = f"{ollama_host}/api/generate"

    def analyze_image(
        self, image_path: str, prompt: str, timeout: int = 300,
    ) -> Dict[str, any]:
        """
        Analyze an image using the configured vision model.

        Args:
            image_path: Path to the image file
            prompt: Analysis prompt
            timeout: Request timeout in seconds

        Returns:
            Dict with status, response, model keys
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        logger.info(f"GenericVisionAdapter: analyzing with {self.model_name}")

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "images": [image_base64],
                    "stream": False,
                },
                timeout=timeout,
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "response": result.get("response", "No response from AI"),
                    "model": self.model_name,
                }

            if response.status_code == 404:
                return {
                    "status": "error",
                    "error": f"Model '{self.model_name}' not found in Ollama",
                    "model": self.model_name,
                }

            return {
                "status": "error",
                "error": f"Ollama returned {response.status_code}: {response.text[:200]}",
                "model": self.model_name,
            }

        except requests.Timeout:
            return {
                "status": "error",
                "error": f"Timeout after {timeout}s with {self.model_name}",
                "model": self.model_name,
            }
        except requests.RequestException as e:
            return {
                "status": "error",
                "error": f"Request failed: {e}",
                "model": self.model_name,
            }

    def health_check(self) -> bool:
        """Check if model is available in Ollama."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code != 200:
                return False
            models = [m.get("name") for m in response.json().get("models", [])]
            return self.model_name in models
        except Exception:
            return False
