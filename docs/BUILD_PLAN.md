# BUILD PLAN — phased, with Cursor prompts

Split stack: **FastAPI backend** owns logic, **React frontend** is a thin client.
Build in order; each phase is runnable and testable. Copy the prompt into Cursor,
let it work, verify "Done when," move on. **One phase per branch.** Keep
`docs/SPEC.md` in context every time.

The taste engine (Phase 1) and the API endpoints (Phase 2) already exist and PASS —
backend boots, endpoints respond, 7/7 model tests green. So your early phases are
mostly "confirm it runs in your env" rather than "write from scratch."

---

## Phase 0 — Boot both halves
**Goal:** `uvicorn` serves the API; `npm run dev` serves the React app; they talk.

> Cursor prompt:
> "Read docs/SPEC.md. The backend/ FastAPI app already exists and runs. Set up the
> frontend/ as a Vite + React + TypeScript app. Create a minimal home page that calls
> GET /api/health (base URL from VITE_API_BASE) and shows the result. Wire CORS is
> already done backend-side. Don't build the feed yet."

**Done when:** Frontend page shows `{ ok: true }` fetched from the backend.

---

## Phase 1 — Taste engine (already built; just verify)
**Goal:** Confirm the model runs and tests pass in your environment.

> Cursor prompt (only if you want to extend it):
> "Per docs/SPEC.md §5, the taste model is in backend/app/taste/. Run `pytest` and
> confirm green. If you change the math, update backend/tests/test_model.py to match."

**Done when:** `cd backend && pytest` → all pass.

---

## Phase 2 — API + mock source (already built; verify & extend)
**Goal:** /feed, /swipe, /taste, /saved work against the mock source + in-memory repo.

> Cursor prompt:
> "Per docs/SPEC.md §8, the routes in backend/app/api/routes.py are implemented against
> a mock source and an in-memory repo (backend/app/api/repo.py). Run the backend and
> hit the endpoints with a test JWT. Don't change route signatures."

**Done when:** With a valid bearer token, /feed returns ranked shoes and /swipe shifts
the taste vector.

---

## Phase 3 — Swipe UI (React, talking to the API)
**Goal:** The real swipe feed. Match the look/feel of docs/REFERENCE_UI.jsx.

> Cursor prompt:
> "Per docs/SPEC.md, build the swipe feed in frontend/src. Fetch GET /api/feed,
> render a SwipeCard stack and a TastePanel showing the live taste vector + match%,
> matching the look and swipe feel of docs/REFERENCE_UI.jsx (drag + arrow keys). On
> swipe, POST /api/swipe and update local state from the response. Use a real auth
> token once Phase 4 lands; until then, a dev token in VITE is fine."

**Done when:** You can swipe in the browser and watch the panel re-rank, data coming
from the backend.

---

## Phase 4 — Auth + persistence (Supabase)
**Goal:** Real users; taste/swipes/saves persist in Postgres and survive reload.

> Cursor prompt:
> "Per docs/SPEC.md §7, wire Supabase. Frontend: supabase-js magic-link login, store
> the session, send Authorization: Bearer <access_token> on every API call, gate the
> feed behind login. Backend: SUPABASE_JWT_SECRET is already verified in
> app/auth/supabase_jwt.py — now replace the in-memory app/api/repo.py with real
> Supabase queries (same function signatures), using supabase/schema.sql which I've
> applied. Service role key backend-only. Confirm RLS blocks cross-user reads."

**Done when:** Log in, swipe, refresh, log in elsewhere — taste persists. A second user
can't see your data.

---

## STOP — that's v1.
Swipe + taste + per-user persistence. Ship/show it, then decide what's next.

## Future (explicitly NOT now)
- **Deal/price agent + MCP** — `saved_shoes` already exists; add a `DealAgent` behind a
  `/api/deals` route, with DeepSeek for query-gen/summary. Its own project-sized effort.
- **Real FeedSource** — affiliate/product-feed/sneaker API behind the existing
  ShoeSource protocol. The scrape/social stubs stay stubs unless you've cleared ToS.
- Each future piece is its own branch. Never break Phases 1–4 to add one.

---

## Working rhythm with Cursor
- Branch per phase: `git checkout -b phase-3-swipe-ui`.
- Keep `docs/SPEC.md` open as context; update it when decisions change.
- If Cursor drifts, `git reset` + a tighter prompt beats arguing across ten messages.
- A green "Done when" is a save point. Don't start the next phase on a red one.