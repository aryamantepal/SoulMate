"""Price drop monitoring and /api/deals endpoint.

On each request we compare the current lowest ask from thesneakerdatabase.dev
against the retail price stored with the saved shoe. Results are cached for
30 minutes to avoid hammering the external API.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from app.api import repo

logger = logging.getLogger(__name__)

_CACHE_TTL = 1800  # seconds

# { user_id: (fetched_at, [deal_dict]) }
_deals_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_fetch_locks: dict[str, asyncio.Lock] = {}


async def _fetch_price(shoe_name: str) -> dict[str, Any] | None:
    """Query thesneakerdatabase.dev for the first match and return price info."""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                "https://api.thesneakerdatabase.dev/v1/sneakers",
                params={"name": shoe_name, "limit": 1},
            )
            resp.raise_for_status()
            results = resp.json().get("results") or []
            if not results:
                return None
            item = results[0]
            market = item.get("market") or {}
            return {
                "lowest_ask": market.get("lowestAsk"),
                "highest_bid": market.get("highestBid"),
                "retail_price": item.get("retailPrice"),
                "url": (item.get("links") or {}).get("stockX"),
            }
    except Exception as exc:
        logger.debug("price fetch for %r failed: %s", shoe_name, exc)
        return None


async def get_deals(user_id: str) -> list[dict[str, Any]]:
    """Return price-drop deals for the user's saved shoes, cached for 30 min."""
    now = time.monotonic()
    cached = _deals_cache.get(user_id)
    if cached and (now - cached[0]) < _CACHE_TTL:
        return cached[1]

    if user_id not in _fetch_locks:
        _fetch_locks[user_id] = asyncio.Lock()

    async with _fetch_locks[user_id]:
        # Re-check after acquiring lock (another coroutine may have populated it)
        cached = _deals_cache.get(user_id)
        if cached and (now - cached[0]) < _CACHE_TTL:
            return cached[1]

        saved = await repo.list_saved(user_id)
        tasks = [_fetch_price(shoe.name) for shoe in saved]
        price_results = await asyncio.gather(*tasks)

        deals: list[dict[str, Any]] = []
        for shoe, prices in zip(saved, price_results):
            if prices is None:
                continue
            lowest_ask = prices.get("lowest_ask")
            retail = prices.get("retail_price")
            deal: dict[str, Any] = {
                "shoe_id": shoe.id,
                "name": shoe.name,
                "brand": shoe.brand,
                "image_url": shoe.image_url,
                "url": prices.get("url") or shoe.url,
                "lowest_ask": lowest_ask,
                "retail_price": retail,
                "highest_bid": prices.get("highest_bid"),
            }
            # Flag as a drop if market ask is below retail
            if lowest_ask and retail and lowest_ask < retail:
                deal["price_drop"] = True
                deal["savings"] = round(retail - lowest_ask, 2)
            else:
                deal["price_drop"] = False
            deals.append(deal)

        # Sort: price drops first, then by shoe name
        deals.sort(key=lambda d: (not d["price_drop"], d["name"]))

        _deals_cache[user_id] = (time.monotonic(), deals)
        return deals
