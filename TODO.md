# SoulMate — Living Roadmap

Current branch: `main`. All v1 infrastructure and v2 scaling work is shipped.
The app is deployed end-to-end and the core loop is complete.

---

## ✅ Shipped (v1 + v2)

### Infrastructure & Deployment
- [x] Frontend deployed to Vercel (`vercel.json` rootDirectory set to `frontend/`)
- [x] Backend deployed to Render/Railway with env vars
- [x] CORS configured via `CORS_ORIGINS` env var
- [x] Supabase Auth URL configuration

### Core Loop
- [x] 7-dimensional taste vector with online linear learning
- [x] Cosine similarity ranking + match% scoring
- [x] Swipe feed with drag, arrow keys, and buttons
- [x] Per-user persistence (taste_vectors, swipes, saved_shoes) in Postgres
- [x] RLS on all tables; asymmetric JWKS token verification (no JWT secret)
- [x] Email/password auth (Supabase)
- [x] Silent feed reloads after swipe
- [x] In-memory fallback when Supabase env is unset

### Scaling & Optimizations
- [x] `SneakerDatabaseSource` — real catalog from thesneakerdatabase.dev with seed fallback
- [x] `vec_from_metadata()` — heuristic taste vector from shoe name/brand/colorway
- [x] Swipe RPC — `public.record_swipe()` PL/pgSQL function (1 round-trip vs 3)
- [x] pgvector migration — `vector(7)` column, HNSW index, `match_shoes()` helper ready

### Product Features
- [x] Taste explainability — "Why this?" dimension badges on active card
- [x] Price/deals endpoint — `GET /api/deals` with 30-min cache, price drop flagging
- [x] Deals UI panel — "Price drops" toggle in session bar

---

## 🔜 Next Up — High Impact, Low Effort

### Onboarding (cold-start fix)
- [ ] **Style quiz on first visit** — 5-card "pick your vibe" screen that pre-seeds the taste vector before the swipe feed loads. Eliminates the cold-start problem where new users see a random-feeling feed.
  - Show 5 archetype shoes (max-retro, max-techy, max-earthy, max-loud, max-minimal)
  - Collect binary yes/no, call `/api/swipe` for each, redirect to feed

### Saved Shoes UI
- [ ] **Saved tab / shelf view** — grid of saved shoes using the existing `/api/saved` endpoint. Currently data is persisted but there's no UI to browse it.
  - Add a tab or slide-out panel to `App.tsx`
  - Show match% + "View on StockX" link if `shoe.url` is set

### Undo Last Swipe
- [ ] **Undo button** — store the last swiped shoe in local state; one tap re-inserts it at the front of the deck and fires a compensating swipe in the opposite direction to the backend.

---

## 🧠 Taste Model Improvements

- [ ] **Collaborative filtering layer** — find users with similar taste vectors (cosine distance on `taste_vectors` table), blend their liked shoes into the feed for discovery beyond the solo taste vector. Pure SQL query, no new infra.
- [ ] **Wire pgvector for feed ranking** — now that `supabase/migrations/002_pgvector.sql` is applied, add a `match_shoes(query_embedding, k)` RPC call path in `repo.py` to replace the in-memory sort in `routes.py:feed`. Only worth it when catalog > ~1000 shoes.
- [ ] **Taste reset** — `DELETE /api/taste` endpoint + a "Reset my taste" button in the UI. Useful for trying a different style persona.
- [ ] **Dimension weighting UI** — sliders in the taste panel that let users manually nudge dimensions (writes directly to taste_vectors). Good power-user escape hatch.

---

## 📱 UX & Polish

- [ ] **Swipe history view** — paginated list of past swipes with direction, shoe thumbnail, and date. Backed by the existing `swipes` table.
- [ ] **Share taste profile** — generate a shareable URL like `/taste/abc123` that shows a read-only taste card ("82% retro · 71% earthy · 68% warm"). Static snapshot, no auth required to view.
- [ ] **Keyboard shortcut cheatsheet** — small tooltip or `?` modal listing arrow keys, `s` for save, `u` for undo.
- [ ] **PWA manifest** — `manifest.json` + service worker so the app is installable on mobile. Vite makes this a 30-minute addition.
- [ ] **Responsive / mobile layout** — current `app-grid` is desktop-first. Add a single-column stacked layout below 768px.
- [ ] **Shoe detail expand** — tap the card image to open a modal with larger photo, all 7 dim scores visualized, and the "Why this?" breakdown.

---

## 🔌 Catalog & Data

- [ ] **More catalog sources** — implement additional `ShoeSource` classes:
  - Affiliate product feeds (Awin, Impact, Skimlinks) — most reliable, price-inclusive
  - GOAT unofficial API — large catalog, CDN-hotlinkable images
  - StockX API (apply for access) — real-time pricing data
- [ ] **Catalog admin endpoint** — `GET /api/admin/catalog/stats` returning source, count, and coverage per taste dimension. Helps tune the catalog balance.
- [ ] **Periodic catalog refresh** — cron job (or Render scheduled task) to re-warm the `SneakerDatabaseSource` cache daily and detect new drops.

---

## 🔔 Notifications & Engagement

- [ ] **Price drop email alerts** — when `/api/deals` detects a drop on a saved shoe, send a transactional email via Resend/Postmark. Supabase Edge Functions are the easiest trigger.
- [ ] **"New arrivals" badge** — track catalog fetch timestamps; show a badge on the feed if shoes have been added since the user's last visit.
- [ ] **Weekly taste recap** — scheduled email summarizing swipe stats, top dims, and 3 recommendations. Good retention hook.

---

## 🏗️ Infrastructure & DX

- [ ] **OpenAPI client generation** — run `openapi-generator` against the FastAPI `/openapi.json` to auto-generate the TypeScript `request()` helpers in the frontend. Eliminates manual type duplication.
- [ ] **Backend tests for routes** — `test_routes.py` with `httpx.AsyncClient` against the FastAPI app. Currently only taste model math is tested.
- [ ] **Staging environment** — separate Vercel preview + Render staging service pointed at a non-production Supabase project.
- [ ] **Error monitoring** — add Sentry to both frontend (`@sentry/react`) and backend (`sentry-sdk`) for production error tracking.

---

## 💡 Bigger Ideas (post-traction)

- [ ] **AI taste blurbs** — use Claude to generate a one-sentence "why you'll love this" for each shoe based on the user's top taste dims. Add as a `notes_personalized` field in the feed response.
- [ ] **Friend comparisons** — "Your friend Alex also saved this." Requires a social graph table and opt-in.
- [ ] **Style personas** — cluster users into named archetypes ("the gorpcore explorer", "the clean minimalist") based on their taste vector. Show on profile page.
- [ ] **Outfit pairings** — given a saved shoe, suggest complementary pieces using an affiliate clothing catalog with compatible taste vectors.
