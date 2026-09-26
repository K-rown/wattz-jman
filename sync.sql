-- Progress that follows one person between their own devices, by a private code.
-- Run once against the Supabase project (already applied 2026-09-26).
--
-- The page holds only the public anon key, so the table itself is closed to it:
-- no policy, no grant. The page reaches it through two functions that take the
-- code, and a row is keyed by the code's SHA-256, never the code itself. Nobody
-- can list the rows, and nobody can read or write a row without its code.
create table if not exists public.ptj_sync (
  id          text primary key,              -- sha256(code), hex
  state       jsonb not null,
  updated_at  timestamptz not null default now()
);
alter table public.ptj_sync enable row level security;
revoke all on public.ptj_sync from anon, authenticated;

create or replace function public.ptj_pull(code text) returns jsonb
language sql security definer set search_path = public stable as $$
  select state from public.ptj_sync
  where length(code) >= 12 and id = encode(sha256(convert_to(code, 'UTF8')), 'hex');
$$;

create or replace function public.ptj_push(code text, st jsonb) returns timestamptz
language plpgsql security definer set search_path = public as $$
declare t timestamptz := now();
begin
  if length(code) < 12 then raise exception 'code too short'; end if;
  if octet_length(st::text) > 500000 then raise exception 'record too large'; end if;
  insert into public.ptj_sync (id, state, updated_at)
  values (encode(sha256(convert_to(code, 'UTF8')), 'hex'), st, t)
  on conflict (id) do update set state = excluded.state, updated_at = t;
  return t;
end $$;

revoke all on function public.ptj_pull(text), public.ptj_push(text, jsonb) from public;
grant execute on function public.ptj_pull(text), public.ptj_push(text, jsonb) to anon, authenticated;
