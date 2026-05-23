import math
from typing import Protocol

from app.sources.base import Shoe
from app.taste.dims import DIMENSIONS, TasteVec


class TasteModel(Protocol):
    def update(
        self,
        taste: TasteVec,
        shoe: Shoe,
        direction: int,
        swipe_count: int,
    ) -> TasteVec:
        ...

    def score(self, taste: TasteVec, shoe: Shoe) -> float:
        ...

    def match_pct(self, taste: TasteVec, shoe: Shoe) -> int:
        ...


class LinearTaste:
    base_lr = 0.5
    decay = 0.15

    def update(
        self,
        taste: TasteVec,
        shoe: Shoe,
        direction: int,
        swipe_count: int,
    ) -> TasteVec:
        lr = self.base_lr / (1 + swipe_count * self.decay)
        next_taste = dict(taste)

        for dim in DIMENSIONS:
            next_taste[dim] = next_taste.get(dim, 0.0) + direction * lr * (
                shoe.v[dim] - 0.5
            )

        return next_taste

    def score(self, taste: TasteVec, shoe: Shoe) -> float:
        taste_norm = math.sqrt(sum(taste.get(dim, 0.0) ** 2 for dim in DIMENSIONS))
        shoe_norm = math.sqrt(sum(shoe.v[dim] ** 2 for dim in DIMENSIONS))
        if taste_norm == 0 or shoe_norm == 0:
            return 0.0

        dot = sum(taste.get(dim, 0.0) * shoe.v[dim] for dim in DIMENSIONS)
        return dot / (taste_norm * shoe_norm)

    def match_pct(self, taste: TasteVec, shoe: Shoe) -> int:
        pct = (self.score(taste, shoe) + 1) / 2 * 100
        return round(max(0, min(100, pct)))
