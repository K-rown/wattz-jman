-- One row per person: their done marks and "We're here". Run once in the Supabase SQL editor.
create table if not exists public.ptj_progress (
  person      text primary key,
  state       jsonb not null default '{}'::jsonb,
  updated_at  timestamptz not null default now()
);
alter table public.ptj_progress enable row level security;
-- The crew page uses the anon key: it may read and write this table and nothing else.
drop policy if exists ptj_read on public.ptj_progress;
drop policy if exists ptj_insert on public.ptj_progress;
drop policy if exists ptj_update on public.ptj_progress;
create policy ptj_read   on public.ptj_progress for select to anon using (true);
create policy ptj_insert on public.ptj_progress for insert to anon with check (true);
create policy ptj_update on public.ptj_progress for update to anon using (true) with check (true);
grant select, insert, update on public.ptj_progress to anon;
