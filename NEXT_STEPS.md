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
- `frontend/src/App.css` — all styles. Has mobile media queries at `720px` and
  `900px`. Dark theme: bg `#0a0a0a`, purple accent `#a855f7`.
- `backend/app/api/routes.py` — all endpoints.
- Backend is in good shape; this pass is almost entirely frontend.

## Priorities (in order)

### 1. Mobile UX pass — HIGHEST VALUE
This is a swipe app; most usage is mobile. Load it on a real phone (or device
emulation in Chrome DevTools) and check:
- Do cards swipe smoothly with **touch**, not just mouse drag? Verify the drag
  handlers in `App.tsx` work with touch events, not only pointer/mouse.
- The shoe detail modal becomes a bottom-sheet under 720px (see `.modal-card`
  mobile rules in App.css). Is it actually usable — scrollable, dismissable,
  not cut off by the iOS safe area?
- Are the Saved / History / Price-drop panels usable one-handed? Do the grids
  reflow to a single column on narrow screens?
- The taste model panel sits beside the card on desktop. Where does it go on
  mobile — does it stack sensibly or get buried?
- Tap targets: are Pass/Want buttons big enough for thumbs?

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

Start with #1. It's where the users actually are.
