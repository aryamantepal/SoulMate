# SoulMate — Living Roadmap

Current branch: `main`. Core loop, images, history, and catalog are all working end-to-end.

---

## ✅ Shipped

### Infrastructure & Deployment
- [x] Frontend deployed to Vercel (`vercel.json` rootDirectory set to `frontend/`)
- [x] Backend deployed to Render with env vars
- [x] CORS configured via `CORS_ORIGINS` env var
- [x] Supabase Auth + asymmetric JWKS token verification (no JWT secret)
- [x] Backend warm-ping on page load to reduce cold-start impact
- [x] "Waking up the server" message after 4s loading delay

### Core Loop
- [x] 7-dimensional taste vector with online linear learning
- [x] Cosine similarity ranking + match% scoring
- [x] Swipe feed with drag, arrow keys, and buttons
- [x] Deck refills only when < 2 cards remain (no flicker on fast swipes)
- [x] Per-user persistence (taste_vectors, swipes, saved_shoes) in Postgres
- [x] RLS on all tables
- [x] Email/password auth (Supabase)
- [x] Undo last swipe (compensating API call + deck restore)
- [x] In-memory fallback when Supabase env is unset

### Catalog & Images
- [x] KicksDB API (`kicks.dev`) for real sneaker catalog with images
- [x] `vec_from_metadata()` — heuristic taste vector from shoe name/brand/colorway
- [x] 60-shoe seed catalog as fallback
- [x] Image proxy endpoint (`GET /api/img`) to bypass CDN hotlink blocking
- [x] Local seed images for 15 hero shoes in `public/shoes/`
- [x] `ShoeImage` component with brand-initials fallback on all cards

### Product Features
- [x] Style quiz onboarding — 5-archetype cold-start seeder
- [x] Taste explainability — "Why this?" dimension badges on active card
- [x] Saved shoes grid panel
- [x] Swipe history panel with Liked / Passed filter tabs
- [x] Swipe history backfill from saved shoes (recovers pre-migration data)
- [x] Price/deals panel — `GET /api/deals` with 30-min cache, price drop flagging
- [x] Taste reset — clears taste + seen + shows onboarding quiz
- [x] Shuffle again — clears seen history, reloads feed (with fresh token fix)
- [x] Swipe RPC — `public.record_swipe()` PL/pgSQL (1 round-trip vs 3)
- [x] pgvector migration applied — `vector(7)` column, HNSW index ready

---

## 🔜 Next Up — High Impact

### UX
- [ ] **Shoe detail modal** — tap card image to expand with larger photo, full dim scores, "Why this?" breakdown, and StockX/GOAT link
- [ ] **Share taste profile** — shareable `/taste/abc123` showing a read-only taste card. Static snapshot, no auth to view.
- [ ] **Dimension weighting sliders** — let users manually nudge taste dims in the taste panel. Good power-user escape hatch.

### Catalog
- [ ] **Periodic catalog refresh** — re-warm KicksDB cache on a schedule so new drops appear without a backend restart
- [ ] **Catalog admin endpoint** — `GET /api/admin/catalog/stats` with source, count, dim coverage. Helps tune catalog balance.

### Taste Model
- [ ] **Wire pgvector for feed ranking** — replace in-memory sort with `match_shoes()` RPC. Only worth it at catalog > ~1000 shoes.

---

## 🔔 Notifications & Engagement

- [ ] **Price drop email alerts** — when `/api/deals` detects a drop, send transactional email via Resend/Postmark
- [ ] **"New arrivals" badge** — show badge on feed if shoes added since last visit
- [ ] **Weekly taste recap** — scheduled email with swipe stats, top dims, 3 picks

---

## 🏗️ Infrastructure

- [ ] **Error monitoring** — Sentry on frontend (`@sentry/react`) and backend (`sentry-sdk`)
- [ ] **Backend route tests** — `test_routes.py` with `httpx.AsyncClient`
- [ ] **Staging environment** — Vercel preview + Render staging on a separate Supabase project

---

## 💡 Bigger Ideas (post-traction)

- [ ] **AI taste blurbs** — use Claude to generate "why you'll love this" per shoe based on top taste dims
- [ ] **Style personas** — cluster users into archetypes ("gorpcore explorer", "clean minimalist") from their taste vector
- [ ] **Friend comparisons** — "Your friend Alex also saved this." Requires social graph + opt-in
- [ ] **Outfit pairings** — given a saved shoe, suggest complementary pieces from an affiliate clothing catalog
