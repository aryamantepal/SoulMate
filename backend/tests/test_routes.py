"""Route-level tests using FastAPI's TestClient.

Auth is stubbed via dependency_overrides and persistence falls back to the
in-memory repo (no Supabase env), so these run with zero external config.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

TEST_USER = "test-user-123"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    # Force the in-memory repo path: no Supabase, no external API key.
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("SNEAKER_DB_API_KEY", raising=False)

    # Reset in-memory state between tests so they don't leak into each other.
    from app.api import repo

    for store in (
        repo._taste_by_user,
        repo._swipe_count_by_user,
        repo._seen_ids_by_user,
        repo._saved_by_user,
        repo._collection_by_user,
    ):
        store.clear()

    from app import main
    from app.auth.supabase_auth import current_user

    main.app.dependency_overrides[current_user] = lambda: TEST_USER
    test_client = TestClient(main.app)
    yield test_client
    main.app.dependency_overrides.clear()


def _first_shoe(client: TestClient) -> dict:
    resp = client.get("/api/feed")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items, "feed should not be empty (seed catalog)"
    return items[0]


def test_health(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"ok": True}


def test_feed_requires_auth() -> None:
    from app import main

    # No dependency override here → real auth runs and rejects the request.
    with TestClient(main.app) as raw:
        assert raw.get("/api/feed").status_code == 401


def test_feed_shape(client: TestClient) -> None:
    body = client.get("/api/feed").json()
    assert "items" in body and "taste" in body and "persona" in body
    assert body["swipe_count"] == 0
    assert body["persona"]["name"] == "Fresh Explorer"  # cold start


def test_swipe_updates_taste_and_persona(client: TestClient) -> None:
    shoe = _first_shoe(client)
    resp = client.post("/api/swipe", json={"shoe_id": shoe["id"], "direction": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["swipe_count"] == 1
    assert "persona" in body
    assert any(v != 0 for v in body["taste"].values())


def test_swipe_zero_direction_rejected(client: TestClient) -> None:
    shoe = _first_shoe(client)
    resp = client.post("/api/swipe", json={"shoe_id": shoe["id"], "direction": 0})
    assert resp.status_code == 422


def test_swipe_unknown_shoe_404(client: TestClient) -> None:
    resp = client.post("/api/swipe", json={"shoe_id": "does-not-exist", "direction": 1})
    assert resp.status_code == 404


def test_save_and_collection_roundtrip(client: TestClient) -> None:
    shoe = _first_shoe(client)
    assert client.post("/api/saved", json={"shoe_id": shoe["id"]}).status_code == 200

    saved = client.get("/api/saved").json()["items"]
    assert any(s["id"] == shoe["id"] for s in saved)
    assert all(s["collection"] is None for s in saved)

    resp = client.put(
        f"/api/saved/{shoe['id']}/collection", json={"collection": "grails"}
    )
    assert resp.status_code == 200

    saved = client.get("/api/saved").json()["items"]
    match = next(s for s in saved if s["id"] == shoe["id"])
    assert match["collection"] == "grails"


def test_stats_reflect_swipes(client: TestClient) -> None:
    shoe = _first_shoe(client)
    client.post("/api/swipe", json={"shoe_id": shoe["id"], "direction": 1})
    body = client.get("/api/stats").json()
    # In-memory repo has no swipe timeline, so totals are 0, but the shape holds.
    assert set(body) >= {"total", "likes", "passes", "like_ratio", "top_dims"}


def test_taste_endpoint_has_persona(client: TestClient) -> None:
    body = client.get("/api/taste").json()
    assert "persona" in body and "taste" in body


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data/",
        "https://localhost/x.png",
        "http://images.stockx.com/a.png",
        "https://evil.com/?images.stockx.com",
        "https://stockx.com.evil.com/a.png",
        "file:///etc/passwd",
    ],
)
def test_image_proxy_rejects_disallowed_urls(client: TestClient, url: str) -> None:
    resp = client.get("/api/img", params={"url": url})
    assert resp.status_code == 400


def test_get_user_email_uses_admin_api(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio
    from types import SimpleNamespace

    from app.api import repo

    calls: list[str] = []

    async def get_user_by_id(uid: str) -> SimpleNamespace:
        calls.append(uid)
        return SimpleNamespace(user=SimpleNamespace(email="a@example.com"))

    fake = SimpleNamespace(auth=SimpleNamespace(admin=SimpleNamespace(get_user_by_id=get_user_by_id)))

    async def fake_supabase() -> SimpleNamespace:
        return fake

    monkeypatch.setattr(repo, "_supabase", fake_supabase)
    assert asyncio.run(repo.get_user_email("u1")) == "a@example.com"
    assert calls == ["u1"]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 100000}, {"direction": 0}, {"direction": 5}])
def test_swipe_history_rejects_bad_params(client: TestClient, params: dict) -> None:
    assert client.get("/api/swipes", params=params).status_code == 422
