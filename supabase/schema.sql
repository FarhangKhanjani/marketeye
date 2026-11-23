-- Marketeye: saved searches. Run once in Supabase -> SQL Editor -> New query -> Run.
-- Row-level security: a logged-in user can read, add and delete only their own rows.

create table if not exists public.searches (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null default auth.uid() references auth.users (id) on delete cascade,
  saved_at    timestamptz not null default now(),
  fetched_at  timestamptz not null,          -- when the market data was fetched
  settings    jsonb not null,                -- volume floor + long/short ranges used
  dominance   numeric not null,              -- BTC dominance %, at fetch time
  pool        integer,                       -- alts above the volume floor
  excluded    integer,                       -- non-alts removed
  longs       jsonb not null,                -- [{code, name, pct, vol, rate}, ...]
  shorts      jsonb not null,
  outliers    jsonb not null
);

create index if not exists searches_user_saved_at on public.searches (user_id, saved_at desc);

alter table public.searches enable row level security;

drop policy if exists "read own searches" on public.searches;
drop policy if exists "add own searches" on public.searches;
drop policy if exists "delete own searches" on public.searches;
create policy "read own searches"   on public.searches for select to authenticated using (user_id = auth.uid());
create policy "add own searches"    on public.searches for insert to authenticated with check (user_id = auth.uid());
create policy "delete own searches" on public.searches for delete to authenticated using (user_id = auth.uid());

revoke all on public.searches from anon;
grant select, insert, delete on public.searches to authenticated;
