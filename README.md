# SoulMate 👟

A premium shoe-discovery and recommendation web application. Swipe right/left on shoes, build a live profile vector as the machine learning engine learns your taste in real-time, and save your favorites. 

Features email/password authentication, a real sneaker catalog sourced live from thesneakerdatabase.dev, taste explainability ("Why this?" badges), price-drop monitoring for saved shoes, and asymmetric public-key JWT verification.

---

## 📁 Repository Structure

```
SoulMate/
├── backend/                  # FastAPI Backend Service
│   ├── app/
│   │   ├── api/              # API endpoints (/feed, /swipe, /taste, /saved, /deals) & repository layer
│   │   ├── auth/             # JWKS asymmetric public key verification (no secrets required)
│   │   ├── sources/          # catalog base protocols, SneakerDatabaseSource, and seed
│   │   ├── taste/            # 7-dimensional taste preference math & update algorithms
│   │   └── main.py           # FastAPI entrypoint, CORS configuration
│   └── tests/                # Pytest suite verifying the preference engine
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
│   └── schema.sql            # Database tables schema (RLS configuration)
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
| **Database** | Supabase (Postgres) | Profiles, preferences, swipes, and saves persistence |
| **Authentication** | Supabase Auth (Email & Password) | Identity management & JWT session issuer |

---

## ⚙️ Local Development

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the pytest suite to verify taste engine math:
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

### 3. Supabase Auth Configuration
To allow users to redirect back to your live frontend after authenticating:
1. Open the **Supabase Dashboard** > **Authentication** > **URL Configuration**.
2. Under **Redirect URLs**, add your Vercel domain: `https://your-vercel-domain.vercel.app`.

---

## 🎯 Key Design Choices & Implementation Details

* **Asymmetric Key JWT Verification:** In [supabase_auth.py](file:///Users/aryamantepal/Desktop/SoulMate/backend/app/auth/supabase_auth.py), the FastAPI server verifies user tokens via Supabase's public JWKS endpoint. The backend never decodes tokens using a shared secret and operates without network round-trips per request by caching the public keys.
* **Stop Event Propagation:** Action buttons inside the swipe card in [App.tsx](file:///Users/aryamantepal/Desktop/SoulMate/frontend/src/App.tsx) explicitly block `onPointerDown` and `onPointerUp` propagation to prevent button clicks from initiating card-swipe calculations and causing double-swiping glitches.
* **Silent Feed Reloads:** When a swipe is committed, the feed is refreshed in the background, smoothly updating user taste profiles and catalog rankings without throwing the deck back into a flashing loading screen.
* **Fallback Persistence:** If Supabase keys are not set, [repo.py](file:///Users/aryamantepal/Desktop/SoulMate/backend/app/api/repo.py) switches automatically to an in-memory dictionary. This allows tests and offline development to run smoothly out of the box.

For the full feature roadmap and next-up items, see [`TODO.md`](./TODO.md) and [`docs/ROADMAP.md`](./docs/ROADMAP.md).