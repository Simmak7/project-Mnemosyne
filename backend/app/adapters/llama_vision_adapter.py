"""
Llama 3.2 Vision 11B Model Adapter

Handles communication with Ollama API for Llama 3.2 Vision model.
This is a refactor of the existing logic from tasks.py.
"""

import requests
import base64
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LlamaVisionAdapter:
    """
    Adapter for Llama 3.2 Vision 11B model via Ollama.

    This is the current/legacy model adapter, refactored from tasks.py.

    Model characteristics:
    - VRAM usage: ~6.5-7.5GB
    - Inference time: 8-12 seconds per image
    - Model load time: 5-7 seconds
    - Good general-purpose vision understanding
    """

    def __init__(self, ollama_host: str, model_name: str = "llama3.2-vision:11b"):
        """
        Initialize Llama Vision Adapter.

        Args:
            ollama_host: Ollama server URL (e.g., "http://ollama:11434")
            model_name: Llama model name (default: "llama3.2-vision:11b")
        """
        self.ollama_host = ollama_host
        self.model_name = model_name
        self.api_url = f"{ollama_host}/api/generate"

        logger.info(f"Initialized LlamaVisionAdapter with model: {model_name}")

    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        timeout: int = 300
    ) -> Dict[str, any]:
        """
        Analyze an image using Llama 3.2 Vision model.

        This method replicates the existing logic from tasks.py:331-340.

        Args:
            image_path: Path to the image file
            prompt: Analysis prompt
            timeout: Request timeout in seconds (default: 300)

        Returns:
            Dictionary with:
            - status: "success" or "error"
            - response: AI-generated analysis text
            - model: Model name used
            - error: Error message (if status="error")

        Raises:
            FileNotFoundError: If image file doesn't exist
            requests.RequestException: If Ollama API call fails
        """
        # Validate image file exists
        if not Path(image_path).exists():
            error_msg = f"Image file not found: {image_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Read and encode image
        try:
            with open(image_path, "rb") as img_file:
                image_bytes = img_file.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            logger.debug(f"Image encoded: {len(image_bytes)} bytes")
        except Exception as e:
            error_msg = f"Failed to read/encode image: {str(e)}"
            logger.error(error_msg)
            raise

        logger.info(f"Sending analysis request to Llama model: {self.model_name}")

        try:
            # Call Ollama API (same as tasks.py:331-340)
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "images": [image_base64],
                    "stream": False
                },
                timeout=timeout
            )

            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get("response", "No response from AI")

                logger.info("Llama analysis successful")

                return {
                    "status": "success",
                    "response": analysis_text,
                    "model": self.model_name
                }

            elif response.status_code == 404:
                error_msg = (
                    f"Llama model '{self.model_name}' not found on Ollama server. "
                    f"Please pull the model: docker-compose exec ollama ollama pull {self.model_name}"
                )
                logger.error(error_msg)
                return {
                    "status": "error",
                    "error": error_msg,
                    "model": self.model_name,
                    "http_status": 404
                }

            else:
                error_msg = f"Ollama API returned status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "error": error_msg,
                    "model": self.model_name,
                    "http_status": response.status_code
                }

        except requests.Timeout:
            error_msg = f"Request timeout after {timeout}s (Llama model may be loading for first time)"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "model": self.model_name
            }
        except requests.RequestException as e:
            error_msg = f"Ollama API request failed: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "model": self.model_name
            }

    def health_check(self) -> bool:
        """
        Check if Ollama server is accessible and Llama model is available.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Check if Ollama server is up
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)

            if response.status_code != 200:
                logger.warning(f"Ollama server health check failed: HTTP {response.status_code}")
                return False

            # Check if Llama model is available
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]

            if self.model_name in model_names:
                logger.info(f"Health check passed: {self.model_name} is available")
                return True
            else:
                logger.warning(
                    f"Health check failed: {self.model_name} not found. "
                    f"Available models: {model_names}"
                )
                return False

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

    def __repr__(self):
        return f"LlamaVisionAdapter(model={self.model_name}, host={self.ollama_host})"
