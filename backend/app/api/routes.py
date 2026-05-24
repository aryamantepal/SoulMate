from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api import repo
from app.auth.supabase_auth import current_user
from app.sources.base import Shoe
from app.sources.mock import MockSource
from app.taste.model import LinearTaste

router = APIRouter()
source = MockSource()
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
    taste = await repo.get_taste(user_id)
    seen_ids = await repo.get_seen_ids(user_id)
    shoes = [shoe for shoe in source.list_shoes() if shoe.id not in seen_ids]
    ranked = sorted(shoes, key=lambda shoe: model.score(taste, shoe), reverse=True)

    return {
        "items": [shoe_out(shoe, model.match_pct(taste, shoe)) for shoe in ranked],
        "taste": taste,
        "swipe_count": await repo.get_swipe_count(user_id),
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
    }


@router.get("/taste")
async def taste(user_id: Annotated[str, Depends(current_user)]) -> dict[str, object]:
    return {
        "taste": await repo.get_taste(user_id),
        "swipe_count": await repo.get_swipe_count(user_id),
    }


@router.get("/saved")
async def saved(user_id: Annotated[str, Depends(current_user)]) -> dict[str, object]:
    taste = await repo.get_taste(user_id)
    shoes = await repo.list_saved(user_id)
    return {
        "items": [shoe_out(shoe, model.match_pct(taste, shoe)) for shoe in shoes],
    }


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
