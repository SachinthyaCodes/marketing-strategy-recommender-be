-- Phase 6 Migration: Embedding-Based Strategy Drift Detection
-- Adds drift metadata columns to strategies table for research auditability

-- ─── Add drift analysis columns ──────────────────────────────────────
alter table strategies
    add column if not exists drift_similarity float,
    add column if not exists drift_level text,
    add column if not exists regenerate_flag boolean;

-- ─── Optional: index on drift_level for analytical queries ───────────
create index if not exists idx_strategies_drift_level
    on strategies (drift_level);
