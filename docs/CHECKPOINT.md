# SoulMate — Checkpoint

For any agent or collaborator opening this repo cold. Read this first, then
`docs/SPEC.md` for decisions and math.

---

## Where we are — v2 (May 2026)

**The full core loop is shipped and deployed.**

- Swipe feed → taste vector learns → feed re-ranks → persists across sessions ✅
- Frontend live on Vercel; backend live on Render/Railway ✅
- Real sneaker catalog (thesneakerdatabase.dev, ~300 shoes) with seed fallback ✅
- Price/deals endpoint with frontend panel ✅
- Taste explainability ("Why this?" badges on active card) ✅
- Swipe writes consolidated into a single Postgres RPC ✅
- pgvector migration applied and ready for catalog-scale search ✅

What's not yet built: onboarding quiz, saved-shoes UI, swipe history, PWA, notifications, collaborative filtering. See `TODO.md` for the full next-steps list.

---

## Completion estimate

| Area | Done |
|---|---|
| Core swipe loop | 100% |
| Auth + persistence | 100% |
| Deployment / infra | 100% |
| Catalog integration | 70% (real API source done; pgvector wiring pending scale) |
| Product UX | 45% (feed + taste panel done; saved UI, onboarding, history missing) |
| Consumer polish | 30% (no PWA, no mobile layout, no notifications) |
| Collaborative / social | 5% (schema exists; no collaborative filtering yet) |

---

## Stack

| Layer | Tech | Where |
|---|---|---|
| Backend | FastAPI (Python), async | `backend/app/` |
| Taste model | Online linear, cosine ranking | `backend/app/taste/` |
| Sources | `ShoeSource` protocol + `SneakerDatabaseSource` + `MockSource` seed | `backend/app/sources/` |
| Persistence | `supabase-py` async (service role) + in-memory fallback | `backend/app/api/repo.py` |
| Auth | JWKS verification of Supabase access token | `backend/app/auth/supabase_auth.py` |
| Deals | Price-drop monitoring via sneaker DB market API | `backend/app/api/deals.py` |
| Frontend | React 19 + Vite + TS | `frontend/src/` |
| Auth client | `supabase-js` email/password | `frontend/src/supabase.ts` |
| Schema + RLS | `supabase/schema.sql` + `supabase/migrations/` | `supabase/` |

---

## Auth flow (load-bearing — don't change without reading this)

Frontend signs in with `supabase-js`, sends `Authorization: Bearer <access_token>`.

Backend in `supabase_auth.py`:
1. Fetches Supabase public keys once from `<SUPABASE_URL>/auth/v1/.well-known/jwks.json` (cached by `PyJWKClient`).
2. Verifies JWT signature locally with `pyjwt` (algos: `ES256`, `EdDSA`, `RS256`).
3. Returns `payload["sub"]` as user id.

**Why not `auth.get_user(token)`:** adds a network round-trip per request and was returning `403 Forbidden` on this project's gateway. JWKS is faster and Supabase-recommended for backend services.

Invariants:
- No `SUPABASE_JWT_SECRET` anywhere.
- Backend never trusts a client-sent user id.
- JWKS keys are cached (no network per request).

---

## Persistence

`repo.py` is a thin async layer over `supabase-py` with service-role key (bypasses RLS server-side). RLS still gates the public anon key as defense-in-depth.

`record_swipe` calls `public.record_swipe()` Postgres RPC — single round-trip that atomically writes profile, taste_vectors, swipes, and optionally saved_shoes.

In-memory dict fallback when env vars are unset — **don't remove it**, tests and offline dev depend on it.

Tables: `profiles`, `taste_vectors`, `swipes`, `saved_shoes`. All RLS-on.

---

## Catalog source

`SneakerDatabaseSource` (`backend/app/sources/sneaker_db.py`):
- Fetches ~300 shoes from `api.thesneakerdatabase.dev/v1/sneakers` on startup.
- `vec_from_metadata()` auto-generates taste vectors from name/brand/colorway using regex heuristics for the 7 dimensions.
- Falls back to `CATALOG` in `seed.py` if API is unreachable.
- Catalog cached in-process after first load; `ensure_loaded()` is idempotent.

To add a new source: implement `list_shoes() -> list[Shoe]` and `get_shoe(id) -> Shoe | None`, swap into `routes.py`.

---

## Known gotchas

**Cursor sandbox proxy:** Starting uvicorn from a Cursor terminal injects `HTTP_PROXY=http://127.0.0.1:60151` which blocks outbound to `*.supabase.co`. Fix:
```bash
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
uvicorn app.main:app --reload
```

**Vercel rootDirectory:** `vercel.json` sets `"rootDirectory": "frontend"` — Vercel must build from there, not the repo root, or vite won't be found.

---

## Run it locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
pytest                    # should be green
cp .env.example .env      # fill SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env.local  # fill VITE_API_BASE + VITE_SUPABASE_URL + VITE_SUPABASE_ANON_KEY
npm run dev
```

**Supabase migrations (run once in SQL editor):**
- `supabase/schema.sql` — base tables + RLS
- `supabase/migrations/001_record_swipe_rpc.sql` — consolidated swipe RPC
- `supabase/migrations/002_pgvector.sql` — pgvector extension + shoes table + HNSW index

---

## File map

```
backend/
  app/
    main.py                       FastAPI app, CORS, lifespan (catalog warm)
    api/
      routes.py                   /feed /swipe /taste /saved /deals
      repo.py                     supabase-py persistence + in-memory fallback
      deals.py                    price-drop monitoring, 30-min cache
    auth/
      supabase_auth.py            JWKS verification (no secret)
    sources/
      base.py                     Shoe dataclass + ShoeSource protocol
      mock.py                     MockSource (uses seed)
      seed.py                     15 hand-tuned seed shoes
      sneaker_db.py               SneakerDatabaseSource (real API + heuristic vectors)
      stubs.py                    ScrapeSource / SocialSource — deliberate stubs
    taste/
      dims.py                     7 dimensions, zero_vec()
      model.py                    LinearTaste (online linear, cosine)
  tests/
    test_model.py                 taste model tests
  requirements.txt                includes httpx>=0.27
frontend/
  src/
    App.tsx                       feed UI, login, drag/keys, why-dims, deals panel
    App.css
    supabase.ts                   supabase-js client
supabase/
  schema.sql                      base tables + RLS
  migrations/
    001_record_swipe_rpc.sql      single-RPC swipe writes
    002_pgvector.sql              pgvector + shoes catalog table + HNSW index
docs/
  SPEC.md                         product & technical decisions
  BUILD_PLAN.md                   original phased build log (phases 0-4 complete)
  CHECKPOINT.md                   you are here
  ROADMAP.md                      next feature ideas with effort/impact ratings
vercel.json                       rootDirectory=frontend build config
TODO.md                           live checklist
```

---

## Don'ts (load-bearing constraints)

- Don't reintroduce `SUPABASE_JWT_SECRET`. Asymmetric JWKS is the path.
- Don't put any Supabase service-role key in the frontend, ever.
- Don't make core feed/taste depend on scrape-based sources (`stubs.py` stays stubs).
- Don't mutate `record_swipe`'s Python signature without updating the RPC call in `repo.py` and the SQL function in `migrations/001`.
- Don't remove the in-memory fallback from `repo.py` — tests depend on it.
