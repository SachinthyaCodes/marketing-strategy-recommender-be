import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.models.sme_profile import SMEProfile
from app.models.strategy_model import MarketingStrategy
from app.services.strategy_service import generate_marketing_strategy
from app.services.realtime_service import auto_refresh_strategy
from app.services.calendar_service import auto_regenerate_calendar
from app.database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/strategy", tags=["Strategy"])


@router.post(
    "/generate",
    summary="Generate a marketing strategy",
    description="Accepts an SME profile and returns an AI-generated marketing strategy.",
    responses={
        422: {"description": "Validation or parsing error"},
        500: {"description": "Internal server error"},
        502: {"description": "LLM or service failure"},
        503: {"description": "Database connection error"},
    },
)
async def generate_strategy_endpoint(profile: SMEProfile) -> dict:
    """Generate a tailored marketing strategy for the given SME profile."""
    try:
        strategy, strategy_id = generate_marketing_strategy(profile)
        result = strategy.model_dump()
        result["strategy_id"] = strategy_id
        # Auto-regenerate calendar if one existed for this submission
        if strategy_id:
            try:
                auto_regenerate_calendar(strategy_id)
            except Exception as cal_exc:
                logger.warning("Calendar auto-regen failed (non-fatal): %s", cal_exc)
        return result
    except ValueError as exc:
        logger.warning("Validation/parsing error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Service error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ConnectionError as exc:
        logger.error("Database connection error: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)
        raise HTTPException(
            status_code=500, detail="Internal server error"
        ) from exc


@router.post(
    "/generate-version",
    summary="Generate a new strategy version from a stored strategy",
    description="Regenerates a strategy using the persisted SME profile — no form re-entry needed.",
)
async def generate_version_endpoint(body: dict) -> dict:
    """Create a new version of an existing strategy using its stored SME profile."""
    strategy_id = body.get("strategy_id")
    if not strategy_id:
        raise HTTPException(status_code=422, detail="strategy_id is required")
    try:
        result = auto_refresh_strategy(strategy_id, force_increment=True)
        # Shape the response the same way as /generate so the frontend can
        # handle it uniformly.
        new_strat = result["strategy"]
        new_strategy_id = result.get("new_strategy_id")
        new_strat["strategy_id"] = new_strategy_id
        # Auto-regenerate calendar for the new version
        if new_strategy_id:
            try:
                auto_regenerate_calendar(new_strategy_id)
            except Exception as cal_exc:
                logger.warning("Calendar auto-regen failed (non-fatal): %s", cal_exc)
        return new_strat
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Generate version error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get(
    "/versions",
    summary="List all strategy versions for a given strategy",
    description="Returns all versions stored under the same submission_id, newest first.",
)
async def list_versions_endpoint(strategy_id: str) -> dict:
    """Fetch all historical versions for the same SME profile run."""
    client = get_supabase_client()
    try:
        # Resolve submission_id from the given strategy row
        row = (
            client.table("strategies")
            .select("submission_id")
            .eq("id", strategy_id)
            .single()
            .execute()
        )
        if not row.data:
            raise HTTPException(status_code=404, detail="Strategy not found")

        submission_id = row.data["submission_id"]

        versions_result = (
            client.table("strategies")
            .select(
                "id, version, confidence_score, drift_level, drift_similarity, "
                "regenerate_flag, created_at, strategy_json, "
                "trend_recency_score, similarity_score, data_coverage_score, "
                "platform_stability_score, realtime_enabled, auto_updated_at"
            )
            .eq("submission_id", submission_id)
            .order("version", desc=True)
            .execute()
        )

        versions = []
        for v in (versions_result.data or []):
            sj = v.get("strategy_json") or {}
            versions.append({
                "strategy_id": v["id"],
                "version": v["version"],
                "confidence_score": v.get("confidence_score"),
                "drift_level": v.get("drift_level"),
                "drift_similarity": v.get("drift_similarity"),
                "regenerate_flag": v.get("regenerate_flag"),
                "created_at": v.get("created_at"),
                "auto_updated_at": v.get("auto_updated_at"),
                "realtime_enabled": v.get("realtime_enabled", False),
                "trend_recency_score": v.get("trend_recency_score"),
                "similarity_score": v.get("similarity_score"),
                "data_coverage_score": v.get("data_coverage_score"),
                "platform_stability_score": v.get("platform_stability_score"),
                "recommended_platforms": sj.get("recommended_platforms", []),
                "strategy_summary": sj.get("strategy_summary", ""),
            })

        return {"submission_id": submission_id, "versions": versions}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("List versions error: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch versions") from exc


@router.get(
    "/{strategy_id}",
    summary="Fetch a single strategy version by ID",
)
async def get_strategy_endpoint(strategy_id: str) -> dict:
    """Return the full strategy data for a specific version row."""
    client = get_supabase_client()
    try:
        row = (
            client.table("strategies")
            .select(
                "id, version, confidence_score, drift_level, drift_similarity, "
                "regenerate_flag, created_at, strategy_json, submission_id, "
                "trend_recency_score, similarity_score, data_coverage_score, "
                "platform_stability_score, realtime_enabled, auto_updated_at"
            )
            .eq("id", strategy_id)
            .single()
            .execute()
        )
        if not row.data:
            raise HTTPException(status_code=404, detail="Strategy not found")

        v = row.data
        sj = v.get("strategy_json") or {}
        return {
            "strategy_id": v["id"],
            "submission_id": v["submission_id"],
            "version": v["version"],
            "confidence_score": v.get("confidence_score"),
            "trend_recency_score": v.get("trend_recency_score"),
            "similarity_score": v.get("similarity_score"),
            "data_coverage_score": v.get("data_coverage_score"),
            "platform_stability_score": v.get("platform_stability_score"),
            "drift_level": v.get("drift_level"),
            "drift_similarity": v.get("drift_similarity"),
            "regenerate_flag": v.get("regenerate_flag"),
            "created_at": v.get("created_at"),
            "auto_updated_at": v.get("auto_updated_at"),
            "realtime_enabled": v.get("realtime_enabled", False),
            # Flatten strategy_json fields to top level (same shape as /generate)
            "strategy_summary": sj.get("strategy_summary", ""),
            "recommended_platforms": sj.get("recommended_platforms", []),
            "content_strategy": sj.get("content_strategy", ""),
            "budget_allocation": sj.get("budget_allocation", {}),
            "reasoning": sj.get("reasoning", ""),
            "is_outdated": sj.get("is_outdated", False),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Get strategy error: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch strategy") from exc
