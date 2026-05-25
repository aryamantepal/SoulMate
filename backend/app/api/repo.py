"""Persistence for taste vectors, swipes, saved shoes.

If `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` are set, we talk to Supabase via
`supabase-py` (service-role bypasses RLS server-side; RLS still gates the public
anon key). Otherwise we fall back to per-process in-memory dicts so the backend
boots and tests run without any cloud config.
"""

from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any

from supabase import AsyncClient, create_async_client

from app.sources.base import Shoe
from app.taste.dims import TasteVec, zero_vec

_taste_by_user: dict[str, TasteVec] = {}
_swipe_count_by_user: dict[str, int] = {}
_seen_ids_by_user: dict[str, set[str]] = {}
_saved_by_user: dict[str, dict[str, Shoe]] = {}

_client: AsyncClient | None = None


async def _supabase() -> AsyncClient | None:
    """Lazy-init a service-role Supabase client, or None if env is unset."""

    global _client
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not service_key:
        return None
    if _client is None:
        _client = await create_async_client(url, service_key)
    return _client


def _shoe_from_payload(payload: dict[str, Any]) -> Shoe:
    return Shoe(
        id=payload["id"],
        name=payload["name"],
        brand=payload["brand"],
        v=payload["v"],
        image_url=payload.get("image_url"),
        url=payload.get("url"),
        notes=payload.get("notes"),
    )


async def get_taste(user_id: str) -> TasteVec:
    client = await _supabase()
    if client is not None:
        result = (
            await client.table("taste_vectors")
            .select("taste")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if result.data:
            return {**zero_vec(), **(result.data[0].get("taste") or {})}
        return zero_vec()

    return dict(_taste_by_user.get(user_id, zero_vec()))


async def get_swipe_count(user_id: str) -> int:
    client = await _supabase()
    if client is not None:
        result = (
            await client.table("taste_vectors")
            .select("swipe_count")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if result.data:
            return int(result.data[0].get("swipe_count") or 0)
        return 0

    return _swipe_count_by_user.get(user_id, 0)


async def get_seen_ids(user_id: str) -> set[str]:
    client = await _supabase()
    if client is not None:
        result = (
            await client.table("swipes")
            .select("shoe_id")
            .eq("user_id", user_id)
            .execute()
        )
        return {row["shoe_id"] for row in (result.data or [])}

    return set(_seen_ids_by_user.get(user_id, set()))


async def record_swipe(
    user_id: str,
    shoe: Shoe,
    direction: int,
    taste: TasteVec,
    next_swipe_count: int,
) -> None:
    client = await _supabase()
    if client is not None:
        await (
            client.rpc(
                "record_swipe",
                {
                    "p_user_id": user_id,
                    "p_shoe_id": shoe.id,
                    "p_direction": direction,
                    "p_shoe": asdict(shoe),
                    "p_taste": taste,
                    "p_swipe_count": next_swipe_count,
                },
            ).execute()
        )
        return

    _taste_by_user[user_id] = dict(taste)
    _swipe_count_by_user[user_id] = next_swipe_count
    _seen_ids_by_user.setdefault(user_id, set()).add(shoe.id)

    if direction > 0:
        await save_shoe(user_id, shoe)


async def save_shoe(user_id: str, shoe: Shoe) -> None:
    client = await _supabase()
    if client is not None:
        await (
            client.table("saved_shoes")
            .upsert(
                {
                    "user_id": user_id,
                    "shoe_id": shoe.id,
                    "shoe": asdict(shoe),
                },
                on_conflict="user_id,shoe_id",
            )
            .execute()
        )
        return

    _saved_by_user.setdefault(user_id, {})[shoe.id] = shoe


async def list_saved(user_id: str) -> list[Shoe]:
    client = await _supabase()
    if client is not None:
        result = (
            await client.table("saved_shoes")
            .select("shoe")
            .eq("user_id", user_id)
            .execute()
        )
        return [_shoe_from_payload(row["shoe"]) for row in (result.data or [])]

    return list(_saved_by_user.get(user_id, {}).values())
