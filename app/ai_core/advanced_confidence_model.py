"""Phase 5 — Advanced Non-LLM Confidence Scoring Model.

Replaces the Phase 4 simple confidence scorer with a multi-factor
computational model based purely on measurable, deterministic signals.

No LLM calls are involved — every component is a pure mathematical
function grounded in retrieval quality, temporal freshness, data
coverage, and platform stability metrics.

Research properties:
    1. **Deterministic** — identical inputs always yield identical scores.
    2. **Measurable** — each factor derives from a concrete, observable signal.
    3. **Transparent** — full breakdown is logged and returned.
    4. **Reproducible** — no randomness, no LLM variance.
    5. **Hybrid** — combines AI retrieval signals with rule-based heuristics.
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Weight configuration ──────────────────────────────────────────────
_W_TREND_RECENCY = 0.4
_W_SIMILARITY = 0.3
_W_DATA_COVERAGE = 0.2
_W_PLATFORM_STABILITY = 0.1

# ── Recency decay constant (days) ────────────────────────────────────
_RECENCY_HALFLIFE_DAYS = 30  # τ in exp(-age / τ)


@dataclass(frozen=True)
class ConfidenceBreakdown:
    """Immutable record of every factor contributing to the final score.

    Stored alongside the strategy for full research auditability.
    """

    trend_recency_score: float
    similarity_score: float
    data_coverage_score: float
    platform_stability_score: float
    final_confidence: float


class AdvancedConfidenceModel:
    """Multi-factor, non-LLM confidence scoring engine.

    Formula
    -------
    confidence = 0.4 × trend_recency_score
               + 0.3 × similarity_score
               + 0.2 × data_coverage_score
               + 0.1 × platform_stability_score

    Each component is independently clamped to [0, 1].
    The composite score is clamped and rounded to 3 decimal places.
    """

    # ── Public API ────────────────────────────────────────────────────

    @staticmethod
    def compute_confidence(
        trend_recency_score: float,
        similarity_score: float,
        data_coverage_score: float,
        platform_stability_score: float,
    ) -> ConfidenceBreakdown:
        """Compute the final weighted confidence and return a full breakdown.

        Args:
            trend_recency_score: Freshness signal (0–1).
            similarity_score: Mean retrieval cosine similarity (0–1).
            data_coverage_score: Ratio of retrieved docs to target (0–1).
            platform_stability_score: Platform count heuristic (0–1).

        Returns:
            ``ConfidenceBreakdown`` with every component and the final score.
        """
        # Clamp all inputs
        tr = AdvancedConfidenceModel._clamp(trend_recency_score)
        ss = AdvancedConfidenceModel._clamp(similarity_score)
        dc = AdvancedConfidenceModel._clamp(data_coverage_score)
        ps = AdvancedConfidenceModel._clamp(platform_stability_score)

        raw = (
            _W_TREND_RECENCY * tr
            + _W_SIMILARITY * ss
            + _W_DATA_COVERAGE * dc
            + _W_PLATFORM_STABILITY * ps
        )
        final = round(AdvancedConfidenceModel._clamp(raw), 3)

        breakdown = ConfidenceBreakdown(
            trend_recency_score=round(tr, 3),
            similarity_score=round(ss, 3),
            data_coverage_score=round(dc, 3),
            platform_stability_score=round(ps, 3),
            final_confidence=final,
        )

        # Structured research log
        logger.info(
            "Confidence Breakdown:\n"
            "  Trend Recency:      %.3f (%.0f%%)\n"
            "  Similarity:         %.3f (%.0f%%)\n"
            "  Coverage:           %.3f (%.0f%%)\n"
            "  Platform Stability: %.3f (%.0f%%)\n"
            "  Final Confidence:   %.3f",
            tr, _W_TREND_RECENCY * 100,
            ss, _W_SIMILARITY * 100,
            dc, _W_DATA_COVERAGE * 100,
            ps, _W_PLATFORM_STABILITY * 100,
            final,
        )

        return breakdown

    # ── Component scorers ─────────────────────────────────────────────

    @staticmethod
    def calculate_trend_recency(
        document_created_dates: list[datetime],
        reference_time: datetime | None = None,
    ) -> float:
        """Measure freshness of retrieved knowledge documents.

        For each document:
            age_in_days = (now − created_at).days

        Recency score = mean(exp(−age / 30))

        Returns:
            Score in [0, 1]. 1 → all documents are brand-new.
        """
        if not document_created_dates:
            return 0.0

        now = reference_time or datetime.now(timezone.utc)
        scores: list[float] = []
        for dt in document_created_dates:
            # Ensure timezone-aware comparison
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_days = max((now - dt).total_seconds() / 86_400, 0.0)
            scores.append(math.exp(-age_days / _RECENCY_HALFLIFE_DAYS))

        return AdvancedConfidenceModel._clamp(sum(scores) / len(scores))

    @staticmethod
    def calculate_similarity(similarity_values: list[float]) -> float:
        """Mean cosine similarity from RAG retrieval.

        Already provided by the RAG engine; this is a normalizing wrapper.
        """
        if not similarity_values:
            return 0.0
        mean_sim = sum(similarity_values) / len(similarity_values)
        return AdvancedConfidenceModel._clamp(mean_sim)

    @staticmethod
    def calculate_data_coverage(
        retrieved_docs_count: int,
        top_k: int = 5,
    ) -> float:
        """Ratio of documents actually retrieved vs. requested.

        coverage = min(retrieved / top_k, 1.0)
        """
        if top_k <= 0:
            return 0.0
        return AdvancedConfidenceModel._clamp(retrieved_docs_count / top_k)

    @staticmethod
    def calculate_platform_stability(
        recommended_platforms: list[str],
    ) -> float:
        """Heuristic stability score based on platform count.

        Logic:
            ≤ 3 platforms → 1.0  (focused strategy)
            > 3 platforms → max(0.5, 1 − (n − 3) × 0.1)  (penalise spread)
        """
        n = len(recommended_platforms)
        if n <= 3:
            return 1.0
        return AdvancedConfidenceModel._clamp(max(0.5, 1.0 - (n - 3) * 0.1))

    # ── Utility ───────────────────────────────────────────────────────

    @staticmethod
    def _clamp(value: float) -> float:
        """Clamp *value* to [0, 1]."""
        return max(0.0, min(1.0, value))
