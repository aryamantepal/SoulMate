-- Enable pgvector and add a vector column to shoes for future catalog integration.
create extension if not exists vector;

-- Catalog table for real shoes (replaces the in-memory seed when populated).
create table if not exists public.shoes (
  id         text primary key,
  name       text not null,
  brand      text not null,
  v          jsonb not null default '{}'::jsonb,
  embedding  vector(7),
  image_url  text,
  url        text,
  notes      text,
  created_at timestamptz not null default now()
);

-- HNSW index for fast cosine-distance neighbour search.
create index if not exists shoes_embedding_hnsw
  on public.shoes
  using hnsw (embedding vector_cosine_ops);

-- Helper: given a query embedding, return shoes ordered by cosine distance.
create or replace function public.match_shoes(
  query_embedding vector(7),
  match_count     integer default 20
)
returns table (
  id        text,
  name      text,
  brand     text,
  v         jsonb,
  image_url text,
  url       text,
  notes     text,
  similarity float
)
language sql stable
as $$
  select
    id, name, brand, v, image_url, url, notes,
    1 - (embedding <=> query_embedding) as similarity
  from public.shoes
  where embedding is not null
  order by embedding <=> query_embedding
  limit match_count;
$$;
