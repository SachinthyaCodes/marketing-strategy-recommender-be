import logging

logger = logging.getLogger(__name__)

# Weighted contribution of each signal to final confidence.
_W_SIMILARITY = 0.4
_W_COVERAGE = 0.2
_W_DEPTH = 0.2
_W_BUDGET = 0.2

# Normalization targets.
_COVERAGE_TARGET = 5      # ideal number of retrieved documents
_DEPTH_TARGET = 800        # ideal strategy text length (chars)


class ConfidenceScorer:
    """Deterministic, mathematical confidence scoring for generated strategies.

    Replaces the LLM's self-reported confidence with a reproducible
    weighted formula grounded in measurable retrieval and output signals.
    """

    @staticmethod
    def calculate_confidence(
        retrieval_similarity_scores: list[float],
        num_documents: int,
        strategy_length: int,
        budget_allocation: dict[str, float],
    ) -> float:
        """Compute a weighted confidence score for a marketing strategy.

        Formula:
            confidence = 0.4 * avg_similarity
                       + 0.2 * document_coverage_score
                       + 0.2 * strategy_depth_score
                       + 0.2 * budget_alignment_score

        Args:
            retrieval_similarity_scores: Cosine similarity scores from RAG.
            num_documents: Number of knowledge documents retrieved.
            strategy_length: Character length of the strategy text.
            budget_allocation: Platform → percentage mapping from the strategy.

        Returns:
            Confidence score clamped to [0, 1], rounded to 3 decimals.
        """
        avg_sim = ConfidenceScorer._avg_similarity(retrieval_similarity_scores)
        coverage = ConfidenceScorer._document_coverage(num_documents)
        depth = ConfidenceScorer._strategy_depth(strategy_length)
        budget_align = ConfidenceScorer._budget_alignment(budget_allocation)

        raw = (
            _W_SIMILARITY * avg_sim
            + _W_COVERAGE * coverage
            + _W_DEPTH * depth
            + _W_BUDGET * budget_align
        )
        confidence = round(max(0.0, min(1.0, raw)), 3)

        logger.info(
            "Confidence components — sim=%.3f cov=%.3f depth=%.3f budget=%.3f → %.3f",
            avg_sim, coverage, depth, budget_align, confidence,
        )
        return confidence

    # ------------------------------------------------------------------
    # Component scores
    # ------------------------------------------------------------------

    @staticmethod
    def _avg_similarity(scores: list[float]) -> float:
        """Mean of retrieval similarity scores, or 0 if none."""
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    @staticmethod
    def _document_coverage(num_documents: int) -> float:
        """Ratio of documents retrieved vs. target, capped at 1.0."""
        return min(num_documents / _COVERAGE_TARGET, 1.0)

    @staticmethod
    def _strategy_depth(strategy_length: int) -> float:
        """Ratio of strategy text length vs. depth target, capped at 1.0."""
        return min(strategy_length / _DEPTH_TARGET, 1.0)

    @staticmethod
    def _budget_alignment(budget_allocation: dict[str, float]) -> float:
        """Score how close budget percentages sum to 100%.

        Returns 1.0 when the sum equals 100; penalizes proportionally
        as the sum deviates.
        """
        if not budget_allocation:
            return 0.0
        total = sum(budget_allocation.values())
        deviation = abs(total - 100.0)
        return max(0.0, 1.0 - deviation / 100.0)
