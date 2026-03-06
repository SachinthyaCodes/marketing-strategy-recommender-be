-- Enable pgvector extension
create extension if not exists vector;

-- Knowledge Base Table
create table if not exists knowledge_base (
    id uuid primary key default gen_random_uuid(),
    content text not null,
    source_type text,
    platform text,
    industry text,
    embedding vector(384),
    created_at timestamp with time zone default now()
);

-- Strategies Table
create table if not exists strategies (
    id uuid primary key default gen_random_uuid(),
    submission_id uuid,
    strategy_json jsonb not null,
    embedding vector(384),
    version int default 1,
    created_at timestamp with time zone default now()
);

-- Indexes for common query patterns
create index if not exists idx_knowledge_base_industry on knowledge_base (industry);
create index if not exists idx_knowledge_base_platform on knowledge_base (platform);
create index if not exists idx_strategies_submission_id on strategies (submission_id);
