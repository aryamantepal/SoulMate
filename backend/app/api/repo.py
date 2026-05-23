import os
from dataclasses import asdict
from typing import Any

import httpx

from app.sources.base import Shoe
from app.taste.dims import TasteVec, zero_vec

_taste_by_user: dict[str, TasteVec] = {}
_swipe_count_by_user: dict[str, int] = {}
_seen_ids_by_user: dict[str, set[str]] = {}
_saved_by_user: dict[str, dict[str, Shoe]] = {}


def _supabase_config() -> tuple[str, str] | None:
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not service_key:
        return None
    return url.rstrip("/"), service_key


def _headers(service_key: str) -> dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


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


async def _get_json(
    client: httpx.AsyncClient,
    path: str,
    service_key: str,
    params: dict[str, str],
) -> list[dict[str, Any]]:
    response = await client.get(path, headers=_headers(service_key), params=params)
    response.raise_for_status()
    return response.json()


async def get_taste(user_id: str) -> TasteVec:
    config = _supabase_config()
    if config:
        url, service_key = config
        async with httpx.AsyncClient(base_url=f"{url}/rest/v1") as client:
            rows = await _get_json(
                client,
                "/taste_vectors",
                service_key,
                {"user_id": f"eq.{user_id}", "select": "taste"},
            )
        if rows:
            return {**zero_vec(), **rows[0].get("taste", {})}

    return dict(_taste_by_user.get(user_id, zero_vec()))


async def get_swipe_count(user_id: str) -> int:
    config = _supabase_config()
    if config:
        url, service_key = config
        async with httpx.AsyncClient(base_url=f"{url}/rest/v1") as client:
            rows = await _get_json(
                client,
                "/taste_vectors",
                service_key,
                {"user_id": f"eq.{user_id}", "select": "swipe_count"},
            )
        if rows:
            return int(rows[0].get("swipe_count", 0))

    return _swipe_count_by_user.get(user_id, 0)


async def get_seen_ids(user_id: str) -> set[str]:
    config = _supabase_config()
    if config:
        url, service_key = config
        async with httpx.AsyncClient(base_url=f"{url}/rest/v1") as client:
            rows = await _get_json(
                client,
                "/swipes",
                service_key,
                {"user_id": f"eq.{user_id}", "select": "shoe_id"},
            )
        return {row["shoe_id"] for row in rows}

    return set(_seen_ids_by_user.get(user_id, set()))


async def record_swipe(
    user_id: str,
    shoe: Shoe,
    direction: int,
    taste: TasteVec,
) -> None:
    config = _supabase_config()
    if config:
        url, service_key = config
        shoe_payload = asdict(shoe)
        async with httpx.AsyncClient(base_url=f"{url}/rest/v1") as client:
            headers = _headers(service_key)
            profile = await client.post(
                "/profiles",
                headers={**headers, "Prefer": "resolution=merge-duplicates"},
                json={"user_id": user_id},
            )
            profile.raise_for_status()

            vector = await client.post(
                "/taste_vectors",
                headers={**headers, "Prefer": "resolution=merge-duplicates"},
                json={
                    "user_id": user_id,
                    "taste": taste,
                    "swipe_count": await get_swipe_count(user_id) + 1,
                },
            )
            vector.raise_for_status()

            swipe = await client.post(
                "/swipes",
                headers=headers,
                json={
                    "user_id": user_id,
                    "shoe_id": shoe.id,
                    "direction": direction,
                    "shoe": shoe_payload,
                    "taste_after": taste,
                },
            )
            swipe.raise_for_status()

        if direction > 0:
            await save_shoe(user_id, shoe)
        return

    _taste_by_user[user_id] = dict(taste)
    _swipe_count_by_user[user_id] = _swipe_count_by_user.get(user_id, 0) + 1
    _seen_ids_by_user.setdefault(user_id, set()).add(shoe.id)

    if direction > 0:
        await save_shoe(user_id, shoe)


async def save_shoe(user_id: str, shoe: Shoe) -> None:
    config = _supabase_config()
    if config:
        url, service_key = config
        async with httpx.AsyncClient(base_url=f"{url}/rest/v1") as client:
            response = await client.post(
                "/saved_shoes",
                headers={
                    **_headers(service_key),
                    "Prefer": "resolution=merge-duplicates",
                },
                json={
                    "user_id": user_id,
                    "shoe_id": shoe.id,
                    "shoe": asdict(shoe),
                },
            )
            response.raise_for_status()
        return

    _saved_by_user.setdefault(user_id, {})[shoe.id] = shoe


async def list_saved(user_id: str) -> list[Shoe]:
    config = _supabase_config()
    if config:
        url, service_key = config
        async with httpx.AsyncClient(base_url=f"{url}/rest/v1") as client:
            rows = await _get_json(
                client,
                "/saved_shoes",
                service_key,
                {"user_id": f"eq.{user_id}", "select": "shoe"},
            )
        return [_shoe_from_payload(row["shoe"]) for row in rows]

    return list(_saved_by_user.get(user_id, {}).values())
