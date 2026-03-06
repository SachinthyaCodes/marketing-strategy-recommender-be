import json
import logging
import uuid
from dataclasses import dataclass

from app.ai_core.drift_detector import DRIFT_THRESHOLD, DriftDetector, DriftResult
from app.ai_core.embedding_engine import generate_embedding
from app.ai_core.strategy_generator import GenerationResult, StrategyGenerator
from app.database.supabase_client import get_supabase_client
from app.models.sme_profile import SMEProfile
from app.models.strategy_model import MarketingStrategy

logger = logging.getLogger(__name__)

_strategy_generator = StrategyGenerator()
_drift_detector = DriftDetector()


# ------------------------------------------------------------------
# Internal dataclass — versioning + drift combined result
# ------------------------------------------------------------------

@dataclass(frozen=True)
class _VersioningResult:
    """Outcome of drift detection and version resolution."""

    version: int
    is_outdated: bool
    drift_result: DriftResult | None   # None when no prior strategy exists


# ------------------------------------------------------------------
# Embedding helpers
# ------------------------------------------------------------------

def parse_embedding(value: str | list[float] | None) -> list[float] | None:
    """Parse an embedding returned by Supabase.

    pgvector columns come back as a comma-separated string like
    ``[-0.059,0.012,...,0.034]``.  This helper converts that to a
    proper ``list[float]`` so numpy/drift-detector can consume it.
    """
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [float(x) for x in parsed]
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return None


def _embed_strategy(strategy: MarketingStrategy) -> list[float] | None:
    """Generate an embedding from the strategy summary + reasoning."""
    try:
        text = strategy.strategy_summary + " " + strategy.reasoning
        return generate_embedding(text)
    except RuntimeError:
        logger.warning("Strategy embedding generation failed.")
        return None


# ------------------------------------------------------------------
# Versioning & drift
# ------------------------------------------------------------------

