# UI — Agentic Negotiation Platform

Single-page React (Vite) app that triggers a negotiation and renders the live
agent chat, status, inventory context, and final invoice. Talks to the FastAPI
backend in `../Backend`.

## Install

```bash
cd UI
npm install
```

## Run against the real backend

1. Start the backend (see `../Backend/README.md`) — it listens on `:8000`.
2. Start the UI:

   ```bash
   npm run dev
   ```

3. Open the printed URL (e.g. http://localhost:5173) and click **Start Negotiation**.

API calls use a **relative base** and are forwarded to the backend by the Vite
dev proxy (`vite.config.js`), so there are no CORS issues. If the backend runs
elsewhere, set `VITE_BACKEND_URL` (proxy target) or `VITE_API_BASE` (direct
fetch base).

## Run without a backend (mock mode)

```bash
VITE_USE_MOCK=true npm run dev
```

`src/mock.js` replays a scripted negotiation whose message and invoice shapes
mirror the real backend, so the UI behaves identically without credentials or a
running server.

## How it maps to the API

- `POST /negotiations/start` → `{ transaction_id }`
- `GET /negotiations/{id}` polled every ~1s → `{ status, turn, messages[], invoice }`
- Agent messages carry a `[OFFER price=.. quantity=.. action=..]` tag; the log
  strips it for display and shows the action (ACCEPT/COUNTER/REJECT) as a chip.
- The invoice block renders when `status === "FULFILLED"` using the backend's
  invoice fields (`agreed_unit_price`, `total_amount`, `payment_status`, …).
