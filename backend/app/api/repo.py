from app.sources.base import Shoe
from app.taste.dims import TasteVec, zero_vec

_taste_by_user: dict[str, TasteVec] = {}
_swipe_count_by_user: dict[str, int] = {}
_seen_ids_by_user: dict[str, set[str]] = {}
_saved_by_user: dict[str, dict[str, Shoe]] = {}


async def get_taste(user_id: str) -> TasteVec:
    return dict(_taste_by_user.get(user_id, zero_vec()))


async def get_swipe_count(user_id: str) -> int:
    return _swipe_count_by_user.get(user_id, 0)


async def get_seen_ids(user_id: str) -> set[str]:
    return set(_seen_ids_by_user.get(user_id, set()))


async def record_swipe(
    user_id: str,
    shoe: Shoe,
    direction: int,
    taste: TasteVec,
) -> None:
    _taste_by_user[user_id] = dict(taste)
    _swipe_count_by_user[user_id] = _swipe_count_by_user.get(user_id, 0) + 1
    _seen_ids_by_user.setdefault(user_id, set()).add(shoe.id)

    if direction > 0:
        await save_shoe(user_id, shoe)


async def save_shoe(user_id: str, shoe: Shoe) -> None:
    _saved_by_user.setdefault(user_id, {})[shoe.id] = shoe


async def list_saved(user_id: str) -> list[Shoe]:
    return list(_saved_by_user.get(user_id, {}).values())
