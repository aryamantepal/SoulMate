# SoulMate — Feature Roadmap

A product-level view of what comes next, with effort/impact ratings and enough
context to pick up any item cold.

> **Current state (May 2026):** Core swipe loop, taste engine, Supabase persistence,
> real sneaker catalog, price/deals endpoint, and taste explainability are all shipped
> and deployed. The app is usable end-to-end but still missing the UX layer that turns
> a prototype into something people return to.

---

## How to read this

**Impact:** How much does this move the needle on retention / discovery quality?
**Effort:** Rough engineering time assuming one focused dev.
**Depends on:** What needs to exist first.

---

## 🔥 Tier 1 — Ship These Next

### 1. Onboarding Quiz (Cold-Start Fix)
**Impact: High | Effort: Small (2–4h)**

New users get a random-feeling feed until they've swiped ~10 times. A 5-card onboarding
quiz pre-seeds the taste vector so the first feed already feels personal.

**How:**
- Show 5 archetype shoes covering the extremes of the taste space:
  - Max retro + earthy (e.g. Clarks Wallabee)
  - Max techy + chunk (e.g. Hoka Tor Ultra)
  - Max loud (e.g. Salomon XT-6 Safari)
  - Max minimal + warm (e.g. Reebok Club C 85)
  - Max retro + loud (e.g. Puma Palermo)
- Collect binary yes/no, POST `/api/swipe` for each immediately
- Redirect to main feed — taste vector is now non-zero
- Flag onboarding complete in localStorage so it doesn't repeat

**Files to touch:** `frontend/src/App.tsx`, no backend changes needed.

---

### 2. Saved Shoes UI
**Impact: High | Effort: Small (2–3h)**

`/api/saved` already exists and returns saved shoes with match%. There's no UI to
browse them. Users who've liked shoes can't find them again.

**How:**
- Add a "Saved" tab or slide-out drawer next to the taste panel
- Fetch `GET /api/saved` on open, render a 2-col grid of shoe cards
- Show match%, brand, name, and a "View" link if `shoe.url` is set
- Optional: add a remove/unsave button (`DELETE /api/saved/:id` — needs a new route)

**Files to touch:** `frontend/src/App.tsx`, `frontend/src/App.css`, `backend/app/api/routes.py`.

---

### 3. Undo Last Swipe
**Impact: Medium | Effort: Tiny (1–2h)**

The most common "oops" moment in swipe UIs. Store the last swiped shoe in local state;
one tap puts it back and fires the compensating direction to the backend.

