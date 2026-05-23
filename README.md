# SoleMate 👟

A shoe-discovery app: swipe right/left, a legible taste model learns your
preferences, and profiles persist per user. (A price/deal agent is a deliberate
*future* phase — the architecture leaves room, v1 doesn't build it.)

This repo is a **scaffold built to be developed iteratively in Cursor.** The backend
spine is real and tested; the frontend and auth wiring are the phases you build.

## Stack
- **Backend:** FastAPI (Python) — owns the taste engine, sources, API. `backend/`
- **Frontend:** React (Vite + TS) — thin client. `frontend/`
- **Auth + DB:** Supabase (Postgres + Auth). Frontend holds the session; **backend
  verifies the JWT** on every protected request. RLS on as defense-in-depth.

## Start here
1. Read **`docs/SPEC.md`** — source of truth (decisions, taste math, API surface).
2. Read **`docs/BUILD_PLAN.md`** — phases 0→4 with a copy-paste Cursor prompt each.
   (v1 ends at Phase 4: swipe + taste + persistence. Agent is future.)
3. Open in Cursor, keep `docs/SPEC.md` in context, work **one phase per branch.**

## What's already real & verified
- `backend/app/taste/` — the taste model (dims, math, ranking). **7/7 pytest green.**
- `backend/app/sources/` — `ShoeSource` protocol, working `MockSource` + seed catalog
  (NB550 'Au Lait' grail lives here), honest scrape/social stubs.
- `backend/app/api/` — FastAPI routes for /feed /swipe /taste /saved, against an
  in-memory repo. **Backend boots and all endpoints respond** (verified with a signed
  test JWT; auth correctly 401s without one).
- `backend/app/auth/` — Supabase JWT verification dependency.
- `supabase/schema.sql` — tables + RLS.

## What you build (the phases)
- **Frontend** (Phase 0, 3) — Vite app + the swipe feed. Look/feel reference in
  `docs/REFERENCE_UI.jsx` (already wired to fetch from the API, not hardcoded).
- **Real persistence** (Phase 4) — swap `backend/app/api/repo.py`'s in-memory stub for
  Supabase queries (same signatures), wire supabase-js login on the frontend.

## What's intentionally NOT built
- Direct scraping of Nike/Adidas/NB and TikTok — **deliberate stubs**, read the
  docstring in `backend/app/sources/stubs.py` for why + the legit feed/affiliate path.
- The deal/price agent — future, schema's ready for it.

## Run the backend now
```bash
cd backend
pip install -r requirements.txt
pytest                       # 7/7 green
SUPABASE_JWT_SECRET=dev uvicorn app.main:app --reload
```
(For local calls without real auth, mint a dev JWT with that same secret and send it as
`Authorization: Bearer <token>`. Phase 4 replaces this with the Supabase session.)

## Architecture in one breath
React → FastAPI (`/api/*`) → lib (`taste` / `sources`). Everything swappable is behind
a protocol (`ShoeSource`, `TasteModel`) and persistence is behind `repo.py`, so no
phase can corner a later one.

## Honest notes
- Taste model is a deliberately simple online linear model, not a neural net — legible
  (you can show users *why*) and runs anywhere. Swap behind `TasteModel` later.
- Backend trusts the verified JWT, never a client-sent user id.
- Don't let the "song of the day with friends" idea leak in here — separate project.