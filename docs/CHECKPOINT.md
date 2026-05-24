# SoleMate — checkpoint

For another agent (or future-you) opening this repo cold. Read this first, then
`docs/SPEC.md` and `docs/BUILD_PLAN.md` for deeper context.

## Where we are

**v1 is shipped end-to-end.** Phases 0–4 of the build plan are done:

- Backend serves `/api/health`, `/api/feed`, `/api/swipe`, `/api/taste`,
  `/api/saved`. Auth-gated routes 401 cleanly without a token.
- Frontend signs in with Supabase magic-link, sends the access token, renders
  a draggable swipe card stack with a live taste panel and ranked match%.
- Taste vector, swipes, saves persist in Supabase Postgres. Reload survives.
  RLS gates cross-user reads.
- 7/7 backend tests green.

What's not v1, by design: real product image URLs, real shoe catalog (the
`MockSource` seed has 15 shoes), the price/deal agent.

## Stack

| Layer        | Tech                                       | Where                               |
| ------------ | ------------------------------------------ | ----------------------------------- |
| Backend      | FastAPI (Python), async                    | `backend/app/`                      |
| Taste model  | Online linear, cosine ranking              | `backend/app/taste/`                |
| Sources      | `ShoeSource` protocol + `MockSource` seed  | `backend/app/sources/`              |
| Persistence  | `supabase-py` async client (service role)  | `backend/app/api/repo.py`           |
| Auth         | JWKS verification of Supabase access token | `backend/app/auth/supabase_auth.py` |
| Frontend     | React 19 + Vite + TS                       | `frontend/src/`                     |
| Auth client  | `supabase-js` magic-link                   | `frontend/src/supabase.ts`          |
| Schema + RLS | `supabase/schema.sql` (already applied)    | `supabase/`                         |

## Auth flow (important — don't "fix" it)

The frontend signs in with `supabase-js`, holds the session, and sends
`Authorization: Bearer <access_token>` on every API call.

The backend **does not decode the JWT with a shared secret**. It does this
instead, in `backend/app/auth/supabase_auth.py`:

1. Fetches Supabase's public keys once from
   `<SUPABASE_URL>/auth/v1/.well-known/jwks.json` (cached by `PyJWKClient`).
2. Verifies the JWT signature locally with `pyjwt` (algos: `ES256`, `EdDSA`,
   `RS256` — Supabase uses asymmetric signing on modern projects).
3. Returns `payload["sub"]` as the user id.

Why this and not `supabase.auth.get_user(token)`:

- Modern Supabase projects sign tokens asymmetrically. `auth.get_user` hits
  `/auth/v1/user` over HTTP, which adds a network round-trip per request and
  was returning `403 Forbidden` against this project (apikey/JWT pairing on
  the new gateway is finicky). JWKS verification is simpler, faster, and the
  Supabase-recommended path for backend services.
- No `SUPABASE_JWT_SECRET` anywhere — keys are public.

If you change auth, keep these invariants:

- No JWT secret in env.
- Backend never trusts a client-sent user id.
- Verification works without a network round-trip per request (cache JWKS).

## Persistence

`backend/app/api/repo.py` is a thin async layer over `supabase-py` using the
**service-role key** (bypasses RLS server-side). RLS still gates the public
anon key as defense-in-depth.

Same module has an in-memory dict fallback when `SUPABASE_URL` /
`SUPABASE_SERVICE_ROLE_KEY` are unset, so tests and offline dev still work.
**Don't remove the fallback.**

Tables (see `supabase/schema.sql`, already applied to the project):
`profiles`, `taste_vectors`, `swipes`, `saved_shoes`. All RLS-on with
`auth.uid() = user_id`.

## Known gotcha — Cursor sandbox proxy

If you start uvicorn from a Cursor terminal, the sandbox injects
`HTTP_PROXY=http://127.0.0.1:60151` (and `HTTPS_PROXY`, `ALL_PROXY`, …) into
the env. That proxy blocks outbound to `*.supabase.co`, so:

- JWKS fetch → `urlopen error Tunnel connection failed: 403 Forbidden`
- Any supabase-py REST call → same 403

**Fix:** start uvicorn from a regular Terminal app, OR `unset` the proxy vars
before launch:

```bash
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
uvicorn app.main:app --reload
```

This is a *Cursor sandbox* artifact, not a code issue — production never
sees it.

## Run it

Backend:

