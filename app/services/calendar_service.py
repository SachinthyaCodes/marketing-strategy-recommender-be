"""Calendar action-plan service.

Generates a day-by-day marketing action plan from a stored strategy,
persists it to Supabase, and auto-regenerates when the strategy changes.
"""

import json
import logging
import uuid
from datetime import date, timedelta

from app.ai_core.groq_client import generate_strategy as call_llm
from app.database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# ── Time-range mapping ────────────────────────────────────────────────────────

TIME_RANGE_DAYS: dict[str, int] = {
    "1_week": 7,
    "2_weeks": 14,
    "1_month": 30,
    "2_months": 60,
    "3_months": 90,
}

DEFAULT_TIME_RANGE = "1_month"


# ── LLM prompt builder ───────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a senior marketing strategist who creates practical, day-by-day "
    "marketing action plans. You understand social media best practices, content "
    "creation workflows, and Sri Lankan market dynamics. You always return ONLY "
    "valid JSON without any markdown formatting or code fences."
)


def _build_calendar_prompt(
    strategy_json: dict,
    sme_profile_json: dict | None,
    start_date: date,
    num_days: int,
) -> str:
    """Build a prompt that asks the LLM for a concrete daily action plan."""

    platforms = strategy_json.get("recommended_platforms", [])
    summary = strategy_json.get("strategy_summary", "")
    content_strategy = strategy_json.get("content_strategy", "")
    budget = strategy_json.get("budget_allocation", {})
    reasoning = strategy_json.get("reasoning", "")

    # Pull business context if available
    biz_type = ""
    industry = ""
    goals = ""
    if sme_profile_json:
        biz_type = sme_profile_json.get("business_type", "")
        industry = sme_profile_json.get("industry", "")
        goals = sme_profile_json.get("primary_goal", "")

    end_date = start_date + timedelta(days=num_days - 1)

    return f"""Based on the following marketing strategy, create a detailed day-by-day
marketing action plan from {start_date.isoformat()} to {end_date.isoformat()} ({num_days} days).

=== BUSINESS CONTEXT ===
Business Type: {biz_type}
Industry: {industry}
Primary Goal: {goals}

=== MARKETING STRATEGY ===
Summary: {summary}

Content Strategy: {content_strategy}

Recommended Platforms: {', '.join(platforms)}

Budget Allocation: {json.dumps(budget)}

Strategy Reasoning: {reasoning}

=== INSTRUCTIONS ===
1. Create one actionable task per day (or skip rest days with a lighter task).
2. Spread tasks evenly across the recommended platforms: {', '.join(platforms)}.
3. Mix content types: images, reels/videos, stories, carousels, text posts, polls, etc.
4. Include specific campaign ideas, captions topics, and objectives for each day.
5. Suggest best posting times.
6. Mark any festive / seasonal days relevant to Sri Lanka if they fall in the range.
7. Make tasks practical — things a small business owner can actually do.

Return a JSON array (no markdown, no code fences) with exactly {num_days} objects:
[
  {{
    "date": "YYYY-MM-DD",
    "day_label": "Day 1 - Monday",
    "platform": "Instagram",
    "content_type": "Reel",
    "title": "Short catchy title",
    "description": "2-3 sentence description of what to create and post",
    "objective": "Engagement|Awareness|Sales|Community",
    "best_time": "19:00",
    "tags": ["tag1", "tag2"]
  }},
  ...
]

Return ONLY the JSON array. No other text."""


# ── Core generation ──────────────────────────────────────────────────────────

def _parse_plan_json(raw_text: str) -> list[dict]:
    """Extract the JSON array from the LLM response, stripping markdown fences."""
    text = raw_text.strip()
    # Strip ```json ... ``` wrappers if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (``` markers)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        plan = json.loads(text)
        if isinstance(plan, list):
            return plan
    except json.JSONDecodeError:
        # Try to find the array within the text
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
    raise ValueError("Failed to parse calendar plan from LLM response")


