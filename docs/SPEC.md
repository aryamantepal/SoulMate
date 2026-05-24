# SOLEMATE — Product & Technical Spec

> A shoe-discovery app: swipe right/left on shoes, a legible taste model learns your
> preferences, and profiles persist per user. (A price/deal agent is a FUTURE phase —
> the architecture leaves room for it but v1 does NOT build it.)

This document is the **source of truth**. When prompting Cursor, reference it:
"per docs/SPEC.md, implement ...". Keep it updated as decisions change.

---

## 1. The Pitch

Generic search is bad at "special" (the NB550 'Au Lait' problem). SoleMate turns
discovery into a swipe feed, learns your taste as a vector in feature space, and
remembers it per user across sessions.

## 2. Stack (decided)

- **Backend:** FastAPI (Python). Owns the taste engine, sources, and all logic.
- **Frontend:** React (Vite + TypeScript). Thin client — renders the feed, sends swipes.
- **Auth + DB:** Supabase (Postgres + Auth + Storage). Frontend holds the session;
  the backend hands the access token to **Supabase Auth** (`auth.get_user(token)`
  via `supabase-py`) and trusts the user id Supabase returns. No JWT secret on our
  side. RLS still on, as defense in depth.
- **Split contract:** frontend and backend talk over a versioned REST API (`/api/...`).
  The OpenAPI schema FastAPI generates is the integration contract.

## 3. Core Loops (v1)

1. **Swipe loop** — card in, swipe right (want) / left (pass). Each swipe updates the
   taste vector (server-side canonical), feed re-ranks by similarity.
2. **Taste loop** — taste vector persists to the user's profile; sharpens over sessions;
   user can inspect it ("why am I seeing this?").

(Shopping/deal loop = future, see §9.)

## 4. Feature Dimensions (the taste space)

Every shoe is a vector over these axes (0..1). The user's taste vector lives in the
same space and can go negative ("actively dislikes chunky"). Defined ONCE in
`backend/app/taste/dims.py`; adding a dim is a one-file change + a catalog re-embed.

| dim     | low ........... high                |
|---------|-------------------------------------|
| chunk   | flat/slim ....... maximal/dad       |
| retro   | modern .......... heritage/vintage  |
| warm    | cool/grey ....... warm/brown/cream  |
| minimal | busy/loud ....... clean/simple      |
| earthy  | synthetic ....... natural/suede/gum |
| loud    | subtle .......... statement         |
| techy   | classic ......... performance/gorp  |

## 5. Taste Model (legible, server-side)

Online preference learning, fully inspectable (no black box):

- taste vector starts at 0 (neutral).
- on swipe of shoe `s`, direction `d ∈ {+1,-1}`:
  `taste[k] += d * lr * (s.v[k] - 0.5)` per dim (centered at 0.5 so a left-swipe on a
  chunky shoe pushes taste *away* from chunk).
- decaying lr: `lr = base / (1 + n*decay)`, `n` = total swipes.
- ranking: `score(s) = cosine(s.v, taste)`; match% = `(cos+1)/2*100`.

Lives in `backend/app/taste/model.py`, behind a `TasteModel` protocol so a fancier
model can swap in later. Has pytest coverage (Phase 1 target).

## 6. Sources (the honest part)

Direct-scraping Nike/Adidas/NB + TikTok is fragile and ToS-violating; nothing core may
depend on it. Sources are pluggable behind one `ShoeSource` protocol
(`backend/app/sources/base.py`):

- `MockSource` — local seed catalog. Always works. Default. **Build first.**
- `FeedSource` — retailer product feeds / affiliate / sneaker APIs. Legit, stable,
  often price-inclusive. **Future.**
- `ScrapeSource` / `SocialSource` — STUBS with risk notes. Opt-in, your legal call.
  Do NOT make core features depend on them.

Embedding (assigning the feature vector) is a separate step (`taste/embed.py`) so
sources stay dumb.

## 7. Auth & Profiles (Supabase, split-stack flavor)

- Frontend uses `supabase-js` for magic-link login; holds the session + access token.
- Frontend sends `Authorization: Bearer <token>` on API calls.
- **Backend asks Supabase Auth to verify that token** (`backend/app/auth/supabase_auth.py`
  calls `supabase.auth.get_user(token)`) and derives `user_id` from the response — it
  trusts what Supabase says, not a client-sent user id. No JWT secret on the backend.
- Tables: `profiles`, `taste_vectors`, `swipes`, `saved_shoes`. RLS on all (defense in
  depth even though the API is the main gate). See `supabase/schema.sql`.
- Taste vector canonical copy = server (Postgres). Client keeps a live copy for snappy
  UI, syncs on swipe.

## 8. API Surface (v1)

FastAPI routes (`backend/app/api/`), all under `/api`:
- `GET  /api/feed` — next batch of shoes, ranked by the caller's taste. (auth)
- `POST /api/swipe` — `{shoe_id, direction}`; persists swipe + updated taste. (auth)
- `GET  /api/taste` — the caller's current taste vector + swipe count. (auth)
- `GET  /api/saved` / `POST /api/saved` — list/add saved shoes. (auth)
- `GET  /api/health` — liveness, no auth.

## 9. Future (explicitly NOT v1)

- Price/deal agent + MCP tools. Schema already has `saved_shoes`; a `DealAgent`
  protocol can slot in behind a `/api/deals` route later. Don't build it now.
- DeepSeek enrichment (taste blurbs, query gen). Later.
- Real `FeedSource`. Later.
- "Song of the day with friends" — SEPARATE project, keep it out of here.

## 10. Non-Negotiables

- Backend owns logic; frontend stays thin.
- Sources pluggable; nothing core depends on scraping.
- Taste model legible and inspectable.
- Backend verifies tokens via Supabase Auth; never trusts a client-supplied user id.
  RLS on every table.
- No secrets in frontend. Supabase service key + any future API keys are backend-only.