import logging
import threading

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None
_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    """Return the singleton SentenceTransformer model, loading it on first call.

    Thread-safe via a lock to prevent duplicate model loads during
    concurrent startup requests.

    Returns:
        Loaded SentenceTransformer model instance.
    """
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                logger.info("Loading embedding model: %s", MODEL_NAME)
                _model = SentenceTransformer(MODEL_NAME)
                logger.info("Embedding model loaded successfully.")
    return _model


def generate_embedding(text: str) -> list[float]:
    """Generate a normalized embedding vector for the given text.

    Args:
        text: Input text to embed.

    Returns:
        List of floats representing the normalized embedding.

    Raises:
        ValueError: If input text is empty.
        RuntimeError: If embedding generation fails.
    """
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text.")

    model = _get_model()

    try:
        embedding = model.encode(text, convert_to_numpy=True)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding.tolist()
    except Exception as exc:
        logger.error("Embedding generation failed: %s", exc)
        raise RuntimeError(f"Embedding generation failed: {exc}") from exc


def get_embedding_dimension() -> int:
    """Return the dimensionality of the loaded embedding model.

    Returns:
        Integer dimension of the embedding vectors (384 for all-MiniLM-L6-v2).
    """
    model = _get_model()
    return model.get_sentence_embedding_dimension()
