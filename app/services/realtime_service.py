"""Phase 7 — Real-time Strategy Update Service.

Handles drift checking and automatic strategy regeneration when new
knowledge arrives from the n8n workflow (triggers every 6 hours).

Pipeline
--------
1. n8n adds knowledge → POST /api/v1/knowledge/add
2. Post-ingest hook calls ``process_realtime_updates()``
3. For every strategy with ``realtime_enabled = True``:
   a. Fetch stored strategy embedding.
   b. Generate a fresh context embedding from the latest knowledge.
   c. Run drift detection.
   d. If HIGH drift → auto-regenerate using persisted ``sme_profile_json``.
   e. Update tracking timestamps.
"""

import logging
from datetime import datetime, timezone

from app.ai_core.drift_detector import DRIFT_THRESHOLD, DriftDetector, DriftResult
from app.ai_core.embedding_engine import generate_embedding
from app.ai_core.rag_engine import RAGEngine
from app.database.supabase_client import get_supabase_client
from app.models.sme_profile import SMEProfile
from app.services.strategy_service import generate_marketing_strategy, parse_embedding

logger = logging.getLogger(__name__)

_drift_detector = DriftDetector()
_rag_engine = RAGEngine()


# ------------------------------------------------------------------
# Toggle
# ------------------------------------------------------------------

def toggle_realtime(strategy_id: str, enabled: bool) -> dict:
    """Enable or disable real-time updates for a strategy row.

    Returns the updated record fragment.
    """
    client = get_supabase_client()
    result = (
        client.table("strategies")
        .update({"realtime_enabled": enabled})
        .eq("id", strategy_id)
        .execute()
    )
    if not result.data:
        raise ValueError(f"Strategy {strategy_id} not found")
    logger.info("Realtime %s for strategy %s", "enabled" if enabled else "disabled", strategy_id)
    return result.data[0]


# ------------------------------------------------------------------
# Drift check for a single strategy
# ------------------------------------------------------------------

