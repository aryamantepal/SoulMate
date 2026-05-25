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
- [ ] **Real Catalog Integration**
  - [ ] Replace the mock catalog in [seed.py](file:///Users/aryamantepal/Desktop/SoulMate/backend/app/sources/seed.py) with a real product feed or sneaker database.
  - [ ] Implement a class conforming to the `ShoeSource` protocol in [base.py](file:///Users/aryamantepal/Desktop/SoulMate/backend/app/sources/base.py) (e.g. using `thesneakerdatabase.dev` or affiliate APIs).
  - [ ] Add vector embeddings for new catalog items.
- [x] **Taste Explainability UI**
  - [x] Diff the active card's vector against the user's taste vector on the client.
  - [x] Render a "Why this?" badge row on the active card highlighting matching dimensions.
- [ ] **Price & Deals Agent**
  - [ ] Create a background worker (Cron or Celery task) to monitor price drops for saved items in `saved_shoes`.
  - [ ] Add a `/api/deals` endpoint to retrieve active coupon codes or discounts.
