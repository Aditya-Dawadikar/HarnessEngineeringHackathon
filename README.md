# Agentic Negotiation & Procurement Platform

> Autonomous AI agents that negotiate deals and settle payments — no humans required.

Two LLM-powered agents (Vendor and Buyer) negotiate a purchase deal inside a LangGraph state machine, driven by a fine-tuned **Qwen3-8B** model on **Pioneer.ai**. When both sides agree, a Stripe-shaped payment flow fires automatically. A React UI streams the conversation live and renders the final invoice.

---

## Architecture

```
Browser (React + Vite)
        │
        │  POST /negotiations/start
        │  GET  /negotiations/{id}   (polls every ~1s)
        │  GET  /config
        ▼
FastAPI Backend  (:8000)
        │
        ▼
LangGraph StateGraph
        │
        ├── buyer_agent          Pioneer.ai LLM (Qwen3-8B fine-tuned)
        ├── vendor_agent         Pioneer.ai LLM (Qwen3-8B fine-tuned)
        ├── guardrail_validator  Enforces price floors/ceilings + turn limit
        ├── payment_request      Vendor creates Stripe PaymentIntent
        ├── payment_authorization Buyer confirms PaymentIntent
        └── generate_invoice     Assembles final invoice
                │
                ├── ClickHouse   Telemetry (agent_message_logs, agent_tool_executions)
                └── In-memory    Active negotiation state store
```

### Negotiation flow

Each agent turn produces a message ending with a structured tag:

```
[OFFER price=X.XX quantity=N action=ACCEPT|COUNTER|REJECT]
```

The guardrail validator checks every offer. A deal closes when both sides emit `action=ACCEPT` at a price within the overlap zone. If either agent violates its hard constraint or the turn limit (10) is reached, the negotiation terminates.

---

## Repo layout

```
Backend/          FastAPI + LangGraph negotiation engine
  app/
    main.py       API endpoints (POST /negotiations/start, GET /negotiations/{id}, GET /config)
    graph.py      LangGraph state machine + all agent/payment nodes
    llm_client.py Pioneer.ai OpenAI-compatible client (falls back to mock if unconfigured)
    payments.py   Mock Stripe PaymentIntent lifecycle
    telemetry.py  ClickHouse client (lazy-init, non-blocking)
    config.py     Vendor/Buyer domain config (prices, quantities, display fields)
  tests/          pytest suite (50 tests)

UI/               Vite + React frontend
  src/
    api.js        startNegotiation / fetchNegotiation / fetchConfig
    useNegotiation.js  Polling hook
    useConfig.js  Config fetch hook
    InventoryContext.jsx  Vendor/Buyer cards + deal-zone price bar
    MessageLog.jsx        Live negotiation transcript
    InvoiceBlock.jsx      Final invoice display
    mock.js       Local mock (VITE_USE_MOCK=true)

eval/             Pioneer MLOps pipeline
  pioneer_mlops.py  Generates synthetic training data + fine-tunes Qwen3-8B via Pioneer API

render.yaml       Render deployment config
startup.sh        One-command local dev launcher
```

---

## Quick start

### Prerequisites

- Python 3.12+
- Node.js 18+
- A Pioneer.ai API key (without it the backend falls back to a deterministic mock — still fully functional)

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in PIONEER_API_KEY (and optionally ClickHouse credentials)
```

```bash
cp UI/.env.example UI/.env
# Edit UI/.env if you need to point at a deployed backend (VITE_API_BASE)
```

### 2a. One-command startup (recommended)

```bash
./startup.sh
```

Starts the FastAPI backend on `:8000` and the Vite UI on `:5173`. Open `http://localhost:5173` and click **Start Negotiation**. Stop both with `Ctrl+C`.

### 2b. Manual startup

**Backend:**

```bash
cd Backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**UI:**

```bash
cd UI
npm install
npm run dev
# Open http://localhost:5173
```

The Vite dev server proxies `/negotiations/*` and `/config` to `:8000` — no CORS setup needed locally.

### Mock mode (no backend required)

```bash
cd UI
VITE_USE_MOCK=true npm run dev
```

Replays a scripted negotiation with shapes that mirror the real backend exactly.

---

## Environment variables

### Backend (`.env`)

| Variable | Required | Description |
|---|---|---|
| `PIONEER_API_KEY` | Yes (for live LLM) | Pioneer.ai API key. Without it, agents use a deterministic mock strategy. |
| `PIONEER_MODEL` | No | Model ID or training job ID. Defaults to `gpt-4.1-mini`. Currently set to the fine-tuned `negotiation-agent-evals` Qwen3-8B adapter. |
| `CLICKHOUSE_HOST` | No | ClickHouse host. Leave blank to disable telemetry (negotiation still works). |
| `CLICKHOUSE_PORT` | No | Defaults to `8443`. |
| `CLICKHOUSE_DATABASE` | No | Defaults to `default`. |
| `CLICKHOUSE_USER` | No | ClickHouse username. |
| `CLICKHOUSE_PASSWORD` | No | ClickHouse password. |
| `CLICKHOUSE_SECURE` | No | Defaults to `true`. |

### UI (`UI/.env`)

| Variable | Required | Description |
|---|---|---|
| `VITE_API_BASE` | Production only | Backend URL, e.g. `https://negotiate-backend.onrender.com`. Leave blank in local dev (Vite proxy handles it). |
| `VITE_USE_MOCK` | No | Set to `true` to run the UI against the local mock without a backend. |

---

## API reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check → `{"status": "ok"}` |
| `GET` | `/config` | Vendor + buyer domain config (prices, product, quantities) |
| `POST` | `/negotiations/start` | Start a new negotiation → `{"transaction_id": "<uuid>"}` |
| `GET` | `/negotiations/{id}` | Poll negotiation state (status, messages, invoice) |

**Negotiation status values:** `NEGOTIATING` → `AGREEMENT` → `PAYMENT_PENDING` → `FULFILLED` (or `TERMINATED`)

---

## Running tests

```bash
cd Backend
source .venv/bin/activate
pytest
# 50 tests, all passing
```

---

## Deployment (Render)

The repo includes `render.yaml` for the backend. Key setting: uvicorn must bind to `0.0.0.0` (not `127.0.0.1`) so Render's port scanner can detect it.

```
startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set all backend env vars in Render's **Environment** dashboard. The `.env` file is gitignored and not deployed.

---

## Fine-tuned model

`eval/pioneer_mlops.py` generates a synthetic negotiation dataset and fine-tunes `Qwen/Qwen3-8B` (LoRA) via Pioneer's training API. The deployed adapter (`negotiation-agent-evals-20260612211958`) is what both agents currently use in production — ~120 tokens per turn, faster and more reliable than a general-purpose model for this task. See `PIONEER_SETUP.md` for full integration notes.
