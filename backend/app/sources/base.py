from dataclasses import dataclass
from typing import Protocol, Sequence

from app.taste.dims import TasteVec


@dataclass(frozen=True)
class Shoe:
    id: str
    name: str
    brand: str
    v: TasteVec
    image_url: str | None = None
    url: str | None = None
    notes: str | None = None


class ShoeSource(Protocol):
    def list_shoes(self) -> Sequence[Shoe]:
        ...
