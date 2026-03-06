-- Phase 2 Migration: Update vector dimensions and add similarity search RPC
-- all-MiniLM-L6-v2 produces 384-dimensional embeddings

-- Drop old columns and recreate with correct dimension
alter table knowledge_base drop column if exists embedding;
alter table knowledge_base add column embedding vector(384);

alter table strategies drop column if exists embedding;
alter table strategies add column embedding vector(384);

-- Create HNSW index for fast approximate nearest neighbor search
create index if not exists idx_knowledge_base_embedding
    on knowledge_base
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- RPC function for semantic similarity search
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
    similarity float
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
        1 - (kb.embedding <=> query_embedding) as similarity
    from knowledge_base kb
    where kb.embedding is not null
    order by kb.embedding <=> query_embedding
    limit match_count;
end;
$$;
