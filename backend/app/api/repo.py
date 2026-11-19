"""In-memory persistence for taste vectors, swipes, saved shoes.

Per-process dicts keyed by anonymous device ID. State resets when the backend restarts.
"""

from __future__ import annotations

import secrets
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from app.sources.base import Shoe
from app.taste.dims import TasteVec, zero_vec

_taste_by_user: dict[str, TasteVec] = {}
_swipe_count_by_user: dict[str, int] = {}
_swipes_by_user: dict[str, list[dict[str, Any]]] = {}
_saved_by_user: dict[str, dict[str, Shoe]] = {}
_collection_by_user: dict[str, dict[str, str | None]] = {}
_share_token_by_user: dict[str, str] = {}
_user_id_by_share_token: dict[str, str] = {}


async def get_taste(user_id: str) -> TasteVec:
    return dict(_taste_by_user.get(user_id, zero_vec()))


async def get_swipe_count(user_id: str) -> int:
    return _swipe_count_by_user.get(user_id, 0)


async def get_seen_ids(user_id: str) -> set[str]:
    return {r["shoe_id"] for r in _swipes_by_user.get(user_id, [])}


async def record_swipe(
    user_id: str,
    shoe: Shoe,
    direction: int,
    taste: TasteVec,
    next_swipe_count: int,
) -> None:
    _taste_by_user[user_id] = dict(taste)
    _swipe_count_by_user[user_id] = next_swipe_count
    _swipes_by_user.setdefault(user_id, []).append(
        {
            "shoe_id": shoe.id,
            "direction": direction,
            "shoe": asdict(shoe),
            "taste_after": dict(taste),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    if direction > 0:
        await save_shoe(user_id, shoe)


async def get_swipe_timeline(user_id: str) -> list[dict[str, Any]]:
    """All swipes (direction, taste_after, created_at), oldest first."""
    return [
        {
            "direction": r["direction"],
            "taste_after": r["taste_after"],
            "created_at": r["created_at"],
        }
        for r in _swipes_by_user.get(user_id, [])
    ]


async def get_swipe_history(
    user_id: str,
    direction: int | None = None,
    limit: int = 40,
) -> list[dict[str, Any]]:
    rows = [
        r
        for r in reversed(_swipes_by_user.get(user_id, []))
        if direction is None or r["direction"] == direction
    ]
    return [
        {
            "shoe_id": r["shoe_id"],
            "direction": r["direction"],
            "shoe": r["shoe"],
            "created_at": r["created_at"],
        }
        for r in rows[:limit]
    ]


async def reset_taste(user_id: str) -> None:
    _taste_by_user.pop(user_id, None)
    _swipe_count_by_user.pop(user_id, None)


async def reset_seen(user_id: str) -> None:
    _swipes_by_user.pop(user_id, None)


async def save_shoe(user_id: str, shoe: Shoe) -> None:
    _saved_by_user.setdefault(user_id, {})[shoe.id] = shoe


async def list_saved(user_id: str) -> list[Shoe]:
    return list(_saved_by_user.get(user_id, {}).values())


async def list_saved_meta(user_id: str) -> list[tuple[Shoe, str | None]]:
    """Like list_saved but pairs each shoe with its collection name (or None)."""
    saved = _saved_by_user.get(user_id, {})
    collections = _collection_by_user.get(user_id, {})
    return [(shoe, collections.get(shoe_id)) for shoe_id, shoe in saved.items()]


async def set_shoe_collection(user_id: str, shoe_id: str, collection: str | None) -> None:
    """Assign (or clear, if collection is None/empty) a saved shoe's collection."""
    value = collection.strip() if collection and collection.strip() else None
    _collection_by_user.setdefault(user_id, {})[shoe_id] = value


async def get_or_create_share_token(user_id: str) -> str:
    if user_id not in _share_token_by_user:
        token = secrets.token_urlsafe(16)
        _share_token_by_user[user_id] = token
        _user_id_by_share_token[token] = user_id
    return _share_token_by_user[user_id]


async def get_user_id_by_share_token(share_token: str) -> str | None:
    return _user_id_by_share_token.get(share_token)


async def get_taste_by_share_token(share_token: str) -> tuple[TasteVec, int] | None:
    user_id = await get_user_id_by_share_token(share_token)
    if not user_id:
        return None
    return await get_taste(user_id), await get_swipe_count(user_id)