**How:**
- Keep `lastSwipe: { shoe, direction } | null` in state
- On undo: push shoe back to front of deck, POST `/api/swipe` with inverted direction
- Show an "Undo" button only when `lastSwipe` is non-null
- Clear `lastSwipe` after two swipes (can't undo further back)

**Files to touch:** `frontend/src/App.tsx` only.

---

### 4. Mobile Layout
**Impact: High | Effort: Small (2–4h)**

The `app-grid` is two columns and breaks below ~700px. Most shoe discovery happens
on phones.

**How:**
- Media query at 768px: stack deck + taste panel vertically
- Make taste panel collapsible on mobile (accordion)
- Ensure swipe cards fill the viewport width
- Test drag gestures on touch (should work — pointer events are already used)

**Files to touch:** `frontend/src/App.css`.

---

## 🧠 Tier 2 — Make the Taste Engine Smarter

### 5. Wire pgvector for Feed Ranking
**Impact: Medium | Effort: Small (2–3h) — migration already done**

`supabase/migrations/002_pgvector.sql` is applied: the `shoes` catalog table has a
`vector(7)` embedding column, an HNSW index, and a `match_shoes()` SQL helper.
The in-memory sort in `routes.py` works fine up to ~1000 shoes; after that, push
ranking into Postgres.

**How:**
- Populate `shoes.embedding` when loading catalog (convert `shoe.v` dict → float array)
- In `repo.py`, add `vector_feed(user_id, taste_vec, seen_ids, k=50)` that calls
  `match_shoes(query_embedding, k)` RPC
- Swap `routes.py:feed` to use it with a feature flag (`USE_PGVECTOR=true` env var)

**Files to touch:** `backend/app/sources/sneaker_db.py`, `backend/app/api/repo.py`, `backend/app/api/routes.py`.

---

### 7. Taste Reset + Manual Dimension Nudges
**Impact: Medium | Effort: Small (2–3h)**

Power users want to reset after exploring a style, or manually boost a dimension.

**How:**
- `DELETE /api/taste` — sets taste vector back to `zero_vec()` in `taste_vectors`
- `PATCH /api/taste` — accepts `{ dim: value }` partial update, merges with current vector
- Frontend: "Reset taste" button in taste panel; optional sliders per dimension

**Files to touch:** `backend/app/api/routes.py`, `backend/app/api/repo.py`, `frontend/src/App.tsx`.

---

## 📱 Tier 3 — Retention & Polish

### 8. Swipe History View
**Impact: Medium | Effort: Small (2–3h)**

Users can't see what they've passed on. The `swipes` table has full history.

**How:**
- `GET /api/swipes?direction=1` (liked) / `direction=-1` (passed) with pagination
- Frontend: "History" tab showing thumbnail grid, filterable by direction
- Bonus: "Unlike" action that fires a compensating swipe

### 9. Share Taste Profile
**Impact: Medium | Effort: Small (2–3h)**

Shareable read-only URL showing a user's taste card.

**How:**
- `GET /api/taste/share` — returns a signed token encoding the taste vector snapshot
- Public route `GET /api/taste/public/:token` — decodes and returns the snapshot (no auth)
- Frontend: `/taste/:token` route renders a read-only taste card

### 10. Price Drop Email Alerts
**Impact: High | Effort: Medium (4–6h)**

When `/api/deals` detects a drop, notify the user. Good retention loop.

**How:**
- Supabase Edge Function on a cron schedule (daily) calls `/api/deals` for each user
  with saved shoes (query `saved_shoes` for active users)
- If `price_drop: true`, send transactional email via Resend (`resend.com`) — free tier
  covers early traction
- Store last-notified price in `saved_shoes.notified_price` column to avoid repeat alerts

### 11. PWA / Installable
**Impact: Medium | Effort: Tiny (1h)**

Make the app installable on iOS/Android home screens.

**How:**
- Add `public/manifest.json` with icons and `display: standalone`
- Register a minimal service worker (Vite's `vite-plugin-pwa` handles this entirely)
- No logic changes needed

---

## 🔌 Tier 4 — Catalog & Data Scale

### 12. Additional Catalog Sources

| Source | Quality | Effort | Notes |
|---|---|---|---|
| Affiliate feeds (Awin/Impact) | High | Medium | Most reliable long-term; price-inclusive |
| GOAT unofficial API | High | Small | Large catalog; CDN images hotlinkable |
| StockX official API | High | Medium | Apply for access; real-time pricing |
| Nike/adidas product feeds | High | Medium | Official RSS/XML feeds exist |

Each source implements `list_shoes() -> list[Shoe]` behind the `ShoeSource` protocol in `base.py`. No core changes needed.

### 13. Catalog Balance Monitoring
**How:** `GET /api/admin/catalog/stats` returning count per brand, per dim quartile, and % with real images. Helps detect skew (e.g. too many retro shoes, no techy ones).

---

## 💡 Tier 5 — Bigger Bets (post-traction)

### AI Taste Blurbs
Use Claude to generate a personalized "why you'll love this" sentence for each shoe
in the feed response, based on the user's top 3 taste dimensions. Add as optional
`notes_personalized` field. Token cost is low at current scale.

### Style Personas
Cluster users into named archetypes ("the gorpcore explorer", "the clean minimalist",
"the retro purist") using k-means on `taste_vectors`. Show persona on profile page,
use as a discovery filter.

### Social Graph
"Your friend also saved this." Requires opt-in friend connections table and a social
`GET /api/feed/social` route that surfaces overlap. Keep it opt-in — privacy default off.

### Outfit Pairings
Given a saved shoe's taste vector, suggest complementary clothing using an affiliate
clothing catalog with compatible vectors. Separate catalog ingest, same taste space logic.

---

## Summary Table

| Feature | Tier | Impact | Effort | Status |
|---|---|---|---|---|
| Onboarding quiz | 1 | High | Small | Not started |
| Saved shoes UI | 1 | High | Small | Not started |
| Undo last swipe | 1 | Medium | Tiny | Not started |
| Mobile layout | 1 | High | Small | Not started |
| Wire pgvector | 2 | Medium | Small | Migration done |
| Taste reset + nudges | 2 | Medium | Small | Not started |
| Swipe history | 3 | Medium | Small | Not started |
| Share taste profile | 3 | Medium | Small | Not started |
| Price drop emails | 3 | High | Medium | Not started |
| PWA | 3 | Medium | Tiny | Not started |
| More catalog sources | 4 | High | Medium | Not started |
| AI taste blurbs | 5 | Medium | Medium | Not started |
| Style personas | 5 | Medium | Large | Not started |