```bash
cd backend
pip install -r requirements.txt
pytest                 # 7/7 green
# fill .env with SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
# fill .env.local with VITE_API_BASE + VITE_SUPABASE_URL + VITE_SUPABASE_ANON_KEY
npm run dev
```

## Image rendering — current state

Each seed shoe has an `image_url` pointing at a `placehold.co` placeholder
(per-shoe color theme, shoe name as text). The frontend renders the image in
`.shoe-art` (220px tall, `object-fit: cover`), falling back to brand initials
when `image_url` is null.

To swap in real product photos, just edit `backend/app/sources/seed.py` and
replace any `image_url=_placeholder(...)` line with `image_url="https://..."`
pointing at a direct image URL. No frontend or backend code changes needed.

## What's next (not v1, but ready to slot in)

The architecture explicitly leaves room for these — none of them require
re-touching auth, taste, or schema:

1. **Real catalog with real product photos.** Implement a `ShoeSource` against
   a real catalog API behind the same protocol as `MockSource`. Options:
   - **The Sneaker Database** (`thesneakerdatabase.dev`) — community API,
     direct image URLs, free tier.
   - **StockX** — official API exists (apply for access); URLs are hashed so
     hotlinking guesses don't work, but the API returns the URL.
   - **GOAT / KicksCrew** — unofficial endpoints; hotlinkable CDNs.
   - **Affiliate product feeds** (Awin, Skimlinks, Impact) — most reliable
     long-term, often price-inclusive.
   Wire as `backend/app/sources/feed.py` exposing `list_shoes()`. Embed each
   shoe into the taste vector via `backend/app/taste/embed.py` (file slot
   already named in `docs/SPEC.md`).

2. **Price/deal agent.** Schema already has `saved_shoes`. Add a `DealAgent`
   protocol behind a new `/api/deals` route. Good place for DeepSeek (or
   similar) to generate retailer queries from the shoe object and summarize
   stock/price across sources.

3. **Taste explainability UI.** `/api/taste` already returns the vector and
   swipe count; the frontend renders bars. Next step is a "why am I seeing
   this?" tooltip per card that diffs the shoe's vector against the user's
   taste vector and surfaces the top contributing dims.

4. **Persistence polish.** `record_swipe` currently issues three sequential
   POSTs (profile upsert, taste_vectors upsert, swipes insert). Consolidate
   into a single Postgres function (`rpc.record_swipe`) when this is the
   bottleneck — not before.

## Don'ts (load-bearing constraints)

- Don't reintroduce `SUPABASE_JWT_SECRET`. Asymmetric is the path.
- Don't put any Supabase service-role key in the frontend, ever.
- Don't make core features (feed, taste) depend on scrape-based sources. The
  `ScrapeSource` / `SocialSource` stubs in `backend/app/sources/stubs.py`
  exist as deliberate non-defaults.
- Don't mutate `record_swipe`'s signature without updating
  `backend/app/api/routes.py` accordingly. It now takes
  `next_swipe_count` so we don't double-fetch the count.
- Don't merge "song of the day with friends" — it's a separate project.

## File map (the parts you'll actually touch)

```
backend/
  app/
    main.py                       FastAPI app, CORS, /api/health
    api/
      routes.py                   /feed /swipe /taste /saved
      repo.py                     supabase-py persistence + in-memory fallback
    auth/
      supabase_auth.py            JWKS verification (no secret)
    sources/
      base.py                     Shoe dataclass + ShoeSource protocol
      mock.py                     MockSource (uses seed)
      seed.py                     15 hand-tuned shoes (taste vectors)
      stubs.py                    ScrapeSource / SocialSource — deliberate stubs
    taste/
      dims.py                     7 dimensions, zero_vec()
      model.py                    LinearTaste (online linear, cosine)
  tests/
    test_model.py                 7 tests, all green
  requirements.txt
  .env.example                    SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY
frontend/
  src/
    App.tsx                       feed UI + magic-link login + drag/keys
    App.css
    supabase.ts                   supabase-js client (anon key)
  .env.example                    VITE_API_BASE + VITE_SUPABASE_URL/ANON_KEY
supabase/
  schema.sql                      tables + RLS (already applied)
docs/
  SPEC.md                         source of truth (decisions, math)
  BUILD_PLAN.md                   phases 0→4 with prompts
  CHECKPOINT.md                   you are here
  REFERENCE_UI.jsx                early UI sketch (do not import)
```
