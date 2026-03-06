-- ============================================================
-- Migration 006 — SME Profiles Table
-- ============================================================
-- Stores the marketing form submissions (SME business profiles)
-- directly from the frontend so they can be linked to strategies
-- and persisted independently of each generation request.
--
-- Run this in the Supabase SQL Editor (same project as the backend).
-- ============================================================

-- ── SME Profiles table ───────────────────────────────────────
create table if not exists sme_profiles (
  id            uuid primary key default gen_random_uuid(),

  -- Who submitted this profile (optional — set when auth is wired)
  user_id       uuid references auth.users(id) on delete set null,

  -- Business identity
  business_type       text        not null,
  industry            text,
  business_size       text        not null,   -- solo | small-team | medium | large
  business_stage      text        not null,   -- new | growing | established
  city                text,
  district            text,
  country             text,
  products_services   text,
  unique_selling_proposition text,

  -- Budget & team
  monthly_budget      text,
  has_marketing_team  boolean     default false,
  team_size           int,

  -- Goals
  primary_goal        text,
  secondary_goals     text[],

  -- Target audience
  age_range           text,
  gender              text[],
  income_level        text,
  target_location     text,
  interests           text[],
  buying_frequency    text,

  -- Platforms
  preferred_platforms text[],
  current_platforms   text[],

  -- Challenges & strengths
  challenges          text[],
  strengths           text[],
  opportunities       text[],

  -- Full profile snapshot (the complete JSON sent to the backend)
  raw_profile_json    jsonb,

  -- Timestamps
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

-- ── Updated-at trigger ───────────────────────────────────────
create or replace function update_sme_profiles_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_sme_profiles_updated_at on sme_profiles;

create trigger trg_sme_profiles_updated_at
  before update on sme_profiles
  for each row execute procedure update_sme_profiles_updated_at();

-- ── Indexes ──────────────────────────────────────────────────
create index if not exists idx_sme_profiles_user_id
  on sme_profiles (user_id);

create index if not exists idx_sme_profiles_created_at
  on sme_profiles (created_at desc);

-- ── Row Level Security ────────────────────────────────────────
-- Enable RLS so authenticated users can only see/edit their own profiles.
-- Anonymous users (before auth is wired) can insert freely.
alter table sme_profiles enable row level security;

-- Allow anyone to INSERT (the form submitter may not be logged in yet)
create policy "allow_insert_sme_profiles"
  on sme_profiles for insert
  with check (true);

-- Authenticated users can read all of their own profiles
create policy "allow_select_own_sme_profiles"
  on sme_profiles for select
  using (user_id = auth.uid() or user_id is null);

-- Authenticated users can update their own profiles
create policy "allow_update_own_sme_profiles"
  on sme_profiles for update
  using (user_id = auth.uid());

-- ── FK: link strategies back to the profile that generated them ──
-- Optional — run only if you want the strategies table to reference sme_profiles
-- alter table strategies add column if not exists sme_profile_id uuid references sme_profiles(id) on delete set null;
-- create index if not exists idx_strategies_sme_profile_id on strategies (sme_profile_id);
