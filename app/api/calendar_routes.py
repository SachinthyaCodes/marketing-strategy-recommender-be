"""Calendar action-plan REST endpoints."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.calendar_service import (
    TIME_RANGE_DAYS,
    generate_calendar_plan,
    get_calendar_by_id,
    get_latest_calendar,
    list_calendars_for_submission,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/calendar", tags=["Calendar"])


# ── Request bodies ────────────────────────────────────────────────────────────

class GenerateCalendarRequest(BaseModel):
    strategy_id: str = Field(..., description="UUID of the strategy to create the plan for")
    time_range: str = Field(default="1_month", description="1_week | 2_weeks | 1_month | 2_months | 3_months")
    start_date: str | None = Field(default=None, description="ISO date for plan start (defaults to tomorrow)")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/generate",
    summary="Generate a calendar action plan from a strategy",
    description=(
        "Uses the AI engine to build a day-by-day marketing action plan "
        "based on the specified strategy. The plan is persisted and can be "
        "fetched later."
    ),
)
async def generate_calendar_endpoint(body: GenerateCalendarRequest) -> dict:
    try:
        plan = generate_calendar_plan(
            strategy_id=body.strategy_id,
            time_range=body.time_range,
            start_date_str=body.start_date,
        )
        return plan
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Calendar generation error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected calendar error: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get(
    "/time-ranges",
    summary="List available time range options",
)
async def list_time_ranges() -> dict:
    return {
        "time_ranges": [
            {"value": k, "label": _label(k), "days": v}
            for k, v in TIME_RANGE_DAYS.items()
        ]
    }


@router.get(
    "/latest",
    summary="Get the latest calendar plan for a strategy",
)
async def get_latest_calendar_endpoint(strategy_id: str) -> dict:
    try:
        plan = get_latest_calendar(strategy_id)
    except Exception as exc:
        logger.warning("Could not fetch latest calendar: %s", exc)
        return {"calendar": None}
    if not plan:
        return {"calendar": None}
    return {"calendar": plan}


@router.get(
    "/list",
    summary="List all calendar plans for a submission",
)
async def list_calendars_endpoint(submission_id: str) -> dict:
    calendars = list_calendars_for_submission(submission_id)
    return {"calendars": calendars}


@router.get(
    "/{calendar_id}",
    summary="Fetch a specific calendar plan by ID",
)
async def get_calendar_endpoint(calendar_id: str) -> dict:
    plan = get_calendar_by_id(calendar_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Calendar plan not found")
    return plan


def _label(key: str) -> str:
    labels = {
        "1_week": "1 Week",
        "2_weeks": "2 Weeks",
        "1_month": "1 Month",
        "2_months": "2 Months",
        "3_months": "3 Months",
    }
    return labels.get(key, key)
