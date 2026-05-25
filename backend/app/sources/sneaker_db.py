"""ShoeSource backed by the free thesneakerdatabase.dev API.

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

_API_BASE = "https://api.thesneakerdatabase.dev/v1/sneakers"
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
    name = (item.get("name") or "").strip()
    brand = (item.get("brand") or "").strip()
    if not name or not brand:
        return None

    shoe_id = _shoe_id(
        item.get("id", ""),
        name,
        brand,
    )
    colorway = item.get("colorway") or ""
    silhouette = item.get("silhouette") or ""
    media = item.get("media") or {}
    image_url = media.get("imageUrl") or media.get("smallImageUrl") or None
    retail_url = item.get("links", {}).get("stockX") or item.get("links", {}).get("goat") or None

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
    shoes: list[Shoe] = []
    async with httpx.AsyncClient(timeout=10) as client:
        for page in range(1, _FETCH_PAGES + 1):
            try:
                resp = await client.get(
                    _API_BASE,
                    params={"limit": _PAGE_LIMIT, "page": page},
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results") or []
                for item in results:
                    shoe = _parse_shoe(item)
                    if shoe is not None:
                        shoes.append(shoe)
                if len(results) < _PAGE_LIMIT:
                    break
            except Exception as exc:
                logger.warning("sneaker_db fetch page %d failed: %s", page, exc)
                break
    return shoes


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

    def list_shoes(self) -> list[Shoe]:
        return list(self._shoes)

    def get_shoe(self, shoe_id: str) -> Shoe | None:
        return next((s for s in self._shoes if s.id == shoe_id), None)
