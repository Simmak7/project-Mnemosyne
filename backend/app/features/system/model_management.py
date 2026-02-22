"""
Model Management Service - Pull and delete Ollama models.

Proxies Ollama /api/pull (streaming) and /api/delete endpoints.
"""

import json
import logging
import requests
from typing import Generator

from core import config

logger = logging.getLogger(__name__)


def pull_model_stream(model_name: str) -> Generator[str, None, None]:
    """
    Pull a model from Ollama, yielding SSE events with progress.

    Each event is a JSON object with:
    - status: Current status message
    - total: Total bytes (when downloading)
    - completed: Bytes completed
    - percent: Completion percentage (0-100)

    Args:
        model_name: Ollama model identifier (e.g., "qwen3-vl:7b")

    Yields:
        SSE-formatted strings: "data: {...}\n\n"
    """
    url = f"{config.OLLAMA_HOST}/api/pull"
    logger.info(f"Starting model pull: {model_name}")

    try:
        response = requests.post(
            url,
            json={"name": model_name, "stream": True},
            stream=True,
            timeout=600,
        )

        if response.status_code != 200:
            error = {"status": "error", "error": f"Ollama returned {response.status_code}"}
            yield f"data: {json.dumps(error)}\n\n"
            return

        ollama_success = False
        ollama_error = False

        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)

                # Ollama sends status "success" when pull is fully complete
                if data.get("status") == "success":
                    ollama_success = True

                if data.get("error"):
                    ollama_error = True
                    event = {
                        "status": "error",
                        "error": data["error"],
                        "percent": 0,
                    }
                    yield f"data: {json.dumps(event)}\n\n"
                    return

                total = data.get("total", 0)
                completed = data.get("completed", 0)
                percent = round((completed / total) * 100, 1) if total > 0 else 0

                event = {
                    "status": data.get("status", ""),
                    "total": total,
                    "completed": completed,
                    "percent": percent,
                }

                yield f"data: {json.dumps(event)}\n\n"
            except json.JSONDecodeError:
                continue

        # Only send success if Ollama actually confirmed the pull completed
        if ollama_success and not ollama_error:
            from core.models_registry_helpers import invalidate_ollama_cache
            from features.system.update_checker import invalidate_update_cache
            invalidate_ollama_cache()
            invalidate_update_cache(model_name)
            yield f"data: {json.dumps({'status': 'success', 'percent': 100})}\n\n"
        elif not ollama_error:
            logger.warning(f"Model pull stream ended without success for {model_name}")
            error = {"status": "error", "error": "Pull stream ended unexpectedly"}
            yield f"data: {json.dumps(error)}\n\n"

    except requests.exceptions.Timeout:
        error = {"status": "error", "error": "Ollama pull timed out after 600s"}
        yield f"data: {json.dumps(error)}\n\n"
    except Exception as e:
        logger.error(f"Model pull failed: {e}")
        error = {"status": "error", "error": str(e)}
        yield f"data: {json.dumps(error)}\n\n"


def delete_model(model_name: str) -> dict:
    """
    Delete a model from Ollama.

    Args:
        model_name: Ollama model identifier

    Returns:
        Dict with status and message
    """
    url = f"{config.OLLAMA_HOST}/api/delete"
    logger.info(f"Deleting model: {model_name}")

    try:
        response = requests.delete(
            url,
            json={"name": model_name},
            timeout=30,
        )

        from core.models_registry_helpers import invalidate_ollama_cache
        from features.system.update_checker import invalidate_update_cache
        invalidate_ollama_cache()
        invalidate_update_cache(model_name)

        if response.status_code == 200:
            return {"status": "success", "message": f"Model '{model_name}' deleted"}

        return {"status": "error", "error": f"Ollama returned {response.status_code}"}

    except Exception as e:
        logger.error(f"Model delete failed: {e}")
        return {"status": "error", "error": str(e)}
