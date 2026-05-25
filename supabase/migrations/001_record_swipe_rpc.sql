-- Consolidates the three sequential writes in record_swipe into one round-trip.
create or replace function public.record_swipe(
  p_user_id   uuid,
  p_shoe_id   text,
  p_direction integer,
  p_shoe      jsonb,
  p_taste     jsonb,
  p_swipe_count integer
)
returns void
language plpgsql
security definer
as $$
begin
  insert into public.profiles (user_id)
  values (p_user_id)
  on conflict (user_id) do nothing;

  insert into public.taste_vectors (user_id, taste, swipe_count)
  values (p_user_id, p_taste, p_swipe_count)
  on conflict (user_id) do update
    set taste       = excluded.taste,
        swipe_count = excluded.swipe_count,
        updated_at  = now();

  insert into public.swipes (user_id, shoe_id, direction, shoe, taste_after)
  values (p_user_id, p_shoe_id, p_direction, p_shoe, p_taste);

  if p_direction > 0 then
    insert into public.saved_shoes (user_id, shoe_id, shoe)
    values (p_user_id, p_shoe_id, p_shoe)
    on conflict (user_id, shoe_id) do nothing;
  end if;
end;
$$;

-- Only the service role (backend) may call this function.
revoke execute on function public.record_swipe(uuid, text, integer, jsonb, jsonb, integer) from public;
grant  execute on function public.record_swipe(uuid, text, integer, jsonb, jsonb, integer) to service_role;