def check_drift_for_strategy(strategy_id: str) -> dict:
    """Run drift detection against the latest knowledge for one strategy.

    Returns a dict with drift_level, similarity, regenerate flag, and
    the updated last_drift_check timestamp.
    """
    client = get_supabase_client()

    # 1. Fetch strategy row (embedding + strategy_json for query context)
    row = (
        client.table("strategies")
        .select("id, submission_id, embedding, strategy_json, sme_profile_json, created_at")
        .eq("id", strategy_id)
        .single()
        .execute()
    )
    if not row.data:
        raise ValueError(f"Strategy {strategy_id} not found")

    strategy_data = row.data
    strategy_embedding = parse_embedding(strategy_data.get("embedding"))

    if not strategy_embedding:
        raise ValueError("Strategy has no embedding — cannot perform drift check")

    # 2. Build a query from the stored strategy to retrieve latest knowledge
    strategy_json = strategy_data.get("strategy_json", {})
    query = strategy_json.get("strategy_summary", "") + " " + strategy_json.get("reasoning", "")

    # 3. Retrieve latest knowledge context via RAG
    retrieval = _rag_engine.retrieve_context(query.strip(), top_k=5)

    # 4. Generate context embedding from latest knowledge
    context_embedding = _drift_detector.generate_context_embedding(
        query_context=query.strip(),
        retrieved_documents=retrieval.documents,
    )

    # 5. Detect drift
    drift: DriftResult = _drift_detector.detect_drift(
        strategy_embedding=strategy_embedding,
        latest_context_embedding=context_embedding,
        threshold=DRIFT_THRESHOLD,
    )

    # 6. Update tracking columns
    now = datetime.now(timezone.utc).isoformat()
    client.table("strategies").update({
        "last_drift_check": now,
        "drift_similarity": drift["similarity"],
        "drift_level": drift["drift_level"],
        "regenerate_flag": drift["regenerate"],
    }).eq("id", strategy_id).execute()

    logger.info(
        "Drift check for %s: level=%s, similarity=%.4f, regenerate=%s",
        strategy_id, drift["drift_level"], drift["similarity"], drift["regenerate"],
    )

    # 7. Check if a newer strategy was already auto-generated (by background batch)
    #    This happens when n8n triggers process_realtime_updates() and auto_refresh
    #    created a new version while the frontend was still polling the old one.
    auto_refreshed = None
    try:
        newer = (
            client.table("strategies")
            .select("id, strategy_json, version, confidence_score, drift_level, "
                     "drift_similarity, regenerate_flag, trend_recency_score, "
                     "similarity_score, data_coverage_score, platform_stability_score")
            .eq("realtime_enabled", True)
            .gt("created_at", row.data.get("created_at", "1970-01-01"))
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if newer.data and newer.data[0]["id"] != strategy_id:
            n = newer.data[0]
            sj = n.get("strategy_json", {})
            auto_refreshed = {
                "new_strategy_id": n["id"],
                "strategy": {
                    "strategy_summary": sj.get("strategy_summary", ""),
                    "recommended_platforms": sj.get("recommended_platforms", []),
                    "content_strategy": sj.get("content_strategy", ""),
                    "budget_allocation": sj.get("budget_allocation", {}),
                    "reasoning": sj.get("reasoning", ""),
                    "confidence_score": n.get("confidence_score", 0),
                    "version": n.get("version", 1),
                    "is_outdated": sj.get("is_outdated", False),
                    "trend_recency_score": n.get("trend_recency_score"),
                    "similarity_score": n.get("similarity_score"),
                    "data_coverage_score": n.get("data_coverage_score"),
                    "platform_stability_score": n.get("platform_stability_score"),
                    "drift_similarity": n.get("drift_similarity"),
                    "drift_level": n.get("drift_level"),
                    "regenerate_flag": n.get("regenerate_flag"),
                    "strategy_id": n["id"],
                },
            }
    except Exception as exc:
        logger.debug("Auto-refresh successor check failed (non-fatal): %s", exc)

    return {
        "strategy_id": strategy_id,
        "drift_level": drift["drift_level"],
        "similarity": drift["similarity"],
        "regenerate": drift["regenerate"],
        "last_drift_check": now,
        "auto_refreshed": auto_refreshed,
    }


# ------------------------------------------------------------------
# Auto-refresh a single strategy
# ------------------------------------------------------------------

def auto_refresh_strategy(strategy_id: str, force_increment: bool = False) -> dict:
    """Regenerate a strategy using its persisted SME profile.

    Args:
        strategy_id: The strategy row to regenerate from.
        force_increment: Always bump the version number (True for manual
            "Generate New Version" clicks; False for automatic drift-triggered
            refreshes which only bump on HIGH drift).
    """
    client = get_supabase_client()

    # 1. Fetch persisted profile + original submission_id for correct versioning
    row = (
        client.table("strategies")
        .select("id, submission_id, sme_profile_json, realtime_enabled")
        .eq("id", strategy_id)
        .single()
        .execute()
    )
    if not row.data:
        raise ValueError(f"Strategy {strategy_id} not found")

    profile_json = row.data.get("sme_profile_json")
    if not profile_json:
        raise ValueError(
            "No SME profile stored on this strategy — cannot auto-refresh. "
            "Regenerate manually from the form."
        )

    # 2. Reconstruct profile and generate new strategy.
    #    Pass the ORIGINAL submission_id so _resolve_version() finds the previous
    #    strategy in the DB and increments the version number (v1 → v2 → v3 ...).
    import uuid as _uuid
    original_submission_id = _uuid.UUID(row.data["submission_id"])
    sme_profile = SMEProfile(**profile_json)
    new_strategy, new_strategy_id = generate_marketing_strategy(
        sme_profile,
        submission_id=original_submission_id,
        force_increment=force_increment,
    )

    # 3. Update the NEWLY created strategy row to carry over realtime settings
    now = datetime.now(timezone.utc).isoformat()
    if new_strategy_id:
        client.table("strategies").update({
            "realtime_enabled": row.data.get("realtime_enabled", False),
            "sme_profile_json": profile_json,
            "auto_updated_at": now,
        }).eq("id", new_strategy_id).execute()

    # Disable realtime on the OLD strategy so only the latest is active
    client.table("strategies").update({
        "realtime_enabled": False,
    }).eq("id", strategy_id).execute()

    logger.info(
        "Auto-refresh completed for strategy %s → new version v%d (confidence=%.3f)",
        strategy_id, new_strategy.version, new_strategy.confidence_score,
    )

    return {
        "previous_strategy_id": strategy_id,
        "new_strategy_id": new_strategy_id,
        "version": new_strategy.version,
        "confidence_score": new_strategy.confidence_score,
        "drift_level": new_strategy.drift_level,
        "strategy": new_strategy.model_dump(),
    }


# ------------------------------------------------------------------
# Batch processor — called after knowledge ingestion
# ------------------------------------------------------------------

def process_realtime_updates() -> dict:
    """Check drift for ALL realtime-enabled strategies and auto-refresh
    those with HIGH drift.

    Called automatically after new knowledge is added to the knowledge base.
    Returns a summary of what happened.
    """
    client = get_supabase_client()

    # Find all strategies with realtime enabled
    result = (
        client.table("strategies")
        .select("id, submission_id")
        .eq("realtime_enabled", True)
        .execute()
    )

    strategies = result.data or []
    if not strategies:
        logger.info("No realtime-enabled strategies to check.")
        return {"checked": 0, "refreshed": 0, "details": []}

    logger.info("Processing realtime updates for %d strategies.", len(strategies))

    checked = 0
    refreshed = 0
    details = []

    for s in strategies:
        sid = s["id"]
        try:
            drift_result = check_drift_for_strategy(sid)
            checked += 1

            if drift_result["regenerate"]:
                refresh_result = auto_refresh_strategy(sid)
                refreshed += 1
                details.append({
                    "strategy_id": sid,
                    "action": "refreshed",
                    "new_version": refresh_result["version"],
                    "drift_level": drift_result["drift_level"],
                })
            else:
                details.append({
                    "strategy_id": sid,
                    "action": "checked",
                    "drift_level": drift_result["drift_level"],
                    "similarity": drift_result["similarity"],
                })
        except Exception as exc:
            logger.error("Error processing strategy %s: %s", sid, exc)
            details.append({
                "strategy_id": sid,
                "action": "error",
                "error": str(exc),
            })

    logger.info("Realtime batch complete: checked=%d, refreshed=%d", checked, refreshed)

    return {
        "checked": checked,
        "refreshed": refreshed,
        "details": details,
    }


# ------------------------------------------------------------------
# Test / Simulation helper
# ------------------------------------------------------------------

# Default disruptive knowledge entries — these contradict typical construction
# social-media strategies so they maximally shift the context embedding.
_DISRUPTIVE_KNOWLEDGE: list[dict] = [
    {
        "content": (
            "2025 Sri Lanka SME Report: Facebook and Instagram ad costs have increased 340% "
            "year-on-year. Construction and trade businesses are abandoning social media ads "
            "entirely in favour of Google My Business, WhatsApp Business broadcast lists, and "
            "local Sinhala-language YouTube tutorials. ROI from traditional social platforms "
            "has dropped below 5% for B2C construction queries."
        ),
        "source_type": "research",
        "platform": "Google My Business",
        "industry": "Construction",
    },
    {
        "content": (
            "Emerging trend 2025: Voice search and AI-assisted procurement now drives 60% of "
            "construction material purchases in Colombo district. SMEs that optimise for "
            "Google Business Profile questions and WhatsApp catalogues see 4x more qualified "
            "leads than those running Facebook/Instagram campaigns. TikTok has near-zero "
            "conversion for building-trade services in Sri Lanka."
        ),
        "source_type": "case_study",
        "platform": "WhatsApp Business",
        "industry": "Construction",
    },
    {
        "content": (
            "Sri Lanka digital marketing shift Q1 2026: Platform algorithm changes have made "
            "organic reach on Facebook drop to under 1% for service businesses. LinkedIn has "
            "surpassed Instagram as the top lead-generation channel for B2B construction "
            "contractors. Email newsletters to past clients now outperform paid social ads "
            "3-to-1 in client retention for trade SMEs nationwide."
        ),
        "source_type": "article",
        "platform": "LinkedIn",
        "industry": "Construction",
    },
    {
        "content": (
            "Budget reallocation insight: Construction SMEs in Maharagama and Colombo suburbs "
            "that shifted 70% of their marketing budget from social media to local SEO and "
            "Google Ads reported 2.5x increase in project inquiries. Monthly budget below "
            "LKR 100,000 is now recommended to go entirely towards Google Ads + WhatsApp "
            "Business rather than Facebook/Instagram due to saturation and rising CPM costs."
        ),
        "source_type": "research",
        "platform": "Google Ads",
        "industry": "Construction",
    },
]


def simulate_drift_and_refresh(
    strategy_id: str,
    extra_knowledge: list[dict] | None = None,
) -> dict:
    """[TEST] Inject disruptive knowledge + run the full drift-and-refresh pipeline.

    Steps:
      1. Fetch the current strategy so we can compare before/after.
      2. Inject disruptive knowledge entries into the knowledge base to ensure
         the context embedding shifts dramatically away from the stored strategy.
      3. Run ``check_drift_for_strategy()`` with the real algorithm — this will
         now return HIGH drift because of the injected knowledge.
      4. Call ``auto_refresh_strategy()`` to regenerate using stored SME profile.
      5. Return full before/after details for inspection.

    Args:
        strategy_id: The strategy to test against.
        extra_knowledge: Optional list of custom knowledge dicts to inject
                         (each must have ``content``, ``source_type`` keys).
                         Defaults to _DISRUPTIVE_KNOWLEDGE if not provided.

    Returns:
        dict with keys: before_strategy, drift_result, after_strategy,
        injected_count, similarity_before (N/A), similarity_after.
    """
    from app.services.knowledge_service import add_knowledge_entry  # avoid circular

    client = get_supabase_client()

    # 1. Snapshot current strategy
    row = (
        client.table("strategies")
        .select("id, version, strategy_json, confidence_score, drift_level, realtime_enabled")
        .eq("id", strategy_id)
        .single()
        .execute()
    )
    if not row.data:
        raise ValueError(f"Strategy {strategy_id} not found")

    before = row.data
    before_sj = before.get("strategy_json", {})

    # 2. Inject disruptive / custom knowledge
    entries_to_inject = extra_knowledge or _DISRUPTIVE_KNOWLEDGE
    injected_ids = []
    for entry in entries_to_inject:
        try:
            result = add_knowledge_entry(
                content=entry["content"],
                source_type=entry.get("source_type", "article"),
                platform=entry.get("platform"),
                industry=entry.get("industry"),
            )
            injected_ids.append(result.get("id"))
        except Exception as exc:
            logger.warning("Failed to inject knowledge entry: %s", exc)

    logger.info("Injected %d disruptive knowledge entries.", len(injected_ids))

    # 3. Run real drift check (will detect HIGH drift due to new knowledge)
    drift_result = check_drift_for_strategy(strategy_id)

    logger.info(
        "Simulation drift check: level=%s, similarity=%.4f, regenerate=%s",
        drift_result["drift_level"], drift_result["similarity"], drift_result["regenerate"],
    )

    # 4. Trigger auto-refresh (regenerate from persisted SME profile)
    refresh_result = auto_refresh_strategy(strategy_id)

    after_sj = refresh_result["strategy"]

    return {
        "injected_knowledge_count": len(injected_ids),
        "drift_result": {
            "similarity_score": drift_result["similarity"],
            "drift_level": drift_result["drift_level"],
            "regenerate_triggered": drift_result["regenerate"],
        },
        "before": {
            "strategy_id": strategy_id,
            "version": before.get("version"),
            "confidence_score": before.get("confidence_score"),
            "drift_level": before.get("drift_level"),
            "summary_preview": before_sj.get("strategy_summary", "")[:200],
            "platforms": before_sj.get("recommended_platforms", []),
        },
        "after": {
            "strategy_id": refresh_result.get("new_strategy_id"),
            "version": refresh_result.get("version"),
            "confidence_score": refresh_result.get("confidence_score"),
            "drift_level": after_sj.get("drift_level"),
            "summary_preview": after_sj.get("strategy_summary", "")[:200],
            "platforms": after_sj.get("recommended_platforms", []),
            "full_strategy": after_sj,
        },
    }
