"""Phase 7 — Real-time Strategy Update Endpoints.

Provides endpoints for the real-time update system:

1. ``POST /toggle-realtime``   — Enable/disable per strategy
2. ``GET  /drift-check``       — Manual drift check
3. ``POST /force-refresh``     — Force regeneration from stored profile
4. ``POST /simulate-drift``    — [TEST] Inject knowledge + trigger full pipeline
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.realtime_service import (
    auto_refresh_strategy,
    check_drift_for_strategy,
    simulate_drift_and_refresh,
    toggle_realtime,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/realtime", tags=["Real-time Updates"])


# ── Request models ────────────────────────────────────────────────────────────

class ToggleRequest(BaseModel):
    strategy_id: str
    enabled: bool


class StrategyIdRequest(BaseModel):
    strategy_id: str


class SimulateDriftRequest(BaseModel):
    strategy_id: str
    knowledge_entries: list[dict] | None = None  # optional override knowledge to inject


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/toggle-realtime",
    summary="Enable or disable real-time updates for a strategy",
)
async def toggle_realtime_endpoint(req: ToggleRequest) -> dict:
    """Toggle real-time auto-refresh on or off for a given strategy."""
    try:
        result = toggle_realtime(req.strategy_id, req.enabled)
        return {
            "status": "success",
            "realtime_enabled": req.enabled,
            "strategy_id": req.strategy_id,
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Toggle error: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to toggle realtime") from exc


@router.get(
    "/drift-check",
    summary="Check drift for a specific strategy",
)
async def drift_check_endpoint(strategy_id: str) -> dict:
    """Run drift detection against the latest knowledge base for one strategy."""
    try:
        result = check_drift_for_strategy(strategy_id)
        return {"status": "success", **result}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Drift check error: %s", exc)
        raise HTTPException(status_code=500, detail="Drift check failed") from exc


@router.post(
    "/force-refresh",
    summary="Force-regenerate a strategy from its stored SME profile",
)
async def force_refresh_endpoint(req: StrategyIdRequest) -> dict:
    """Force strategy regeneration using the persisted SME profile."""
    try:
        result = auto_refresh_strategy(req.strategy_id)
        return {"status": "success", **result}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Refresh error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected refresh error: %s", exc)
        raise HTTPException(status_code=500, detail="Strategy refresh failed") from exc


@router.post(
    "/simulate-drift",
    summary="[TEST] Inject disruptive knowledge and trigger auto-regeneration",
    tags=["Real-time Updates", "Testing"],
)
async def simulate_drift_endpoint(req: SimulateDriftRequest) -> dict:
    """Development/testing endpoint.

    1. Injects disruptive knowledge entries into the knowledge base
       (or uses provided ones) to guarantee HIGH drift on the next check.
    2. Runs the full drift + auto-regeneration pipeline for the given strategy.
    3. Returns before/after comparison including real similarity score and
       the fully generated new strategy.

    Use this to verify the real-time pipeline end-to-end without waiting
    for n8n to trigger.
    """
    try:
        result = simulate_drift_and_refresh(
            strategy_id=req.strategy_id,
            extra_knowledge=req.knowledge_entries,
        )
        return {"status": "simulation_complete", **result}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Simulate drift error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected simulate drift error: %s", exc)
        raise HTTPException(status_code=500, detail="Simulation failed") from exc
