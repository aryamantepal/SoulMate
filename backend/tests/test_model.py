import pytest

from app.sources.base import Shoe
from app.taste.dims import zero_vec
from app.taste.model import LinearTaste


def shoe_with(chunk: float, shoe_id: str = "shoe") -> Shoe:
    return Shoe(
        id=shoe_id,
        name=shoe_id,
        brand="Test",
        v={
            "chunk": chunk,
            "retro": 0.5,
            "warm": 0.5,
            "minimal": 0.5,
            "earthy": 0.5,
            "loud": 0.5,
            "techy": 0.5,
        },
    )


def test_right_swipe_raises_chunk_weight() -> None:
    model = LinearTaste()
    taste = model.update(zero_vec(), shoe_with(1.0), direction=1, swipe_count=0)

    assert taste["chunk"] > 0


def test_left_swipe_lowers_chunk_weight() -> None:
    model = LinearTaste()
    taste = model.update(zero_vec(), shoe_with(1.0), direction=-1, swipe_count=0)

    assert taste["chunk"] < 0


def test_lr_decays_with_swipe_count() -> None:
    model = LinearTaste()
    early = model.update(zero_vec(), shoe_with(1.0), direction=1, swipe_count=0)
    late = model.update(zero_vec(), shoe_with(1.0), direction=1, swipe_count=10)

    assert 0 < late["chunk"] < early["chunk"]


def test_ranking_orders_by_similarity() -> None:
    model = LinearTaste()
    chunky = shoe_with(1.0, "chunky")
    slim = shoe_with(0.0, "slim")
    taste = model.update(zero_vec(), chunky, direction=1, swipe_count=0)

    ranked = sorted([slim, chunky], key=lambda shoe: model.score(taste, shoe), reverse=True)

    assert [shoe.id for shoe in ranked] == ["chunky", "slim"]


def test_match_pct_in_0_to_100() -> None:
    model = LinearTaste()
    taste = model.update(zero_vec(), shoe_with(1.0), direction=1, swipe_count=0)
    pct = model.match_pct(taste, shoe_with(1.0))

    assert 0 <= pct <= 100


def test_cosine_of_identical_vectors_is_1() -> None:
    model = LinearTaste()
    shoe = Shoe(
        id="identical",
        name="Identical",
        brand="Test",
        v={
            "chunk": 0.1,
            "retro": 0.2,
            "warm": 0.3,
            "minimal": 0.4,
            "earthy": 0.5,
            "loud": 0.6,
            "techy": 0.7,
        },
    )

    assert model.score(shoe.v, shoe) == pytest.approx(1.0)


def test_zero_taste_keeps_source_order() -> None:
    model = LinearTaste()
    shoes = [shoe_with(0.2, "first"), shoe_with(0.8, "second")]

    ranked = sorted(shoes, key=lambda shoe: model.score(zero_vec(), shoe), reverse=True)

    assert [shoe.id for shoe in ranked] == ["first", "second"]
