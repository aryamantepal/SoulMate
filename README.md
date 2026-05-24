# SoleMate

A shoe-discovery app: swipe right/left, a legible taste model learns your
preferences, and profiles persist per user. (A price/deal agent is a deliberate
*future* phase — the architecture leaves room, v1 doesn't build it.)

## Stack
- **Backend:** FastAPI (Python) — owns the taste engine, sources, API. `backend/`
- **Frontend:** React (Vite + TS) — thin client. `frontend/`
- **Auth + DB:** Supabase (Postgres + Auth). Frontend signs in with `supabase-js`
  (magic link); the backend hands the access token to **Supabase Auth**
  (`auth.get_user(token)` via `supabase-py`) and trusts the user id Supabase
  returns. No JWT secrets on our side. RLS on as defense in depth.

## Start here
1. Read **`docs/SPEC.md`** — source of truth (decisions, taste math, API surface).
2. Read **`docs/BUILD_PLAN.md`** — phases 0→4 with a copy-paste Cursor prompt each.
3. Keep `docs/SPEC.md` in context, work **one phase per branch.**

## What's real & verified
- `backend/app/taste/` — taste model (dims, math, ranking). **7/7 pytest green.**
- `backend/app/sources/` — `ShoeSource` protocol, `MockSource` + seed catalog
  (NB550 'Au Lait' lives here), honest scrape/social stubs.
- `backend/app/api/` — FastAPI routes for `/feed`, `/swipe`, `/taste`, `/saved`,
  on an async Supabase repo (with an in-memory fallback when env is unset).
- `backend/app/auth/supabase_auth.py` — verifies the bearer token by calling
  Supabase Auth; never decodes the JWT itself.
- `frontend/src/App.tsx` — magic-link login + drag/arrow-key swipe feed +
  live taste panel.
- `supabase/schema.sql` — tables + RLS.

## What's intentionally NOT built
- Direct scraping of Nike/Adidas/NB and TikTok — **deliberate stubs**, see
  `backend/app/sources/stubs.py`.
- The deal/price agent — future, schema's ready for it.

## Run it

Backend:

```bash
cd backend
pip install -r requirements.txt
pytest                                  # 7/7 green
cp .env.example .env                    # then fill SUPABASE_URL / ANON / SERVICE keys
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env.local              # then fill VITE_SUPABASE_URL / ANON_KEY
npm run dev
```

Then open the Vite URL, request a magic link, click it, and start swiping. The
backend asks Supabase to verify the access token on every protected call.

## Architecture in one breath
React → FastAPI (`/api/*`) → lib (`taste` / `sources`) → Supabase. Everything
swappable is behind a protocol (`ShoeSource`, `TasteModel`) and persistence is
behind `repo.py`, so no phase can corner a later one.

## Honest notes
- Taste model is a deliberately simple online linear model, not a neural net —
  legible (you can show users *why*) and runs anywhere. Swap behind `TasteModel`
  later.
- Backend trusts the user id Supabase returns from the access token, never a
  client-sent user id.
- Service-role key is backend-only; never ship it to the browser.