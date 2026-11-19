# SoulMate 👟

A premium shoe-discovery and recommendation web application. Swipe right/left on shoes, build a live profile vector as the machine learning engine learns your taste in real-time, and save your favorites.

### Features

- **Swipe-to-learn feed** — a 7-dimension taste vector updates on every swipe; the catalog re-ranks by cosine similarity.
- **Style persona** — your strongest taste dimension is translated into a named archetype (Retro Hunter, Clean Minimalist, Gorpcore Explorer…) shown on your profile and shareable card.
- **Taste stats** — a dashboard of swipe count, like/pass rate, strongest dimensions, and a sparkline of how your dominant dimension grew over time.
- **Collections** — group saved shoes into named folders ("rotation", "grails") and filter by them.
- **Diversity injection** — once your taste is established, the feed sprinkles in off-taste "wildcard" shoes so it never collapses into clones.
- **Brand filter** — chips above the deck to narrow swiping to a single brand.
- **Price-drop monitoring** — live market prices for saved shoes (via KicksDB).
- **Public taste sharing** — an opaque-token read-only profile card at `/taste/:token`, no auth to view.
- **Taste explainability** — "Why this?" badges on the active card; tap to expand a detail modal.
- **Real catalog with images** — sourced live from the KicksDB (kicks.dev) StockX API, refreshed every 6h, with an image proxy to bypass CDN hotlink blocking.
- **No accounts** — each browser gets a random device ID (stored in `localStorage`) sent as `X-Device-Id`; it is the only identity.

---

## 📁 Repository Structure

```
SoulMate/
├── backend/                  # FastAPI Backend Service
│   ├── app/
│   │   ├── api/              # API endpoints (/feed, /swipe, /taste, /stats, /saved, /deals) & repository layer
│   │   ├── auth/             # Device-ID dependency (`X-Device-Id` header)
│   │   ├── sources/          # catalog base protocols, KicksDB source, periodic refresh, and seed
│   │   ├── taste/            # 7-dim taste math, persona, stats, and diversity injection
│   │   └── main.py           # FastAPI entrypoint, CORS, Sentry, periodic catalog refresh
│   └── tests/                # Pytest suite (preference engine + route tests, no cloud config needed)
├── frontend/                 # Vite + React + TypeScript Frontend Client
│   ├── public/
│   │   └── shoes/            # High-resolution generated sneaker product photography
│   ├── src/
│   │   ├── App.tsx           # Swipe feed user interface and interactive states
│   │   ├── App.css           # Styling rules, dark mode supports, and glassmorphic cards
│   │   └── main.tsx          # Client bundle mounter
│   └── index.html
├── docs/                     # Technical specifications, build plans, and checkpoints
│   ├── SPEC.md               # Core spec (ranking formulas, vector dimensions)
│   ├── BUILD_PLAN.md         # Phased implementation outline
│   └── CHECKPOINT.md         # Project status summary
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
| **Backend** | FastAPI (Python 3.11) | High performance API service |
| **ML Taste Model** | Online Linear Preference, Cosine Similarity | Active learning recommendation loop |
| **Storage** | In-memory (per backend process; resets on restart) | Taste, swipes, saves, and collections, keyed by anonymous device ID |
| **Catalog & Pricing** | KicksDB (kicks.dev) StockX API | Live sneaker catalog, images, and market prices |
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
   the in-memory repo and a stubbed device ID, so **no API keys are
   required**:
   ```bash
   pytest
   ```
4. Optionally copy the environment template (`cp .env.example .env`) to set `SNEAKER_DB_API_KEY` etc.
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
   * `CORS_ORIGINS` = `https://your-vercel-domain.vercel.app` *(Comma-separated list of your allowed frontend Vercel origins)*
   * `SNEAKER_DB_API_KEY` = *(KicksDB API key — optional; falls back to the seed catalog if unset)*
   * `SENTRY_DSN` = *(optional; error monitoring is skipped if unset)*

> **Note:** storage is in-memory, so all taste data is lost whenever the backend restarts or spins down.

---

## 🎯 Key Design Choices & Implementation Details

* **Anonymous device identity:** [device.py](./backend/app/auth/device.py) validates the `X-Device-Id` header (8-64 chars of `[A-Za-z0-9-]`) and uses it as the user id. There are no accounts, passwords, or email alerts; clearing browser storage starts a fresh profile.
* **Thin client:** The backend owns all logic — taste updates, ranking, persona/stats derivation, and diversity injection all happen server-side. The frontend renders state and sends swipes.
* **Lazy deck refill:** The feed only refetches when the deck is nearly empty (`< 2` cards), so fast consecutive swipes never replace the active card mid-gesture or trigger a flashing loading screen.
* **In-memory persistence:** [repo.py](./backend/app/api/repo.py) keeps per-device dictionaries (taste, swipe log, saves, collections, share tokens). Nothing survives a backend restart.
* **Cold-start mitigation:** A GitHub Actions cron pings `/api/health` every 10 minutes to keep the free-tier backend warm; the frontend also warm-pings on load and shows a "Waking up the server…" message after 4s.

For the full feature roadmap and next-up items, see [`TODO.md`](./TODO.md) and [`docs/ROADMAP.md`](./docs/ROADMAP.md).