"""
Embedding generation module for semantic search.

This module provides functions to generate embeddings using Ollama's nomic-embed-text model.
Embeddings are 768-dimensional vectors used for semantic similarity search via pgvector.

Ollama API:
- Endpoint: POST /api/embeddings
- Model: nomic-embed-text (274MB, 768 dimensions)
- Timeout: 30 seconds per request

pgvector Integration:
- Embeddings stored in Note.embedding column (vector(768))
- Similarity search uses cosine distance operator (<=>)
- ivfflat index for efficient nearest neighbor search
"""

import os
import requests
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Get Ollama host from environment
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIMENSION = 768
MAX_TEXT_LENGTH = 2000  # Maximum characters to send to embedding model


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate a semantic embedding vector for the given text.

    Uses Ollama's nomic-embed-text model to generate a 768-dimensional embedding.
    Text is truncated to MAX_TEXT_LENGTH characters before processing.

    Args:
        text: The text to generate an embedding for (note title + content)

    Returns:
        List of 768 floats representing the embedding vector, or None if generation fails

    Raises:
        requests.exceptions.RequestException: If the Ollama API request fails
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding generation")
        return None

    # Truncate text to max length
    text_to_embed = text[:MAX_TEXT_LENGTH].strip()

    if not text_to_embed:
        logger.warning("Text became empty after truncation and stripping")
        return None

    try:
        logger.info(f"Generating embedding for text (length: {len(text_to_embed)} chars)")

        # Call Ollama embedding API
        response = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": text_to_embed
            },
            timeout=30  # 30 second timeout
        )

        response.raise_for_status()
        data = response.json()

        embedding = data.get("embedding")

        if not embedding:
            logger.error(f"No embedding in response: {data}")
            return None

        if len(embedding) != EMBEDDING_DIMENSION:
            logger.error(
                f"Unexpected embedding dimension: {len(embedding)} "
                f"(expected {EMBEDDING_DIMENSION})"
            )
            return None

        logger.info(f"Successfully generated {len(embedding)}-dimensional embedding")
        return embedding

    except requests.exceptions.Timeout:
        logger.error(f"Timeout while generating embedding (>{30}s)")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to generate embedding: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error generating embedding: {str(e)}", exc_info=True)
        return None


def prepare_note_text(title: str, content: str) -> str:
    """
    Prepare note text for embedding generation.

    Combines title and content, with title given more weight by including it twice.
    This helps embeddings better capture the note's main topic.

    Args:
        title: Note title
        content: Note content

    Returns:
        Combined text ready for embedding generation
    """
    # Include title twice for more weight, then content
    combined = f"{title}\n{title}\n{content}"

    # Truncate to max length
    return combined[:MAX_TEXT_LENGTH]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Used for in-memory similarity comparisons when database query is not available.
    For database queries, use pgvector's <=> operator instead.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score between -1 and 1 (higher = more similar)
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"Vector dimension mismatch: {len(vec1)} vs {len(vec2)}")

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def check_ollama_health() -> bool:
    """
    Check if Ollama service is available and has the required model.

    Used by health check endpoint and startup verification.

    Returns:
        True if Ollama is healthy and has nomic-embed-text model, False otherwise
    """
    try:
        # Check if Ollama is reachable
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        response.raise_for_status()

        # Check if required model is available
        data = response.json()
        models = data.get("models", [])
        model_names = [model.get("name", "") for model in models]

        has_model = any(EMBEDDING_MODEL in name for name in model_names)

        if not has_model:
            logger.warning(
                f"Ollama is reachable but {EMBEDDING_MODEL} model not found. "
                f"Available models: {model_names}"
            )
            logger.info(f"To install: docker-compose exec ollama ollama pull {EMBEDDING_MODEL}")

        return has_model

    except Exception as e:
        logger.error(f"Ollama health check failed: {str(e)}")
        return False


def batch_generate_embeddings(texts: List[str]) -> List[Optional[List[float]]]:
    """
    Generate embeddings for multiple texts.

    Processes texts sequentially (Ollama doesn't support batch requests).
    Returns None for any text that fails to generate an embedding.

    Args:
        texts: List of texts to generate embeddings for

    Returns:
        List of embeddings (or None for failed generations)
    """
    embeddings = []
    for i, text in enumerate(texts):
        try:
            embedding = generate_embedding(text)
            embeddings.append(embedding)
            if embedding:
                logger.debug(f"Generated embedding {i+1}/{len(texts)}")
            else:
                logger.warning(f"Failed to generate embedding {i+1}/{len(texts)}")
        except Exception as e:
            logger.error(f"Error generating embedding {i+1}/{len(texts)}: {e}")
            embeddings.append(None)
    return embeddings