def generate_calendar_plan(
    strategy_id: str,
    time_range: str = DEFAULT_TIME_RANGE,
    start_date_str: str | None = None,
) -> dict:
    """Generate a calendar action plan for the given strategy.

    Args:
        strategy_id: UUID of the strategy row.
        time_range: One of ``TIME_RANGE_DAYS`` keys.
        start_date_str: Optional ISO date string for the start date.
            Defaults to tomorrow.

    Returns:
        The full calendar_plans row as a dict.
    """
    if time_range not in TIME_RANGE_DAYS:
        raise ValueError(
            f"Invalid time_range '{time_range}'. "
            f"Choose from: {', '.join(TIME_RANGE_DAYS.keys())}"
        )

    num_days = TIME_RANGE_DAYS[time_range]
    plan_start = (
        date.fromisoformat(start_date_str)
        if start_date_str
        else date.today() + timedelta(days=1)
    )

    client = get_supabase_client()

    # Fetch the strategy + SME profile
    row = (
        client.table("strategies")
        .select("id, submission_id, strategy_json, sme_profile_json")
        .eq("id", strategy_id)
        .single()
        .execute()
    )
    if not row.data:
        raise ValueError(f"Strategy {strategy_id} not found")

    strategy_json = row.data.get("strategy_json", {})
    sme_profile_json = row.data.get("sme_profile_json")
    submission_id = row.data["submission_id"]

    # Build prompt & call LLM
    prompt = _build_calendar_prompt(strategy_json, sme_profile_json, plan_start, num_days)
    raw_response = call_llm(prompt, system_prompt=_SYSTEM_PROMPT)
    plan_items = _parse_plan_json(raw_response)

    plan_end = plan_start + timedelta(days=num_days - 1)

    # Persist to Supabase
    record = {
        "strategy_id": strategy_id,
        "submission_id": submission_id,
        "time_range": time_range,
        "plan_json": plan_items,
        "total_tasks": len(plan_items),
        "start_date": plan_start.isoformat(),
        "end_date": plan_end.isoformat(),
        "auto_generated": False,
    }

    result = client.table("calendar_plans").insert(record).execute()
    if not result.data:
        raise RuntimeError("Failed to store calendar plan")

    stored = result.data[0]
    logger.info(
        "Calendar plan created: %s (%s, %d tasks, %s → %s)",
        stored["id"], time_range, len(plan_items),
        plan_start.isoformat(), plan_end.isoformat(),
    )
    return stored


# ── Fetch latest calendar for a strategy ─────────────────────────────────────

def get_latest_calendar(strategy_id: str) -> dict | None:
    """Return the most recent calendar plan for the given strategy, or None."""
    client = get_supabase_client()
    result = (
        client.table("calendar_plans")
        .select("*")
        .eq("strategy_id", strategy_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_calendar_by_id(calendar_id: str) -> dict | None:
    """Fetch a specific calendar plan by its row ID."""
    client = get_supabase_client()
    result = (
        client.table("calendar_plans")
        .select("*")
        .eq("id", calendar_id)
        .single()
        .execute()
    )
    return result.data if result.data else None


def list_calendars_for_submission(submission_id: str) -> list[dict]:
    """Return all calendar plans for a submission, newest first."""
    client = get_supabase_client()
    result = (
        client.table("calendar_plans")
        .select("id, strategy_id, time_range, total_tasks, start_date, end_date, created_at, auto_generated")
        .eq("submission_id", submission_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


# ── Auto-regeneration (called when strategy changes) ─────────────────────────

def auto_regenerate_calendar(strategy_id: str) -> dict | None:
    """Check if a calendar existed for the previous version of this strategy's
    submission and, if so, regenerate it with the same time range.

    Called automatically after a new strategy version is generated.
    """
    client = get_supabase_client()

    # Get the submission_id for this strategy
    strat_row = (
        client.table("strategies")
        .select("submission_id")
        .eq("id", strategy_id)
        .single()
        .execute()
    )
    if not strat_row.data:
        return None

    submission_id = strat_row.data["submission_id"]

    # Find the most recent calendar for this submission (from any strategy version)
    prev_cal = (
        client.table("calendar_plans")
        .select("time_range")
        .eq("submission_id", submission_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not prev_cal.data:
        logger.info("No previous calendar for submission %s — skipping auto-regen.", submission_id)
        return None

    prev_time_range = prev_cal.data[0].get("time_range", DEFAULT_TIME_RANGE)
    logger.info(
        "Auto-regenerating calendar for strategy %s (time_range=%s)",
        strategy_id, prev_time_range,
    )

    # Generate new calendar linked to the new strategy version
    plan = generate_calendar_plan(strategy_id, time_range=prev_time_range)
    # Mark as auto-generated
    client.table("calendar_plans").update({"auto_generated": True}).eq("id", plan["id"]).execute()
    plan["auto_generated"] = True
    return plan
