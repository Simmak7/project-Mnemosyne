"""
Qwen 2.5-VL 7B Vision Model Adapter

Handles communication with Ollama API for Qwen 2.5-VL model.
Optimized for RTX 5070 (12GB VRAM).
"""

import requests
import base64
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class QwenVisionAdapter:
    """
    Adapter for Qwen 2.5-VL 7B (q4_K_M) vision model via Ollama.

    Model characteristics:
    - VRAM usage: ~4-5GB (q4_K_M quantization)
    - Inference time: 6-10 seconds per image
    - Model load time: 3-5 seconds
    - Excellent OCR for documents
    - Superior diagram analysis
    - Better performance than Llama 3.2-Vision 11B
    """

    def __init__(self, ollama_host: str, model_name: str = "qwen2.5vl:7b-q4_K_M"):
        """
        Initialize Qwen Vision Adapter.

        Args:
            ollama_host: Ollama server URL (e.g., "http://ollama:11434")
            model_name: Qwen model name (default: "qwen2.5vl:7b-q4_K_M")
        """
        self.ollama_host = ollama_host
        self.model_name = model_name
        self.api_url = f"{ollama_host}/api/generate"

        logger.info(f"Initialized QwenVisionAdapter with model: {model_name}")

    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        timeout: int = 300
    ) -> Dict[str, any]:
        """
        Analyze an image using Qwen 2.5-VL model.

        Args:
            image_path: Path to the image file
            prompt: Analysis prompt (typically Hybrid Smart-Router Prompt)
            timeout: Request timeout in seconds (default: 300)

        Returns:
            Dictionary with:
            - status: "success" or "error"
            - response: AI-generated analysis text
            - model: Model name used
            - error: Error message (if status="error")
            - eval_count: Number of tokens generated (if available)
            - total_duration: Total processing time in nanoseconds (if available)

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

        # Prepare request payload
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                # Qwen-specific options for optimal performance
                "num_predict": 2048,  # Max tokens to generate
                "temperature": 0.7,   # Balanced creativity/accuracy
                "top_p": 0.9,         # Nucleus sampling
                "top_k": 40           # Top-k sampling
            }
        }

        logger.info(f"Sending analysis request to Qwen model: {self.model_name}")

        try:
            # Call Ollama API
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=timeout
            )

            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get("response", "No response from AI")

                # Extract performance metrics if available
                eval_count = result.get("eval_count", 0)
                total_duration_ns = result.get("total_duration", 0)
                total_duration_s = total_duration_ns / 1_000_000_000 if total_duration_ns else 0

                logger.info(
                    f"Qwen analysis successful: {eval_count} tokens, "
                    f"{total_duration_s:.2f}s total duration"
                )

                return {
                    "status": "success",
                    "response": analysis_text,
                    "model": self.model_name,
                    "eval_count": eval_count,
                    "total_duration_ns": total_duration_ns,
                    "total_duration_s": total_duration_s
                }

            elif response.status_code == 404:
                error_msg = (
                    f"Qwen model '{self.model_name}' not found on Ollama server. "
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
            error_msg = f"Request timeout after {timeout}s (Qwen model may be loading for first time)"
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
        Check if Ollama server is accessible and Qwen model is available.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Check if Ollama server is up
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)

            if response.status_code != 200:
                logger.warning(f"Ollama server health check failed: HTTP {response.status_code}")
                return False

            # Check if Qwen model is available
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
        return f"QwenVisionAdapter(model={self.model_name}, host={self.ollama_host})"
