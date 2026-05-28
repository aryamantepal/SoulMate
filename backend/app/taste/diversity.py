"""Inject off-taste "wildcard" shoes into a ranked feed.

Without this, a strong taste vector collapses the feed into near-identical
shoes. Once a user's taste is established we sprinkle in shoes from the lower
half of the ranking so discovery stays fresh, while keeping best matches
dominant up top.
"""

from __future__ import annotations

import random
from typing import TypeVar

T = TypeVar("T")


def diversify(
    ranked: list[T],
    swipe_count: int,
    every: int = 4,
    min_swipes: int = 8,
) -> list[T]:
    """Return ranked with a wildcard from the lower half inserted every `every`th slot.

    No-op until the taste signal is meaningful (`swipe_count >= min_swipes`) or
    when there aren't enough shoes to make injection worthwhile.
    """
    n = len(ranked)
    if swipe_count < min_swipes or n < every * 2:
        return ranked

    boundary = n // 2
    top = ranked[:boundary]
    tail = ranked[boundary:]
    random.shuffle(tail)

    result: list[T] = []
    wi = 0
    for pos, shoe in enumerate(top, start=1):
        result.append(shoe)
        if pos % every == 0 and wi < len(tail):
            result.append(tail[wi])
            wi += 1

    result.extend(tail[wi:])
    return result
