"""Price monitoring for saved shoes via KicksDB (kicks.dev).

Always returns an entry per saved shoe. If KicksDB has market data,
it's attached. Otherwise the shoe is shown with "no market data" state.
Results cached 30 min per user.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from typing import Any

import httpx

from app.api import repo

logger = logging.getLogger(__name__)

_CACHE_TTL = 1800  # 30 minutes

_deals_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_fetch_locks: dict[str, asyncio.Lock] = {}


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", name.lower()).strip()


async def _fetch_price(shoe_name: str) -> dict[str, Any] | None:
    """Return market price info from KicksDB StockX endpoint, or None on failure."""
    api_key = os.getenv("SNEAKER_DB_API_KEY", "")
    if not api_key:
        return None
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        async with httpx.AsyncClient(timeout=10, headers=headers) as client:
            for query in [shoe_name, shoe_name.split("'")[0].strip(), shoe_name.split(" ")[0]]:
                resp = await client.get(
                    "https://api.kicks.dev/v3/stockx/products",
                    params={"query": query, "limit": 3},
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("data") or data.get("results") or (data if isinstance(data, list) else [])
                if not results:
                    continue

                norm_target = _normalize(shoe_name)
                best = None
                for item in results:
                    item_name = item.get("title") or item.get("name") or ""
                    if _normalize(item_name) in norm_target or norm_target in _normalize(item_name):
                        best = item
                        break
                if best is None:
                    best = results[0]

                # KicksDB returns min_price / max_price / avg_price
                min_price = best.get("min_price") or best.get("lowest_ask") or None
                retail = best.get("retail_price") or best.get("avg_price") or None
                image = best.get("image") or best.get("image_url") or None
                url = best.get("url") or best.get("stockx_url") or None
                matched = best.get("title") or best.get("name")

                return {
                    "lowest_ask": float(min_price) if min_price else None,
                    "highest_bid": None,  # not provided by this endpoint
                    "retail_price": float(retail) if retail else None,
                    "image_url": image,
                    "url": url,
                    "matched_name": matched,
                }
    except Exception as exc:
        logger.debug("price fetch for %r failed: %s", shoe_name, exc)
    return None


async def get_deals(user_id: str) -> list[dict[str, Any]]:
    now = time.monotonic()
    cached = _deals_cache.get(user_id)
    if cached and (now - cached[0]) < _CACHE_TTL:
        return cached[1]

    if user_id not in _fetch_locks:
        _fetch_locks[user_id] = asyncio.Lock()

    async with _fetch_locks[user_id]:
        cached = _deals_cache.get(user_id)
        if cached and (now - cached[0]) < _CACHE_TTL:
            return cached[1]

        saved = await repo.list_saved(user_id)
        tasks = [_fetch_price(shoe.name) for shoe in saved]
        price_results = await asyncio.gather(*tasks)

        deals: list[dict[str, Any]] = []
        for shoe, prices in zip(saved, price_results):
            deal: dict[str, Any] = {
                "shoe_id": shoe.id,
                "name": shoe.name,
                "brand": shoe.brand,
                "image_url": shoe.image_url,
                "url": shoe.url,
                "lowest_ask": None,
                "retail_price": None,
                "highest_bid": None,
                "price_drop": False,
                "has_market_data": False,
            }

            if prices:
                deal["url"] = prices.get("url") or shoe.url
                deal["image_url"] = prices.get("image_url") or shoe.image_url
                deal["lowest_ask"] = prices.get("lowest_ask")
                deal["retail_price"] = prices.get("retail_price")
                deal["highest_bid"] = prices.get("highest_bid")
                deal["matched_name"] = prices.get("matched_name")

                lowest = prices.get("lowest_ask")
                retail = prices.get("retail_price")
                if lowest and retail:
                    deal["has_market_data"] = True
                    if lowest < retail:
                        deal["price_drop"] = True
                        deal["savings"] = round(retail - lowest, 2)
                elif lowest:
                    deal["has_market_data"] = True

            deals.append(deal)

        # Price drops first, then shoes with any market data, then the rest
        deals.sort(key=lambda d: (not d["price_drop"], not d["has_market_data"], d["name"]))

        _deals_cache[user_id] = (time.monotonic(), deals)
        return deals
