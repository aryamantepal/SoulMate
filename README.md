# SoulMate 👟

A premium shoe-discovery and recommendation web application. Swipe right/left on shoes, build a live profile vector as the machine learning engine learns your taste in real-time, and save your favorites.

### Features

- **Swipe-to-learn feed** — a 7-dimension taste vector updates on every swipe; the catalog re-ranks by cosine similarity.
- **Style persona** — your strongest taste dimension is translated into a named archetype (Retro Hunter, Clean Minimalist, Gorpcore Explorer…) shown on your profile and shareable card.
- **Taste stats** — a dashboard of swipe count, like/pass rate, strongest dimensions, and a sparkline of how your dominant dimension grew over time.
- **Collections** — group saved shoes into named folders ("rotation", "grails") and filter by them.
- **Diversity injection** — once your taste is established, the feed sprinkles in off-taste "wildcard" shoes so it never collapses into clones.
- **Brand filter** — chips above the deck to narrow swiping to a single brand.
- **Price-drop monitoring** — live market prices for saved shoes (via KicksDB) with optional email alerts (Resend).
- **Public taste sharing** — an opaque-token read-only profile card at `/taste/:token`, no auth to view.
- **Taste explainability** — "Why this?" badges on the active card; tap to expand a detail modal.
- **Real catalog with images** — sourced live from the KicksDB (kicks.dev) StockX API, refreshed every 6h, with an image proxy to bypass CDN hotlink blocking.
- **Asymmetric public-key JWT verification** — no shared secret on the backend.

---

## 📁 Repository Structure

```
SoulMate/
├── backend/                  # FastAPI Backend Service
│   ├── app/
│   │   ├── api/              # API endpoints (/feed, /swipe, /taste, /stats, /saved, /deals) & repository layer
│   │   ├── auth/             # JWKS asymmetric public key verification (no secrets required)
│   │   ├── sources/          # catalog base protocols, KicksDB source, periodic refresh, and seed
│   │   ├── taste/            # 7-dim taste math, persona, stats, and diversity injection
│   │   └── main.py           # FastAPI entrypoint, CORS, Sentry, periodic catalog refresh
│   └── tests/                # Pytest suite (preference engine + route tests, no cloud config needed)
├── frontend/                 # Vite + React + TypeScript Frontend Client
│   ├── public/
│   │   └── shoes/            # High-resolution generated sneaker product photography
│   ├── src/
│   │   ├── App.tsx           # Swipe feed user interface, login screen, and interactive states
│   │   ├── App.css           # Styling rules, dark mode supports, and glassmorphic cards
│   │   ├── main.tsx          # Client bundle mounter
│   │   └── supabase.ts       # Supabase-js client initialization
│   └── index.html
├── docs/                     # Technical specifications, build plans, and checkpoints
│   ├── SPEC.md               # Core spec (ranking formulas, vector dimensions)
│   ├── BUILD_PLAN.md         # Phased implementation outline
│   └── CHECKPOINT.md         # Project status summary
├── supabase/
│   ├── schema.sql            # Database tables schema (RLS configuration)
│   └── migrations/           # Incremental SQL migrations (RPC, pgvector, share token, collections)
├── .github/workflows/
│   └── keep-warm.yml         # Cron that pings the backend every 10 min to avoid free-tier cold starts
├── TODO.md                   # Live checklist for scaling and production tasks
└── README.md                 # Project handbook
```

---

## 🛠️ Technology Stack

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | React 19, TypeScript, Vite | Sleek responsive SPA client |
| **Backend** | FastAPI (Python 3.11), PyJWT | High performance API service |
| **ML Taste Model** | Online Linear Preference, Cosine Similarity | Active learning recommendation loop |
| **Database** | Supabase (Postgres) | Profiles, preferences, swipes, saves, and collections persistence |
| **Authentication** | Supabase Auth (Email & Password) | Identity management & JWT session issuer |
| **Catalog & Pricing** | KicksDB (kicks.dev) StockX API | Live sneaker catalog, images, and market prices |
| **Email** | Resend | Transactional price-drop alert emails |
| **Monitoring** | Sentry | Error tracking on frontend and backend (env-gated) |

---

## ⚙️ Local Development

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtualenv and install Python dependencies:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the pytest suite (taste engine math + route tests). These run against
   the in-memory repo and stubbed auth, so **no Supabase or API keys are
   required**:
   ```bash
   pytest
   ```
