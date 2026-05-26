# SoulMate — Polish Pass Handoff

Brief for an agent picking up the next round of work. The app is feature-complete
for v1; this round is about polish, not features. Read this top to bottom before
starting — it has the context you need to make judgment calls.

## What the app is

SoulMate is a sneaker discovery app with a Tinder-style swipe interface. FastAPI
backend (thin-client pattern — backend owns all logic), React 19 + Vite + TypeScript
frontend. Users swipe shoes, a 7-dimension taste vector learns their preference,
the feed re-ranks by cosine similarity. Deployed: frontend on Vercel
(`soulmate-lemon.vercel.app`), backend on Render (`soulmate-9grg.onrender.com`).

## Key files

- `frontend/src/App.tsx` — the entire frontend. All state, the swipe deck,
  panels (Saved / History / Price drops), onboarding quiz, shoe detail modal,
  `ShoeImage` and `ShoeSummary` components.
- `frontend/src/App.css` — all styles. Has mobile media queries at `400px`,
  `720px`, and `900px`. Dark theme: bg `#0a0a0a`, purple accent `#a855f7`.
- `backend/app/api/routes.py` — all endpoints.
- Backend is in good shape; this pass is almost entirely frontend.

## Priorities (in order)

### ~~1. Mobile UX pass~~ ✅ DONE

Completed in commits `d029db2`, `a4cb0e0`, `846fc73`. Here's what was shipped:

- **Touch swiping with visual drag feedback**: Cards now move with the finger
  during swipe via dual `onTouch*` + `onPointer*` handlers. "WANT" / "PASS"
  labels fade in once drag exceeds 40px. 80px threshold fires the swipe.
  `touch-action: none` on `.shoe-card--active` prevents the browser from
  hijacking the gesture. Drag state tracked via `useRef` + `dragOffset` state.
- **Bottom-sheet modal improvements**: Drag handle bar at top of modal (visible
  ≤720px via `.modal-drag-handle`). Swipe down >100px dismisses; card slides
  with the finger during gesture. iOS safe-area padding via
  `env(safe-area-inset-bottom)`. `-webkit-overflow-scrolling: touch` for smooth
  scroll.
- **Panel reflow**: Saved grid goes single-column at ≤400px. Session action bar
  now scrolls horizontally instead of wrapping on narrow screens (no-scrollbar,
  `flex-shrink: 0` on buttons).
- **Collapsible taste panel on mobile**: At ≤900px, a toggle button
  ("Taste model — N swipes ▼") appears above the panel. Panel hidden by default
  via `.taste-panel--collapsed`. Desktop layout unchanged (toggle `display: none`
  above 900px).
- **Thumb-friendly tap targets**: Pass/Want buttons bumped to `min-height: 52px`
  + `font-size: 17px` at ≤720px. Onboarding buttons get same treatment. Card
  meta hint updated to "Swipe or tap · ← → keys · ⌘Z undo".

All changes scoped to `App.tsx` and `App.css`. `npx tsc --noEmit` passes clean.

### 2. Empty & error states
Audit every state a real user hits:
- Brand-new user before the onboarding quiz fires — what shows?
- Saved panel with zero saved shoes — is there a friendly empty state or just
  a blank grid?
- History panel "Passed" tab when there are no passes — empty message?
- Backend cold-start: there's already a "Waking up the server…" message after
  4s (search `slowLoad` in App.tsx). Confirm it looks intentional, not broken.
- Feed exhausted ("You've seen everything" + Shuffle again) — verify it still
  works after the recent token fixes.

### 3. Share taste profile — only growth feature left
A shareable read-only taste card, e.g. `/taste/:id` rendering "82% retro ·
71% earthy · 68% warm" with no auth required to view. This is the one feature
that helps the app *spread* rather than just retain. Backend needs a public
read-only endpoint that returns a taste vector by a shareable id (do NOT expose
user_id directly — generate an opaque token). Frontend needs a small standalone
route/page. Confirm approach with the user before building — it touches auth
boundaries.

## Constraints / gotchas

- Backend free tier (Render) cold-starts ~30-50s. The frontend pings
  `/api/health` on load to pre-warm. Don't be surprised by slow first requests.
- The `request()` helper in App.tsx pulls a fresh Supabase token via
  `getSession()` on every call — don't revert that, it fixes 401s from stale
  tokens.
- Image URLs: local seed paths (`/shoes/*.png`) are served directly; external
  URLs go through the backend `/api/img` proxy. See `proxyImg()` in App.tsx.
- **Drag system**: Touch swipe uses `useRef` for `dragStartX` / `isDragging`
  (zero re-renders during drag) and `useState` for `dragOffset` (drives the
  visual transform). Don't switch to controlled-only — the ref pattern is
  intentional for 60fps drag perf.
- **Taste panel toggle**: `tastePanelOpen` state drives visibility via CSS class.
  The toggle button is always rendered but `display: none` above 900px.
- Commit style: imperative subject, short body explaining *why*, with the
  `Co-Authored-By` trailer. Push to `main` (no PR flow set up).
- Test UI changes in a real browser before claiming done — type-checking
  proves correctness, not that the feature actually works.

## What NOT to do

- Don't add more seed shoes — the KicksDB catalog is sufficient and refreshes
  every 6h automatically.
- Don't wire pgvector ranking yet — not worth it under ~1000 shoes.
- Don't build the post-traction ideas (friend comparisons, AI blurbs, outfit
  pairings) — needs real users first.

Start with #2. The mobile pass is shipped.
