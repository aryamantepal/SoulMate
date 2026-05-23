create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

create table if not exists public.taste_vectors (
  user_id uuid primary key references auth.users(id) on delete cascade,
  taste jsonb not null default '{}'::jsonb,
  swipe_count integer not null default 0,
  updated_at timestamptz not null default now()
);

create table if not exists public.swipes (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  shoe_id text not null,
  direction integer not null check (direction in (-1, 1)),
  shoe jsonb not null,
  taste_after jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.saved_shoes (
  user_id uuid not null references auth.users(id) on delete cascade,
  shoe_id text not null,
  shoe jsonb not null,
  created_at timestamptz not null default now(),
  primary key (user_id, shoe_id)
);

alter table public.profiles enable row level security;
alter table public.taste_vectors enable row level security;
alter table public.swipes enable row level security;
alter table public.saved_shoes enable row level security;

drop policy if exists "profiles are user scoped" on public.profiles;
create policy "profiles are user scoped"
on public.profiles
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "taste vectors are user scoped" on public.taste_vectors;
create policy "taste vectors are user scoped"
on public.taste_vectors
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "swipes are user scoped" on public.swipes;
create policy "swipes are user scoped"
on public.swipes
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "saved shoes are user scoped" on public.saved_shoes;
create policy "saved shoes are user scoped"
on public.saved_shoes
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);
