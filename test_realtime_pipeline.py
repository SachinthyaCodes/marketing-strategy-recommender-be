"""
Real-time Strategy Regeneration — End-to-End Test Script
=========================================================

Tests the full pipeline:
  1. POST /api/v1/realtime/simulate-drift  (injects disruptive knowledge + auto-regenerates)
  2. GET  /api/v1/realtime/drift-check     (verifies drift status on old strategy shows HIGH)
  3. Inspect before/after strategy differences

Usage
-----
  # Make sure the backend is running (uvicorn app.main:app --reload)
  python test_realtime_pipeline.py <strategy_id>

  # Optionally pass custom API base:
  python test_realtime_pipeline.py <strategy_id> --base http://localhost:8000

How to get your strategy_id
----------------------------
  1. Open browser DevTools → Application → Local Storage → http://localhost:3000
  2. Find key "strategy_result" → copy the "strategy_id" field value.
"""

import argparse
import json
import sys
import time

import requests

# ── Colour helpers (works on Windows 10+ with VirtualTerminal) ──────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"{GREEN}  ✔ {msg}{RESET}")
def warn(msg):  print(f"{YELLOW}  ⚠ {msg}{RESET}")
def fail(msg):  print(f"{RED}  ✖ {msg}{RESET}")
def info(msg):  print(f"{CYAN}  ℹ {msg}{RESET}")
def bold(msg):  print(f"{BOLD}{msg}{RESET}")


# ── Main test ────────────────────────────────────────────────────────────────

def run_test(strategy_id: str, base: str) -> None:
    sep = "─" * 60

    bold(f"\n{sep}")
    bold(" REAL-TIME STRATEGY PIPELINE TEST")
    bold(sep)
    info(f"Backend: {base}")
    info(f"Strategy ID: {strategy_id}")
    print()

    # ── Step 1: Health check ─────────────────────────────────────────────────
    bold("Step 1 — Health check")
    try:
        r = requests.get(f"{base}/health", timeout=5)
        r.raise_for_status()
        ok(f"Backend is up  ({r.json()})")
    except Exception as e:
        fail(f"Backend not reachable: {e}")
        fail("Start the backend first:  uvicorn app.main:app --reload --port 8000")
        sys.exit(1)
    print()

    # ── Step 2: Initial drift check (baseline) ───────────────────────────────
    bold("Step 2 — Baseline drift check (before injecting knowledge)")
    r = requests.get(f"{base}/api/v1/realtime/drift-check",
                     params={"strategy_id": strategy_id}, timeout=60)
    if r.status_code != 200:
        fail(f"Drift check failed: {r.status_code} — {r.text[:300]}")
        sys.exit(1)

    baseline = r.json()
    sim_before = baseline.get("similarity", "N/A")
    level_before = baseline.get("drift_level", "N/A")

    drift_colour = GREEN if level_before == "LOW" else YELLOW if level_before == "MODERATE" else RED
    print(f"  Similarity : {sim_before:.4f}" if isinstance(sim_before, float) else f"  Similarity : {sim_before}")
    print(f"  Drift level: {drift_colour}{level_before}{RESET}")
    print()

    # ── Step 3: Simulate HIGH drift (inject disruptive knowledge + regenerate) ──
    bold("Step 3 — Simulate HIGH drift + auto-regeneration")
    info("Injecting 4 disruptive knowledge entries about strategy shifts for construction SMEs...")
    info("This may take 30–60 seconds (LLM call in progress)...")
    print()

    start = time.time()
    r = requests.post(
        f"{base}/api/v1/realtime/simulate-drift",
        json={"strategy_id": strategy_id},
        timeout=180,  # LLM can take up to 60s
    )
    elapsed = time.time() - start

    if r.status_code != 200:
        fail(f"Simulate drift failed: {r.status_code}")
        print(r.text[:500])
        sys.exit(1)

    result = r.json()

    ok(f"Simulation complete in {elapsed:.1f}s")
    print()

    # ── Step 4: Print results ────────────────────────────────────────────────
    bold("Step 4 — Results")
    print(sep)

    injected = result.get("injected_knowledge_count", 0)
    dr = result.get("drift_result", {})
    before = result.get("before", {})
    after  = result.get("after", {})

    info(f"Knowledge entries injected: {injected}")
    print()

    # Drift result
    sim = dr.get("similarity_score", 0)
    level = dr.get("drift_level", "?")
    regenerated = dr.get("regenerate_triggered", False)
    drift_colour = GREEN if level == "LOW" else YELLOW if level == "MODERATE" else RED
    print(f"  Similarity score : {sim:.4f}")
    print(f"  Drift level      : {drift_colour}{BOLD}{level}{RESET}")
    print(f"  Regenerate flag  : {'YES ✔' if regenerated else 'NO'}")
    if not regenerated:
        warn(f"Drift level was not HIGH (similarity {sim:.4f} > 0.75).")
        warn("The knowledge base already has enough matching content to keep similarity above threshold.")
        warn("Try calling the endpoint again to accumulate more disruptive entries,")
        warn("or use POST /api/v1/realtime/force-refresh for an unconditional regeneration.")
    print()

    # Before
    bold("BEFORE (old strategy):")
    print(f"  ID         : {before.get('strategy_id')}")
    print(f"  Version    : v{before.get('version')}")
    print(f"  Confidence : {round((before.get('confidence_score') or 0) * 100)}%")
    print(f"  Drift level: {before.get('drift_level') or 'N/A'}")
    print(f"  Platforms  : {', '.join(before.get('platforms', []))}")
    print(f"  Summary    : {before.get('summary_preview', '')[:150]}...")
    print()

    # After
    bold("AFTER (new strategy — auto-generated from same SME profile):")
    print(f"  ID         : {after.get('strategy_id')}")
    print(f"  Version    : v{after.get('version')}")
    print(f"  Confidence : {round((after.get('confidence_score') or 0) * 100)}%")
    print(f"  Drift level: {after.get('drift_level') or 'N/A'}")
    print(f"  Platforms  : {', '.join(after.get('platforms', []))}")
    print(f"  Summary    : {after.get('summary_preview', '')[:150]}...")
    print()

    # Full strategy JSON (optional verbose output)
    print(sep)
    bold("Full new strategy JSON:")
    full = after.get("full_strategy", {})
    fields = ["strategy_summary", "recommended_platforms", "content_strategy",
              "budget_allocation", "reasoning", "confidence_score"]
    for f in fields:
        val = full.get(f, "")
        if isinstance(val, str) and len(val) > 300:
            val = val[:300] + "..."
        print(f"  {f}: {json.dumps(val, ensure_ascii=False, indent=2) if isinstance(val, (dict, list)) else val}")
    print()

    ok(f"New strategy_id to use in the dashboard: {after.get('strategy_id')}")
    info("Update localStorage in the browser:")
    info("  localStorage.setItem('strategy_result', JSON.stringify(<paste full_strategy field>))")
    info("  Or regenerate from the form to pick it up automatically.")


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test real-time strategy pipeline")
    parser.add_argument("strategy_id", help="The strategy_id to test (from localStorage)")
    parser.add_argument("--base", default="http://localhost:8000",
                        help="FastAPI base URL (default: http://localhost:8000)")
    args = parser.parse_args()

    run_test(args.strategy_id, args.base.rstrip("/"))
