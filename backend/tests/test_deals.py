from app.api.deals import _best_match, _is_match


def test_exact_and_superset_titles_match() -> None:
    assert _is_match("New Balance 9060 Sea Salt", "New Balance 9060 Sea Salt")
    assert _is_match("New Balance 9060 Sea Salt", "New Balance 9060 'Sea Salt' (2023)")


def test_unrelated_same_brand_product_does_not_match() -> None:
    assert not _is_match("New Balance 9060 Sea Salt", "New Balance 550 White Green")


def test_best_match_returns_none_instead_of_first_result() -> None:
    results = [{"title": "Nike Dunk Low Panda"}, {"title": "Nike Air Force 1 White"}]
    assert _best_match("Nike Air Max 1 Crepe Hemp", results) is None


def test_best_match_picks_matching_result() -> None:
    results = [{"title": "Nike Dunk Low Panda"}, {"name": "Nike Air Max 1 Crepe Hemp"}]
    assert _best_match("Nike Air Max 1 Crepe Hemp", results) == results[1]
