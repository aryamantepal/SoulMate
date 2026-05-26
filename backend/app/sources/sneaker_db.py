"""ShoeSource backed by the KicksDB API (kicks.dev).

Falls back to the seed catalog if the API is unreachable or returns no usable
results, so the app still works in dev without network access.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from typing import Any

import httpx

from app.sources.base import Shoe, ShoeSource
from app.sources.seed import CATALOG
from app.taste.dims import DIMENSIONS, TasteVec

logger = logging.getLogger(__name__)

_KICKS_BASE = "https://api.kicks.dev/v3/stockx/products"
_PAGE_LIMIT = 100
_FETCH_PAGES = 3  # ~300 shoes per cold start; cached in memory after that

# ---------------------------------------------------------------------------
# Heuristic vector generation from shoe metadata
# ---------------------------------------------------------------------------

_RETRO_SIGNALS = re.compile(
    r"\b(retro|vintage|classic|og|low|high|court|heritage|old school|archive)\b", re.I
)
_WARM_SIGNALS = re.compile(
    r"\b(cream|wheat|beige|tan|caramel|sand|brown|clay|rust|terracotta|mocha|latte)\b",
    re.I,
)
_EARTHY_SIGNALS = re.compile(
    r"\b(earth|brown|olive|sage|forest|moss|mud|stone|hemp|canvas|suede|leather"
    r"|linen|ivory|khaki|natural|taupe)\b",
    re.I,
)
_TECHY_SIGNALS = re.compile(
    r"\b(gel|boost|max|react|zoom|foam|wave|trail|ultra|gore.?tex|carbon|reflective"
    r"|flyknit|primeknit|vaporfly|alphafly|terrascape|xt-|acg|tech)\b",
    re.I,
)
_CHUNK_SIGNALS = re.compile(
    r"\b(chunky|platform|dad|9060|polttoauto|yeezy|foam runner|clogs|mule|crocs"
    r"|monster|hoka|maximalist|stack|super elevated)\b",
    re.I,
)
_LOUD_SIGNALS = re.compile(
    r"\b(neon|volt|hyper|infrared|bright|multicolor|tie.?dye|iridescent|holographic"
    r"|acid|rainbow|aurora|solar)\b",
    re.I,
)
_MINIMAL_SIGNALS = re.compile(
    r"\b(minimal|clean|simple|monochrome|all.?white|triple.?white|all.?black"
    r"|triple.?black|tonal|blank|gat|common projects|achilles)\b",
    re.I,
)


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _count(pattern: re.Pattern[str], text: str) -> float:
    return min(1.0, len(pattern.findall(text)) * 0.35)


def vec_from_metadata(
    name: str,
    brand: str,
    colorway: str = "",
    silhouette: str = "",
) -> TasteVec:
    text = f"{name} {brand} {colorway} {silhouette}"

    retro = _clamp(0.2 + _count(_RETRO_SIGNALS, text))
    warm = _clamp(0.2 + _count(_WARM_SIGNALS, text))
    earthy = _clamp(0.15 + _count(_EARTHY_SIGNALS, text))
    techy = _clamp(0.1 + _count(_TECHY_SIGNALS, text))
    chunk = _clamp(0.15 + _count(_CHUNK_SIGNALS, text))
    loud = _clamp(0.1 + _count(_LOUD_SIGNALS, text))
    minimal = _clamp(0.1 + _count(_MINIMAL_SIGNALS, text))

    # Techy and retro are roughly inverse; loud and minimal are roughly inverse.
    techy = _clamp(techy - retro * 0.3)
    minimal = _clamp(minimal - loud * 0.2)

    return {
        "chunk": round(chunk, 2),
        "retro": round(retro, 2),
        "warm": round(warm, 2),
        "minimal": round(minimal, 2),
        "earthy": round(earthy, 2),
        "loud": round(loud, 2),
        "techy": round(techy, 2),
    }


# ---------------------------------------------------------------------------
# Deterministic ID from name + brand (API ids are UUIDs we can keep as-is)
# ---------------------------------------------------------------------------

def _shoe_id(raw_id: str, name: str, brand: str) -> str:
    if raw_id:
        return raw_id
    slug = re.sub(r"[^a-z0-9]+", "-", f"{brand}-{name}".lower()).strip("-")
    return slug[:80]


def _parse_shoe(item: dict[str, Any]) -> Shoe | None:
    name = (item.get("name") or item.get("title") or "").strip()
    brand = (item.get("brand") or "").strip()
    if not name or not brand:
        return None

    shoe_id = _shoe_id(item.get("id") or item.get("uuid") or "", name, brand)
    colorway = item.get("colorway") or item.get("color") or ""
    silhouette = item.get("silhouette") or item.get("model") or ""

    # KicksDB puts image in image/image_url/thumbnail at top level or nested
    image_url = (
        item.get("image_url")
        or item.get("image")
        or item.get("thumbnail")
        or (item.get("media") or {}).get("imageUrl")
        or (item.get("media") or {}).get("smallImageUrl")
        or None
    )

    retail_url = (
        item.get("url")
        or item.get("stockx_url")
        or (item.get("links") or {}).get("stockX")
        or (item.get("links") or {}).get("goat")
        or None
    )

    return Shoe(
        id=shoe_id,
        name=name,
        brand=brand,
        v=vec_from_metadata(name, brand, colorway, silhouette),
        image_url=image_url,
        url=retail_url,
        notes=colorway if colorway and colorway.lower() not in name.lower() else None,
    )


# ---------------------------------------------------------------------------
# Async fetch + in-memory cache
# ---------------------------------------------------------------------------

_cache: list[Shoe] = []
_cache_lock = asyncio.Lock()


async def _fetch_catalog() -> list[Shoe]:
    import os
    api_key = os.getenv("SNEAKER_DB_API_KEY", "")
    if not api_key:
        logger.warning("sneaker_db: SNEAKER_DB_API_KEY not set, falling back to seed")
        return []

    shoes: list[Shoe] = []
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        for page in range(1, _FETCH_PAGES + 1):
            try:
                resp = await client.get(
                    _KICKS_BASE,
                    params={"limit": _PAGE_LIMIT, "page": page, "filters": 'product_type = "sneakers"'},
                )
                logger.info("kicks.dev page %d status %d", page, resp.status_code)
                resp.raise_for_status()
                data = resp.json()
                # KicksDB wraps results in {"data": [...]} or returns a list directly
                results = data.get("data") or data.get("results") or (data if isinstance(data, list) else [])
                for item in results:
                    shoe = _parse_shoe(item)
                    if shoe is not None:
                        shoes.append(shoe)
                logger.info("kicks.dev page %d: %d items, %d total", page, len(results), len(shoes))
                if len(results) < _PAGE_LIMIT:
                    break
            except Exception as exc:
                logger.warning("kicks.dev fetch page %d failed: %s", page, exc)
                break
    return shoes


async def refresh_catalog() -> None:
    """Re-fetch the catalog and atomically swap the in-memory cache.

    Only replaces the cache when the fetch returns a non-empty list, so a
    transient API failure never clobbers a previously-good cache with the
    seed fallback.
    """
    global _cache
    fetched = await _fetch_catalog()
    if fetched:
        async with _cache_lock:
            _cache = fetched
        logger.info("sneaker_db: refreshed cache, now %d shoes", len(fetched))
    else:
        logger.warning(
            "sneaker_db: refresh fetch returned nothing, keeping existing %d shoes",
            len(_cache),
        )


async def start_periodic_refresh(interval_seconds: int = 21600) -> None:
    """Loop forever, refreshing the catalog every ``interval_seconds``.

    The interval can be overridden via the ``CATALOG_REFRESH_SECONDS`` env var.
    Each iteration is wrapped in try/except so a single failure does not kill
    the loop.
    """
    import os

    raw = os.getenv("CATALOG_REFRESH_SECONDS")
    if raw is not None:
        try:
            interval_seconds = int(raw)
        except (TypeError, ValueError):
            logger.warning(
                "sneaker_db: invalid CATALOG_REFRESH_SECONDS=%r, using default %d",
                raw,
                interval_seconds,
            )

    logger.info("sneaker_db: starting periodic refresh every %d seconds", interval_seconds)
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            await refresh_catalog()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("sneaker_db: periodic refresh iteration failed: %s", exc)


async def _warm_cache() -> list[Shoe]:
    global _cache
    async with _cache_lock:
        if _cache:
            return _cache
        fetched = await _fetch_catalog()
        if fetched:
            _cache = fetched
            logger.info("sneaker_db: loaded %d shoes from API", len(_cache))
        else:
            logger.warning("sneaker_db: API returned nothing, falling back to seed")
            _cache = list(CATALOG)
        return _cache


# ---------------------------------------------------------------------------
# ShoeSource implementation
# ---------------------------------------------------------------------------

class SneakerDatabaseSource:
    """Async-friendly source backed by thesneakerdatabase.dev with seed fallback."""

    def __init__(self) -> None:
        self._shoes: list[Shoe] = list(CATALOG)  # start with seed; replaced on first use
        self._loaded = False

    async def ensure_loaded(self) -> None:
        if not self._loaded:
            self._shoes = await _warm_cache()
            self._loaded = True

    def _current(self) -> list[Shoe]:
        # Once loaded, read the live module cache so periodic refreshes are
        # picked up after an atomic swap. Before load, use the seed list.
        return _cache if self._loaded and _cache else self._shoes

    def list_shoes(self) -> list[Shoe]:
        return list(self._current())

    def get_shoe(self, shoe_id: str) -> Shoe | None:
        return next((s for s in self._current() if s.id == shoe_id), None)
