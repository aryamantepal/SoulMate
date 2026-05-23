from typing import TypeAlias

DIMENSIONS: tuple[str, ...] = (
    "chunk",
    "retro",
    "warm",
    "minimal",
    "earthy",
    "loud",
    "techy",
)

TasteVec: TypeAlias = dict[str, float]


def zero_vec() -> TasteVec:
    return {dim: 0.0 for dim in DIMENSIONS}
