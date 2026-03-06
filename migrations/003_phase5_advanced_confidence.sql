-- Phase 5 Migration: Advanced Non-LLM Confidence Scoring
-- Adds per-component confidence columns for research auditability
-- Updates match_knowledge RPC to return created_at for trend recency

-- ─── 1) Add confidence breakdown columns to strategies table ───────
alter table strategies
    add column if not exists confidence_score float,
    add column if not exists trend_recency_score float,
    add column if not exists similarity_score float,
    add column if not exists data_coverage_score float,
    add column if not exists platform_stability_score float;

-- ─── 2) Update match_knowledge RPC to include created_at ──────────
-- Must drop first because the return type is changing (added created_at column)
drop function if exists match_knowledge(vector(384), integer);

create or replace function match_knowledge(
    query_embedding vector(384),
    match_count int default 5
)
returns table (
    id uuid,
    content text,
    source_type text,
    platform text,
    industry text,
    similarity float,
    created_at timestamptz
)
language plpgsql
as $$
begin
    return query
    select
        kb.id,
        kb.content,
        kb.source_type,
        kb.platform,
        kb.industry,
        1 - (kb.embedding <=> query_embedding) as similarity,
        kb.created_at
    from knowledge_base kb
    where kb.embedding is not null
    order by kb.embedding <=> query_embedding
    limit match_count;
end;
$$;