4. Copy the environment template and configure your secrets:
   ```bash
   cp .env.example .env
   ```
   *Required variables:*
   * `SUPABASE_URL` = *(Your Supabase Project URL)*
   * `SUPABASE_SERVICE_ROLE_KEY` = *(Your Supabase Service Role Key)*
5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node modules:
   ```bash
   npm install
   ```
3. Copy the environment template:
   ```bash
   cp .env.example .env.local
   ```
   *Required variables:*
   * `VITE_API_BASE` = `http://localhost:8000` *(Pointer to local backend)*
   * `VITE_SUPABASE_URL` = *(Your Supabase Project URL)*
   * `VITE_SUPABASE_ANON_KEY` = *(Your Supabase Anonymous Key)*
4. Run the Vite development server:
   ```bash
   npm run dev
   ```

---

## 🚀 Production Deployment

### 1. Frontend (Vercel)
1. Install and run the Vercel CLI from inside `frontend/`:
   ```bash
   npx vercel
   ```
2. Link your account and run the deploy prompts. Vercel will auto-detect Vite.
3. Once deployed, note down your production Vercel URL (e.g. `https://soulmate-lemon.vercel.app`).
4. Set the following environment variables in Vercel Project Settings:
   * `VITE_API_BASE` = `https://your-backend-url.onrender.com` *(Point to backend once live)*
   * `VITE_SUPABASE_URL` = *(Your Supabase URL)*
   * `VITE_SUPABASE_ANON_KEY` = *(Your Supabase Anon Key)*
5. Re-run deployment for production environment variables to build into index bundle:
   ```bash
   npx vercel --prod
   ```

### 2. Backend (Render / Railway)
1. Create a new **Web Service** on Render pointing to your Git repository.
2. Configure settings:
   * **Root Directory:** `backend`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add these Environment Variables:
   * `SUPABASE_URL` = *(Your Supabase URL)*
   * `SUPABASE_SERVICE_ROLE_KEY` = *(Your Supabase service role key)*
   * `CORS_ORIGINS` = `https://your-vercel-domain.vercel.app` *(Comma-separated list of your allowed frontend Vercel origins)*
   * `SNEAKER_DB_API_KEY` = *(KicksDB API key — optional; falls back to the seed catalog if unset)*
   * `RESEND_API_KEY` = *(Resend API key — optional; price-drop emails no-op if unset)*
   * `SENTRY_DSN` = *(optional; error monitoring is skipped if unset)*

> **Migrations:** apply the SQL files in `supabase/migrations/` (in order) via the Supabase SQL editor. The latest, `004_collections.sql`, adds the `collection` column used by Collections.

### 3. Supabase Auth Configuration
To allow users to redirect back to your live frontend after authenticating:
1. Open the **Supabase Dashboard** > **Authentication** > **URL Configuration**.
2. Under **Redirect URLs**, add your Vercel domain: `https://your-vercel-domain.vercel.app`.

---

## 🎯 Key Design Choices & Implementation Details

* **Asymmetric Key JWT Verification:** In [supabase_auth.py](file:///Users/aryamantepal/Desktop/SoulMate/backend/app/auth/supabase_auth.py), the FastAPI server verifies user tokens via Supabase's public JWKS endpoint. The backend never decodes tokens using a shared secret and operates without network round-trips per request by caching the public keys.
* **Thin client:** The backend owns all logic — taste updates, ranking, persona/stats derivation, and diversity injection all happen server-side. The frontend renders state and sends swipes.
* **Lazy deck refill:** The feed only refetches when the deck is nearly empty (`< 2` cards), so fast consecutive swipes never replace the active card mid-gesture or trigger a flashing loading screen.
* **Fallback persistence:** If Supabase keys are not set, [repo.py](./backend/app/api/repo.py) switches automatically to an in-memory dictionary, and the `supabase` package is imported lazily — so tests and offline development run with zero cloud config.
* **Graceful migration handling:** Reads that depend on newer columns (e.g. `collection`) degrade gracefully if the migration hasn't been applied yet, rather than 500-ing the endpoint.
* **Cold-start mitigation:** A GitHub Actions cron pings `/api/health` every 10 minutes to keep the free-tier backend warm; the frontend also warm-pings on load and shows a "Waking up the server…" message after 4s.

For the full feature roadmap and next-up items, see [`TODO.md`](./TODO.md) and [`docs/ROADMAP.md`](./docs/ROADMAP.md).