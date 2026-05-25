# SoulMate Project TODOs

A structured roadmap for taking the SoulMate local prototype to a production-ready, scaled-out application.

## 🚀 1. Deployment & Infrastructure
- [x] **Frontend Deployment (Vite/React)**
  - [x] Deploy frontend to **Vercel** or **Netlify**.
  - [x] Set environment variables: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, and `VITE_API_BASE`.
  - [x] Add the deployed redirect URL to Supabase Dashboard > Authentication > URL Configuration.
- [x] **Backend Deployment (FastAPI)**
  - [x] Deploy backend to **Render**, **Railway**, **Fly.io**, or **Google Cloud Run**.
  - [x] Set environment variables: `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
  - [x] Update `allow_origins` in [main.py](file:///Users/aryamantepal/Desktop/SoulMate/backend/app/main.py) to include the deployed frontend URL.

## ⚡ 2. Technical Scaling & Database Optimizations
- [x] **Database-level Vector Search (`pgvector`)**
  - [x] Enable `pgvector` extension in Supabase Postgres.
  - [x] Add a `vector(7)` column to the shoes table (`supabase/migrations/002_pgvector.sql`).
  - [ ] Rewrite query logic in [repo.py](file:///Users/aryamantepal/Desktop/SoulMate/backend/app/api/repo.py) using the `<=>` cosine distance operator in SQL instead of doing similarity ranking in-memory in Python. (Migration ready; backend wiring pending real catalog.)
- [x] **Swipe Event Optimization (Postgres RPC)**
  - [x] Consolidate sequential writes in `record_swipe` into `public.record_swipe` PL/pgSQL function (`supabase/migrations/001_record_swipe_rpc.sql`).
  - [x] Update the backend code to call the database function in a single network round-trip.

## 🎨 3. Product Features & Scaling the Catalog
- [x] **Real Catalog Integration**
  - [x] Implemented `SneakerDatabaseSource` in `sources/sneaker_db.py` backed by `thesneakerdatabase.dev` with seed fallback.
  - [x] Heuristic `vec_from_metadata()` auto-generates taste vectors from name/brand/colorway.
  - [x] Catalog warms on startup via FastAPI lifespan; cached in-process.
- [x] **Taste Explainability UI**
  - [x] Diff the active card's vector against the user's taste vector on the client.
  - [x] Render a "Why this?" badge row on the active card highlighting matching dimensions.
- [x] **Price & Deals Agent**
  - [x] `GET /api/deals` endpoint added — queries thesneakerdatabase.dev market prices for each saved shoe.
  - [x] Results cached 30 min per user; price drops flagged when market ask < retail price.
  - [x] Frontend "Price drops" toggle panel in the session bar.
