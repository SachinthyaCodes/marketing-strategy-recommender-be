-- ============================================================
-- Migration 007 — Calendar Action Plans
-- ============================================================
-- Stores AI-generated day-by-day marketing action plans tied
-- to a specific strategy version.  When a new strategy is
-- generated the calendar is automatically regenerated.
--
-- Run this in the Supabase SQL Editor.
-- ============================================================

-- ── Calendar Plans table ─────────────────────────────────────
create table if not exists calendar_plans (
  id              uuid primary key default gen_random_uuid(),

  -- Link to the strategy that produced this calendar
  strategy_id     uuid  not null references strategies(id) on delete cascade,
  submission_id   uuid  not null,

  -- Time-range the user chose (e.g. "1_week", "2_weeks", "1_month")
  time_range      text  not null default '1_month',

  -- The generated plan: an ordered JSON array of daily tasks
  -- Each element: { date, day_label, platform, content_type,
  --                  title, description, objective, best_time, tags }
  plan_json       jsonb not null default '[]'::jsonb,

  -- Quick stats
  total_tasks     int   not null default 0,
  start_date      date  not null,
  end_date        date  not null,

  -- Auto-regeneration tracking
  auto_generated  boolean not null default false,

  -- Timestamps
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

-- ── Updated-at trigger ───────────────────────────────────────
create or replace function update_calendar_plans_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_calendar_plans_updated_at on calendar_plans;

create trigger trg_calendar_plans_updated_at
  before update on calendar_plans
  for each row execute procedure update_calendar_plans_updated_at();

-- ── Indexes ──────────────────────────────────────────────────
create index if not exists idx_calendar_plans_strategy_id
  on calendar_plans (strategy_id);

create index if not exists idx_calendar_plans_submission_id
  on calendar_plans (submission_id);

create index if not exists idx_calendar_plans_created_at
  on calendar_plans (created_at desc);

-- ── Row Level Security ───────────────────────────────────────
alter table calendar_plans enable row level security;

create policy "allow_insert_calendar_plans"
  on calendar_plans for insert
  with check (true);

create policy "allow_select_calendar_plans"
  on calendar_plans for select
  using (true);

create policy "allow_update_calendar_plans"
  on calendar_plans for update
  using (true);

create policy "allow_delete_calendar_plans"
  on calendar_plans for delete
  using (true);
