"""Persistence for taste vectors, swipes, saved shoes.

If `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` are set, we talk to Supabase via
`supabase-py` (service-role bypasses RLS server-side; RLS still gates the public
anon key). Otherwise we fall back to per-process in-memory dicts so the backend
boots and tests run without any cloud config.
"""

from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any  # noqa: F401 — used in get_swipe_history return type

from supabase import AsyncClient, create_async_client

from app.sources.base import Shoe
from app.taste.dims import TasteVec, zero_vec

_taste_by_user: dict[str, TasteVec] = {}
_swipe_count_by_user: dict[str, int] = {}
_seen_ids_by_user: dict[str, set[str]] = {}
_saved_by_user: dict[str, dict[str, Shoe]] = {}
_share_token_by_user: dict[str, str] = {}
_user_id_by_share_token: dict[str, str] = {}

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


async def get_swipe_timeline(user_id: str) -> list[dict[str, Any]]:
    """Return all swipes (direction, taste_after, created_at) oldest-first.

    Used to compute taste-evolution stats. Best-effort: returns [] on failure
    or when running without Supabase.
    """
    import logging
    log = logging.getLogger(__name__)
    client = await _supabase()
    if client is None:
        return []
    try:
        result = (
            await client.table("swipes")
            .select("direction, taste_after, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .execute()
        )
        return [
            {
                "direction": row["direction"],
                "taste_after": row.get("taste_after") or {},
                "created_at": row.get("created_at"),
            }
            for row in (result.data or [])
        ]
    except Exception as exc:
        log.error("get_swipe_timeline failed user=%s: %s", user_id, exc)
        return []


async def get_swipe_history(
    user_id: str,
    direction: int | None = None,
    limit: int = 40,
) -> list[dict[str, Any]]:
    import logging
    log = logging.getLogger(__name__)
    client = await _supabase()
    if client is not None:
        try:
            q = (
                client.table("swipes")
                .select("*")
                .eq("user_id", user_id)
            )
            if direction is not None:
                q = q.eq("direction", direction)
            result = await q.limit(limit).execute()
            log.info("swipe_history user=%s rows=%d", user_id, len(result.data or []))
            return [
                {
                    "shoe_id": row["shoe_id"],
                    "direction": row["direction"],
                    "shoe": row.get("shoe") or {},
                    "created_at": row.get("created_at") or row.get("inserted_at"),
                }
                for row in (result.data or [])
            ]
        except Exception as exc:
            log.error("get_swipe_history failed user=%s: %s", user_id, exc)
            return []
    # In-memory fallback: no history stored beyond seen_ids
    return []


async def reset_taste(user_id: str) -> None:
    client = await _supabase()
    if client is not None:
        await (
            client.table("taste_vectors")
            .upsert({"user_id": user_id, "taste": {}, "swipe_count": 0}, on_conflict="user_id")
            .execute()
        )
        return
    _taste_by_user.pop(user_id, None)
    _swipe_count_by_user.pop(user_id, None)


async def reset_seen(user_id: str) -> None:
    client = await _supabase()
    if client is not None:
        await (
            client.table("swipes")
            .delete()
            .eq("user_id", user_id)
            .execute()
        )
        return
    _seen_ids_by_user.pop(user_id, None)


async def backfill_liked_swipes(user_id: str) -> int:
    """Insert direction=1 swipe rows for any saved shoe that has no swipe record."""
    client = await _supabase()
    if client is None:
        return 0
    existing = await get_seen_ids(user_id)
    saved = await list_saved(user_id)
    missing = [s for s in saved if s.id not in existing]
    if not missing:
        return 0
    from dataclasses import asdict
    rows = [
        {"user_id": user_id, "shoe_id": s.id, "direction": 1, "shoe": asdict(s), "taste_after": {}}
        for s in missing
    ]
    await client.table("swipes").insert(rows).execute()
    return len(rows)


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


async def get_user_email(user_id: str) -> str | None:
    """Return the email address for a user from auth.users, or None."""
    client = await _supabase()
    if client is None:
        return None
    try:
        result = (
            await client.table("auth.users")
            .select("email")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if result.data:
            return result.data.get("email")
    except Exception:
        pass
    return None


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


async def get_or_create_share_token(user_id: str) -> str:
    import secrets
    client = await _supabase()
    if client is not None:
        result = (
            await client.table("profiles")
            .select("share_token")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if result.data and result.data[0].get("share_token"):
            return str(result.data[0]["share_token"])

        # Generate new token
        token = secrets.token_urlsafe(16)
        # Update the profiles table
        await (
            client.table("profiles")
            .upsert({"user_id": user_id, "share_token": token}, on_conflict="user_id")
            .execute()
        )
        return token

    if user_id not in _share_token_by_user:
        token = secrets.token_urlsafe(16)
        _share_token_by_user[user_id] = token
        _user_id_by_share_token[token] = user_id
    return _share_token_by_user[user_id]


async def get_user_id_by_share_token(share_token: str) -> str | None:
    client = await _supabase()
    if client is not None:
        result = (
            await client.table("profiles")
            .select("user_id")
            .eq("share_token", share_token)
            .limit(1)
            .execute()
        )
        if result.data:
            return str(result.data[0]["user_id"])
        return None

    return _user_id_by_share_token.get(share_token)


async def get_taste_by_share_token(share_token: str) -> tuple[TasteVec, int] | None:
    user_id = await get_user_id_by_share_token(share_token)
    if not user_id:
        return None
    taste = await get_taste(user_id)
    count = await get_swipe_count(user_id)
    return taste, count