def _resolve_version(
    submission_id: uuid.UUID,
    strategy_embedding: list[float] | None,
    context_embedding: list[float] | None,
    force_increment: bool = False,
) -> _VersioningResult:
    """Run drift detection and determine the version for a new strategy.

    Steps:
        1. Fetch the latest strategy for the same submission_id.
        2. No prior record → version 1, no drift data.
        3. force_increment=True → always bump version (manual generation).
        4. Prior record found → call DriftDetector.detect_drift().
        5. HIGH drift (regenerate=True) → increment version, mark outdated.
        6. Otherwise → keep same version, not outdated.

    Returns:
        _VersioningResult with version, is_outdated, and drift metadata.
    """
    client = get_supabase_client()

    try:
        result = (
            client.table("strategies")
            .select("version, embedding")
            .eq("submission_id", str(submission_id))
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
    except Exception:
        logger.warning("Could not fetch previous strategies — defaulting to v1.")
        return _VersioningResult(version=1, is_outdated=False, drift_result=None)

    if not result.data:
        return _VersioningResult(version=1, is_outdated=False, drift_result=None)

    previous = result.data[0]
    prev_version = int(previous.get("version", 1))
    prev_embedding = parse_embedding(previous.get("embedding"))

    # Manual generation: always increment regardless of drift level.
    if force_increment:
        new_version = prev_version + 1
        logger.info("Force increment: bumping version %d → %d", prev_version, new_version)
        return _VersioningResult(version=new_version, is_outdated=False, drift_result=None)

    # Cannot compare without both embeddings
    if not prev_embedding or not context_embedding:
        logger.warning("Missing embeddings — bumping version without drift analysis.")
        return _VersioningResult(
            version=prev_version + 1,
            is_outdated=False,
            drift_result=None,
        )

    # Core Phase 6 drift detection
    drift: DriftResult = _drift_detector.detect_drift(
        strategy_embedding=prev_embedding,
        latest_context_embedding=context_embedding,
        threshold=DRIFT_THRESHOLD,
    )

    if drift["regenerate"]:
        new_version = prev_version + 1
        logger.info(
            "HIGH drift — bumping version %d → %d (similarity=%.4f)",
            prev_version, new_version, drift["similarity"],
        )
        return _VersioningResult(
            version=new_version,
            is_outdated=True,
            drift_result=drift,
        )

    logger.info(
        "Drift level=%s — keeping version %d (similarity=%.4f)",
        drift["drift_level"], prev_version, drift["similarity"],
    )
    return _VersioningResult(
        version=prev_version,
        is_outdated=False,
        drift_result=drift,
    )


# ------------------------------------------------------------------
# Storage
# ------------------------------------------------------------------

def _store_strategy(
    strategy: MarketingStrategy,
    submission_id: uuid.UUID,
    strategy_embedding: list[float] | None,
    sme_profile: SMEProfile | None = None,
) -> str | None:
    """Persist the strategy, its embedding, confidence breakdown, and drift metadata.

    Returns the database row ID of the inserted strategy, or None on failure.
    """
    client = get_supabase_client()

    record: dict = {
        "submission_id": str(submission_id),
        "strategy_json": strategy.model_dump(),
        "version": strategy.version,
    }
    if strategy_embedding is not None:
        record["embedding"] = strategy_embedding

    # Phase 5 — confidence breakdown
    record["confidence_score"] = strategy.confidence_score
    record["trend_recency_score"] = strategy.trend_recency_score
    record["similarity_score"] = strategy.similarity_score
    record["data_coverage_score"] = strategy.data_coverage_score
    record["platform_stability_score"] = strategy.platform_stability_score

    # Phase 6 — drift metadata
    record["drift_similarity"] = strategy.drift_similarity
    record["drift_level"] = strategy.drift_level
    record["regenerate_flag"] = strategy.regenerate_flag

    # Phase 7 — persist SME profile for auto-refresh
    if sme_profile is not None:
        record["sme_profile_json"] = sme_profile.model_dump()

    try:
        result = client.table("strategies").insert(record).execute()
        row_id = result.data[0]["id"] if result.data else None
        logger.info(
            "Strategy v%d stored for submission %s (confidence=%.3f, outdated=%s, id=%s)",
            strategy.version, submission_id,
            strategy.confidence_score, strategy.is_outdated, row_id,
        )
        return row_id
    except Exception as exc:
        logger.error("Failed to store strategy: %s", exc)
        raise RuntimeError(f"Database insert failed: {exc}") from exc


# ------------------------------------------------------------------
# Public orchestrator
# ------------------------------------------------------------------

def generate_marketing_strategy(
    sme_profile: SMEProfile,
    submission_id: uuid.UUID | None = None,
    force_increment: bool = False,
) -> tuple[MarketingStrategy, str | None]:
    """Orchestrate end-to-end strategy generation with RAG, confidence,
    drift detection, and versioning.

    Args:
        sme_profile: Comprehensive SME business profile.
        submission_id: Re-use an existing submission UUID so that versioning
            can find the previous strategy and increment the version number.
            Pass ``None`` (default) for brand-new generations.
        force_increment: Always bump the version number regardless of drift.
            Set True for manual "Generate New Version" calls.

    Returns:
        (strategy, strategy_id) — the enriched MarketingStrategy and the
        database row ID (None if persistence failed).
    """
    logger.info(
        "Generating strategy for '%s' (%s)",
        sme_profile.business_type,
        sme_profile.industry or "general",
    )

    # Step 1 — Core generation (RAG + LLM + advanced confidence scoring)
    gen_result: GenerationResult = _strategy_generator.generate(sme_profile)
    strategy = gen_result.strategy

    # Step 2 — Embed strategy text
    strategy_embedding = _embed_strategy(strategy)

    # Step 3 — Generate context embedding via Phase 6 DriftDetector
    try:
        context_embedding: list[float] | None = _drift_detector.generate_context_embedding(
            query_context=gen_result.query_context,
            retrieved_documents=gen_result.retrieval_result.documents,
        )
    except RuntimeError:
        logger.warning("Context embedding generation failed — skipping drift analysis.")
        context_embedding = None

    # Step 4 + 5 — Drift detection & version resolution
    # Reuse the caller-supplied submission_id (for auto-refresh) or mint a new one.
    if submission_id is None:
        submission_id = uuid.uuid4()
    versioning: _VersioningResult = _resolve_version(
        submission_id, strategy_embedding, context_embedding,
        force_increment=force_increment,
    )

    # Step 6 — Attach versioning and drift metadata to strategy
    strategy.version = versioning.version
    strategy.is_outdated = versioning.is_outdated

    if versioning.drift_result is not None:
        dr = versioning.drift_result
        strategy.drift_similarity = dr["similarity"]
        strategy.drift_level = dr["drift_level"]
        strategy.regenerate_flag = dr["regenerate"]
    else:
        strategy.drift_similarity = None
        strategy.drift_level = None
        strategy.regenerate_flag = None

    # Step 7 — Persist
    strategy_id = _store_strategy(strategy, submission_id, strategy_embedding, sme_profile=sme_profile)

    logger.info(
        "Strategy v%d complete — confidence=%.3f, drift=%s, regenerate=%s",
        strategy.version,
        strategy.confidence_score,
        strategy.drift_level or "N/A",
        strategy.regenerate_flag,
    )

    return strategy, strategy_id
