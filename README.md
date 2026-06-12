# Agentic Negotiation & Procurement Platform

Hackathon POC — two LLM agents (Vendor and Buyer) negotiate a purchase deal inside a LangGraph state graph. A React UI streams the conversation live and displays the final invoice when a deal is reached.

## Architecture

```
Browser (React/Vite)
    |
    | HTTP polling every ~1s
    v
FastAPI Backend (LangGraph)
    |
    |-- buyer_agent  (LLM or mock strategy)
    |-- vendor_agent (LLM or mock strategy)
    |-- guardrail_validator
    |-- payment / invoice nodes
```

## Repo layout

```
Backend/   FastAPI + LangGraph negotiation engine
UI/        Vite + React live log viewer
eval/      Pioneer MLOps evaluation pipeline
```

## Quick start

### Option A — one-command startup

```bash
./startup.sh
```

Starts the FastAPI backend on `:8000` and the Vite UI dev server on `:5173`. Open the printed URL and click **Start Negotiation**. Stop both with `Ctrl+C`.

### Option B — manual

#### 1. Start the backend

```bash
cd Backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# Listening on http://localhost:8000
```

#### 2. Start the UI

```bash
cd UI
npm install
npm run dev
# Open http://localhost:5173
```

The Vite dev server proxies `/negotiations/*` to `:8000`, so no CORS configuration is needed in development.

#### 3. Run the UI without a backend (mock mode)

```bash
cd UI
VITE_USE_MOCK=true npm run dev
```

Replays a scripted negotiation whose shapes mirror the real backend exactly.

---

## Known production issues

See `UI/README.md` for full details on both issues.

### 1. Frontend cannot reach the backend in production

The Vite dev proxy only exists during local development. In a deployed build (e.g. Render static site), `VITE_API_BASE` must be set to the backend's public URL so the browser knows where to send API requests.

### 2. CORS headers required for cross-origin deployments

When the frontend and backend are deployed on different domains, the browser enforces CORS. The backend now includes `CORSMiddleware` (`allow_origins=["*"]`), which resolves this. If you see empty responses or `Unexpected end of JSON input` in production, CORS or a missing `VITE_API_BASE` is the cause — see `UI/README.md`.

---

## LLM configuration (Pioneer.ai)

Set `PIONEER_API_KEY` (or `PROMISE_API_KEY`) to enable live LLM negotiation. Without it the backend falls back to a deterministic mock strategy. See `Backend/README.md` for all env vars and `PIONEER_SETUP.md` for Pioneer.ai integration notes including the model currently used by the agents.
