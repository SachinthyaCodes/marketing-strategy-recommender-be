-- ============================================================
-- Migration 005 — Real-time Strategy Updates
-- ============================================================
-- Adds columns to `strategies` to support:
--   1. realtime_enabled  — user toggle per strategy
--   2. sme_profile_json  — persisted profile for auto-regeneration
--   3. last_drift_check  — timestamp of the latest drift evaluation
--   4. auto_updated_at   — timestamp of the latest auto-refresh
-- ============================================================

-- 1. Real-time toggle (opt-in per strategy row)
alter table strategies
  add column if not exists realtime_enabled boolean not null default false;

-- 2. Store the SME profile so we can regenerate without user presence
alter table strategies
  add column if not exists sme_profile_json jsonb;

-- 3. Tracking timestamps
alter table strategies
  add column if not exists last_drift_check timestamptz;

alter table strategies
  add column if not exists auto_updated_at timestamptz;

-- 4. Index for quick lookup of realtime-enabled strategies
create index if not exists idx_strategies_realtime
  on strategies (realtime_enabled)
  where realtime_enabled = true;
