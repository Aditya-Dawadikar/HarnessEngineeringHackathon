# UI — Agentic Negotiation Platform

Single-page React (Vite) app that triggers a negotiation and renders the live
agent chat, status, inventory context, and final invoice. Talks to the FastAPI
backend in `../Backend`.

> To run this alongside the backend with one command, use `../startup.sh`
> from the repo root.

## Install

```bash
cd UI
npm install
```

## Run against the real backend (development)

1. Start the backend (see `../Backend/README.md`) — it listens on `:8000`.
2. Start the UI:

   ```bash
   npm run dev
   ```

3. Open the printed URL (e.g. http://localhost:5173) and click **Start Negotiation**.

API calls use a **relative base** (`VITE_API_BASE` defaults to `''`) and are
forwarded to the backend by the Vite dev proxy (`vite.config.js`). No CORS
configuration is needed in development.

## Run without a backend (mock mode)

```bash
VITE_USE_MOCK=true npm run dev
```

`src/mock.js` replays a scripted negotiation whose message and invoice shapes
mirror the real backend, so the UI behaves identically without credentials or a
running server.

---

## Production deployment

Two things **must** be configured when deploying the frontend to a static host
(Render, Vercel, Netlify, etc.). Without them, the UI silently fails with
`Unexpected end of JSON input` when clicking Start Negotiation.

### Issue 1 — Set `VITE_API_BASE` to the backend URL

**Root cause:** The Vite dev proxy only exists during local development. A
production build is plain static HTML/CSS/JS — there is no Node process to
forward requests. When `VITE_API_BASE` is empty, API calls go to
`<frontend-origin>/negotiations/start`, which is the static file server and
returns garbage (HTML or an empty body), not JSON.

**Fix:** In your hosting provider's environment settings, add:

```
VITE_API_BASE = https://<your-backend-url>
```

For example on Render: open the frontend service → **Environment** →
**Add environment variable** → key `VITE_API_BASE`, value `https://your-backend.onrender.com`.
Then trigger a redeploy so the value is baked into the build.

### Issue 2 — Backend must have CORS headers

**Root cause:** When the frontend and backend are on different domains, the
browser performs a CORS preflight (`OPTIONS`) before every API request. If the
backend does not return `Access-Control-Allow-Origin` headers the browser
blocks the response, the body arrives empty, and parsing it as JSON throws
`Unexpected end of JSON input`.

**Fix (already applied):** `Backend/app/main.py` includes FastAPI's
`CORSMiddleware` with `allow_origins=["*"]`. No additional configuration is
needed — redeploy the backend after pulling the latest `master`.

---

## How it maps to the API

- `POST /negotiations/start` → `{ transaction_id }`
- `GET /negotiations/{id}` polled every ~1s → `{ status, turn, messages[], invoice }`
- Agent messages carry a `[OFFER price=.. quantity=.. action=..]` tag; the log
  strips it for display and shows the action (ACCEPT/COUNTER/REJECT) as a chip.
- The invoice block renders when `status === "FULFILLED"` using the backend's
  invoice fields (`agreed_unit_price`, `total_amount`, `payment_status`, …).

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE` | `''` (same origin) | Backend base URL for production deploys |
| `VITE_BACKEND_URL` | `http://localhost:8000` | Vite dev proxy target (dev only) |
| `VITE_USE_MOCK` | `false` | Set to `true` to run without a backend |
