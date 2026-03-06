"""Phase 6 — Embedding-Based Strategy Drift Detection.

Implements semantic drift detection by comparing the cosine similarity
between a stored strategy embedding and the latest context embedding.

Research definition
-------------------
    Strategy Drift = 1 − cosine_similarity(strategy_embedding, context_embedding)

    Threshold τ = 0.75

    similarity < τ  → strategy semantically outdated → regeneration required
    τ ≤ sim < τ+0.1 → moderate drift  → monitor, no regeneration yet
    sim ≥ τ+0.1     → low drift       → strategy still aligned

Design properties
-----------------
- Pure numpy cosine similarity — no sklearn.
- Deterministic — identical inputs always yield the same drift decision.
- Safe fallbacks for missing or mismatched embeddings.
- Fully unit-testable modular functions.
"""

import logging
from typing import TypedDict

import numpy as np

from app.ai_core.embedding_engine import generate_embedding

logger = logging.getLogger(__name__)

# ── Drift threshold constant ─────────────────────────────────────────
DRIFT_THRESHOLD: float = 0.75

# ── Drift level labels ───────────────────────────────────────────────
DRIFT_LOW = "LOW"
DRIFT_MODERATE = "MODERATE"
DRIFT_HIGH = "HIGH"


class DriftResult(TypedDict):
    """Structured result of a single drift detection evaluation."""

    similarity: float
    drift_level: str
    regenerate: bool


class DriftDetector:
    """Semantic drift detector using cosine similarity of embedding vectors.

    Responsibilities
    ----------------
    1. Compute cosine similarity (numpy, no sklearn).
    2. Generate a unified context embedding from query + retrieved docs.
    3. Produce a structured drift decision with level and regeneration flag.
    """

    # ──────────────────────────────────────────────────────────────────
    # Part 1 — Cosine Similarity
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two embedding vectors using numpy.

        Formula: similarity = dot(v1, v2) / (‖v1‖ · ‖v2‖)

        Args:
            vec1: First embedding (must be non-empty, same length as vec2).
            vec2: Second embedding (must be non-empty, same length as vec1).

        Returns:
            Cosine similarity rounded to 4 decimal places, in [-1, 1].

        Raises:
            ValueError: If vectors are empty or have different lengths.
        """
        if not vec1 or not vec2:
            raise ValueError("Embedding vectors must not be empty.")
        if len(vec1) != len(vec2):
            raise ValueError(
                f"Embedding length mismatch: {len(vec1)} vs {len(vec2)}. "
                "Both vectors must share the same dimensionality."
            )

        v1 = np.array(vec1, dtype=np.float64)
        v2 = np.array(vec2, dtype=np.float64)

        norm1 = float(np.linalg.norm(v1))
        norm2 = float(np.linalg.norm(v2))

        # Zero vector guard — no meaningful direction to compare
        if norm1 == 0.0 or norm2 == 0.0:
            logger.warning("Zero-magnitude vector encountered — returning similarity 0.")
            return 0.0

        raw = float(np.dot(v1, v2) / (norm1 * norm2))
        return round(float(np.clip(raw, -1.0, 1.0)), 4)

    # ──────────────────────────────────────────────────────────────────
    # Part 2 — Context Embedding Generation
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def generate_context_embedding(
        query_context: str,
        retrieved_documents: list[str],
    ) -> list[float]:
        """Build a unified embedding representing the latest market state.

        Concatenates the query context with all retrieved documents into a
        single summary string, then embeds it to capture the complete
        semantic context at inference time.

        Args:
            query_context: Semantic query derived from the SME profile.
            retrieved_documents: Knowledge base documents returned by RAG.

        Returns:
            384-dimensional normalised embedding vector.

        Raises:
            RuntimeError: If the embedding engine fails.
        """
        doc_block = " ".join(retrieved_documents) if retrieved_documents else ""
        combined = f"{query_context} {doc_block}".strip()

        logger.debug(
            "Generating context embedding from %d docs (combined length=%d).",
            len(retrieved_documents), len(combined),
        )
        return generate_embedding(combined)

    # ──────────────────────────────────────────────────────────────────
    # Part 3 — Drift Decision Logic
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def detect_drift(
        strategy_embedding: list[float],
        latest_context_embedding: list[float],
        threshold: float = DRIFT_THRESHOLD,
    ) -> DriftResult:
        """Evaluate semantic drift between a stored strategy and current context.

        Decision table (τ = threshold, default 0.75):
        ┌─────────────────────────────────────┬──────────┬─────────────┐
        │ Condition                           │  Level   │ Regenerate  │
        ├─────────────────────────────────────┼──────────┼─────────────┤
        │ similarity < τ                      │  HIGH    │    True     │
        │ τ ≤ similarity < τ + 0.1            │ MODERATE │    False    │
        │ similarity ≥ τ + 0.1                │  LOW     │    False    │
        └─────────────────────────────────────┴──────────┴─────────────┘

        Args:
            strategy_embedding: Stored embedding of the previous strategy.
            latest_context_embedding: Embedding of the current market context.
            threshold: Similarity floor below which drift is HIGH (default 0.75).

        Returns:
            DriftResult dict with 'similarity', 'drift_level', 'regenerate'.
        """
        similarity = DriftDetector.cosine_similarity(
            strategy_embedding, latest_context_embedding
        )

        if similarity < threshold:
            drift_level = DRIFT_HIGH
            regenerate = True
        elif similarity < threshold + 0.1:
            drift_level = DRIFT_MODERATE
            regenerate = False
        else:
            drift_level = DRIFT_LOW
            regenerate = False

        logger.info(
            "Drift Analysis:\n"
            "  Similarity:             %.4f\n"
            "  Threshold:              %.2f\n"
            "  Drift Level:            %s\n"
            "  Regeneration Required:  %s",
            similarity, threshold, drift_level, regenerate,
        )

        return DriftResult(
            similarity=similarity,
            drift_level=drift_level,
            regenerate=regenerate,
        )

    # ──────────────────────────────────────────────────────────────────
    # Convenience wrapper (backward-compat)
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def is_strategy_outdated(
        strategy_embedding: list[float],
        latest_context_embedding: list[float],
        threshold: float = DRIFT_THRESHOLD,
    ) -> bool:
        """Return True when drift is HIGH (similarity < threshold).

        Thin wrapper around ``detect_drift`` kept for backward compatibility
        with Phase 4 code paths.
        """
        result = DriftDetector.detect_drift(
            strategy_embedding, latest_context_embedding, threshold
        )
        return result["regenerate"]
