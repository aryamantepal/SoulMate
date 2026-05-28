import base64
import hashlib
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.api import deals as deals_service
from app.api import emails as emails_service
from app.api import repo
from app.auth.supabase_auth import current_user
from app.sources.base import Shoe
from app.sources.sneaker_db import SneakerDatabaseSource
from app.taste.model import LinearTaste
from app.taste.persona import derive_persona

router = APIRouter()
source = SneakerDatabaseSource()
model = LinearTaste()


class SwipeIn(BaseModel):
    shoe_id: str
    direction: int = Field(..., ge=-1, le=1)


class SaveIn(BaseModel):
    shoe_id: str


def shoe_out(shoe: Shoe, match_pct: int | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": shoe.id,
        "name": shoe.name,
        "brand": shoe.brand,
        "v": shoe.v,
        "image_url": shoe.image_url,
        "url": shoe.url,
        "notes": shoe.notes,
    }
    if match_pct is not None:
        payload["match_pct"] = match_pct
    return payload


@router.get("/feed")
async def feed(user_id: Annotated[str, Depends(current_user)]) -> dict[str, object]:
    await source.ensure_loaded()
    taste = await repo.get_taste(user_id)
    seen_ids = await repo.get_seen_ids(user_id)
    shoes = [shoe for shoe in source.list_shoes() if shoe.id not in seen_ids]
    ranked = sorted(shoes, key=lambda shoe: model.score(taste, shoe), reverse=True)

    return {
        "items": [shoe_out(shoe, model.match_pct(taste, shoe)) for shoe in ranked],
        "taste": taste,
        "swipe_count": await repo.get_swipe_count(user_id),
        "persona": derive_persona(taste),
    }


@router.post("/swipe")
async def swipe(
    body: SwipeIn,
    user_id: Annotated[str, Depends(current_user)],
) -> dict[str, object]:
    if body.direction == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="direction must be 1 or -1",
        )

    shoe = source.get_shoe(body.shoe_id)
    if shoe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shoe not found",
        )

    taste = await repo.get_taste(user_id)
    swipe_count = await repo.get_swipe_count(user_id)
    next_taste = model.update(taste, shoe, body.direction, swipe_count)
    next_swipe_count = swipe_count + 1
    await repo.record_swipe(
        user_id, shoe, body.direction, next_taste, next_swipe_count
    )

    return {
        "shoe": shoe_out(shoe, model.match_pct(next_taste, shoe)),
        "taste": next_taste,
        "swipe_count": next_swipe_count,
        "persona": derive_persona(next_taste),
    }


@router.get("/taste")
async def taste(user_id: Annotated[str, Depends(current_user)]) -> dict[str, object]:
    taste_vec = await repo.get_taste(user_id)
    return {
        "taste": taste_vec,
        "swipe_count": await repo.get_swipe_count(user_id),
        "persona": derive_persona(taste_vec),
    }


@router.get("/saved")
async def saved(user_id: Annotated[str, Depends(current_user)]) -> dict[str, object]:
    taste = await repo.get_taste(user_id)
    shoes = await repo.list_saved(user_id)
    return {
        "items": [shoe_out(shoe, model.match_pct(taste, shoe)) for shoe in shoes],
    }


@router.delete("/taste")
async def reset_taste(user_id: Annotated[str, Depends(current_user)]) -> dict[str, object]:
    """Reset the user's taste vector back to zero without touching swipe history."""
    await repo.reset_taste(user_id)
    return {"taste": {}, "swipe_count": 0}


@router.delete("/seen")
async def reset_seen(user_id: Annotated[str, Depends(current_user)]) -> dict[str, object]:
    """Clear the user's swipe history so the full catalog is visible again."""
    await repo.reset_seen(user_id)
    return {"ok": True}


@router.get("/swipes")
async def swipe_history(
    user_id: Annotated[str, Depends(current_user)],
    direction: int | None = None,
    limit: int = 40,
) -> dict[str, object]:
    history = await repo.get_swipe_history(user_id, direction=direction, limit=limit)
    return {"items": history}


_img_cache: dict[str, tuple[bytes, str]] = {}  # url_hash -> (bytes, content_type)


@router.get("/img")
async def image_proxy(url: str) -> Response:
    """Proxy shoe images to avoid CDN hotlink blocking."""
    key = hashlib.md5(url.encode()).hexdigest()
    if key in _img_cache:
        data, ct = _img_cache[key]
        return Response(content=data, media_type=ct, headers={"Cache-Control": "public, max-age=86400"})
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            ct = resp.headers.get("content-type", "image/jpeg").split(";")[0]
            _img_cache[key] = (resp.content, ct)
            return Response(content=resp.content, media_type=ct, headers={"Cache-Control": "public, max-age=86400"})
    except Exception:
        raise HTTPException(status_code=502, detail="Could not fetch image")


@router.post("/swipes/backfill")
async def backfill_swipes(user_id: Annotated[str, Depends(current_user)]) -> dict[str, object]:
    """Insert direction=1 swipe rows for saved shoes that have no swipe record yet."""
    inserted = await repo.backfill_liked_swipes(user_id)
    return {"inserted": inserted}


@router.get("/catalog/count")
async def catalog_count(user_id: Annotated[str, Depends(current_user)]) -> dict[str, object]:
    await source.ensure_loaded()
    return {"count": len(source.list_shoes())}


@router.get("/deals")
async def deals(user_id: Annotated[str, Depends(current_user)]) -> dict[str, object]:
    return {"items": await deals_service.get_deals(user_id)}


@router.post("/saved")
async def save(
    body: SaveIn,
    user_id: Annotated[str, Depends(current_user)],
) -> dict[str, object]:
    shoe = source.get_shoe(body.shoe_id)
    if shoe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shoe not found",
        )

    await repo.save_shoe(user_id, shoe)
    taste = await repo.get_taste(user_id)
    return {"shoe": shoe_out(shoe, model.match_pct(taste, shoe))}


@router.post("/deals/notify")
async def notify_price_drops(user_id: Annotated[str, Depends(current_user)]) -> dict[str, object]:
    """Send a price drop alert email for the user's saved shoes with price drops."""
    all_deals = await deals_service.get_deals(user_id)
    price_drops = [d for d in all_deals if d.get("price_drop")]

    if not price_drops:
        return {"sent": False, "drops": 0}

    email = await repo.get_user_email(user_id)
    if not email:
        raise HTTPException(status_code=404, detail="Could not resolve user email")

    await emails_service.send_price_drop_alert(email, price_drops)
    return {"sent": True, "drops": len(price_drops)}


@router.get("/taste/share")
async def get_share_token(user_id: Annotated[str, Depends(current_user)]) -> dict[str, object]:
    """Retrieve existing or generate new shareable token for the current user's taste."""
    token = await repo.get_or_create_share_token(user_id)
    return {"share_token": token}


@router.get("/taste/public/{share_token}")
async def get_public_taste(share_token: str) -> dict[str, object]:
    """Retrieve the public taste profile for a specific share token, no authentication required."""
    res = await repo.get_taste_by_share_token(share_token)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public taste profile not found",
        )
    taste, swipe_count = res
    return {
        "taste": taste,
        "swipe_count": swipe_count,
        "persona": derive_persona(taste),
    }
