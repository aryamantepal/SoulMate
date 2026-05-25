# SoulMate Project TODOs

A structured roadmap for taking the SoulMate local prototype to a production-ready, scaled-out application.

## 🚀 1. Deployment & Infrastructure
- [ ] **Frontend Deployment (Vite/React)**
  - [ ] Deploy frontend to **Vercel** or **Netlify**.
  - [ ] Set environment variables: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, and `VITE_API_BASE`.
  - [ ] Add the deployed redirect URL to Supabase Dashboard > Authentication > URL Configuration.
- [ ] **Backend Deployment (FastAPI)**
  - [ ] Deploy backend to **Render**, **Railway**, **Fly.io**, or **Google Cloud Run**.
  - [ ] Set environment variables: `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
  - [ ] Update `allow_origins` in [main.py](file:///Users/aryamantepal/Desktop/SoulMate/backend/app/main.py) to include the deployed frontend URL.

## ⚡ 2. Technical Scaling & Database Optimizations
- [ ] **Database-level Vector Search (`pgvector`)**
  - [ ] Enable `pgvector` extension in Supabase Postgres.
  - [ ] Add a `vector(7)` column to the shoes table.
  - [ ] Rewrite query logic in [repo.py](file:///Users/aryamantepal/Desktop/SoulMate/backend/app/api/repo.py) using the `<=>` cosine distance operator in SQL instead of doing similarity ranking in-memory in Python.
- [ ] **Swipe Event Optimization (Postgres RPC)**
  - [ ] Consolidate sequential writes in `record_swipe` (profile upsert, taste_vectors upsert, swipes insert) into a single PL/pgSQL database function `rpc.record_swipe`.
  - [ ] Update the backend code to call the database function in a single network round-trip.

## 🎨 3. Product Features & Scaling the Catalog
- [ ] **Real Catalog Integration**
  - [ ] Replace the mock catalog in [seed.py](file:///Users/aryamantepal/Desktop/SoulMate/backend/app/sources/seed.py) with a real product feed or sneaker database.
  - [ ] Implement a class conforming to the `ShoeSource` protocol in [base.py](file:///Users/aryamantepal/Desktop/SoulMate/backend/app/sources/base.py) (e.g. using `thesneakerdatabase.dev` or affiliate APIs).
  - [ ] Add vector embeddings for new catalog items.
- [ ] **Taste Explainability UI**
  - [ ] Diff the active card's vector against the user's taste vector on the server/client.
  - [ ] Render a "Why am I seeing this?" tooltip on the frontend cards highlighting matching dimensions (e.g., retro, warm tones).
- [ ] **Price & Deals Agent**
  - [ ] Create a background worker (Cron or Celery task) to monitor price drops for saved items in `saved_shoes`.
  - [ ] Add a `/api/deals` endpoint to retrieve active coupon codes or discounts.
