# Tickets: Agentic Negotiation & Procurement Platform (Hackathon POC)

Companion to `INSTRUCTIONS.md`. Tickets are sized so Backend and UI agents can work in parallel. Tickets marked **[PLACEHOLDER]** depend on external integration details (Promise Platform, Stripe, ClickHouse) — **ask the user for those details when the ticket is picked up.** Do not guess or invent connection info.

---

## Status Overview

| Ticket | Summary | Status |
|---|---|---|
| BE-1 | Project scaffolding & domain config | ✅ Done |
| BE-2 | LangGraph negotiation graph | ✅ Done |
| BE-3 | Promise Platform LLM client (Pioneer.ai) | ✅ Done |
| BE-4 | Stripe payment integration stub | ✅ Done |
| BE-5 | ClickHouse telemetry stub | ✅ Done |
| BE-6 | Negotiation API endpoints | ✅ Done |
| BE-7 | Finalize ClickHouse telemetry integration | ⏳ Blocked — needs `CLICKHOUSE_HOST`/`PORT`/`DATABASE` from user |
| BE-8 | Mock Stripe payment tool (PaymentIntent lifecycle) | ✅ Done |
| BE-9 | Expose vendor/buyer config via `GET /config` | 🚧 In progress |
| UI-1 | Project scaffolding | ✅ Done |
| UI-2 | Negotiation log viewer | ✅ Done |
| UI-3 | Status badge & invoice block | ✅ Done |
| UI-4 | Negotiation context panels (inventory cards + price bar) | ✅ Done (static data — see UI-7) |
| UI-5 | Integrate UI with real FastAPI backend | ✅ Done |
| UI-6 | Polish (typing indicator, TERMINATED banner, fade-in, empty state) | ✅ Done |
| UI-7 | Wire negotiation context panel to live `GET /config` | 🚧 In progress |

---

## Shared API Contract (read this first)

```
POST /negotiations/start
  -> 200 { "transaction_id": "<uuid>" }

GET /negotiations/{transaction_id}
  -> 200 {
       "transaction_id": "<uuid>",
       "status": "NEGOTIATING" | "AGREEMENT" | "PAYMENT_PENDING" | "FULFILLED" | "TERMINATED",
       "turn": <int>,
       "messages": [
         {
           "sender": "VendorAgent" | "BuyerAgent" | "System",
           "text": "<string>",
           "extracted_price": <number|null>,
           "extracted_quantity": <number|null>,
           "timestamp": "<ISO8601>"
         }
       ],
       "invoice": { ... } | null
     }

GET /config
  -> 200 {
       "vendor": {
         "agent_id": "<string>", "company": "<string>",
         "product": { "id": "<string>", "name": "<string>", "description": "<string>", "unit": "<string>" },
         "stock_quantity": <int>, "floor_price": <number>, "ceiling_price": <number>
       },
       "buyer": {
         "agent_id": "<string>", "company": "<string>",
         "product": { "id": "<string>", "name": "<string>", "unit": "<string>" },
         "desired_quantity": <int>, "floor_price": <number>, "ceiling_price": <number>
       }
     }
```

This contract lets UI tickets be built against a mock before the Backend endpoints exist.

---

## Backend Tickets (`Backend/`)

### BE-1 — Project Scaffolding & Domain Config
- FastAPI app skeleton + `requirements.txt` (`fastapi`, `uvicorn`, `langgraph`, `langchain-core`).
- `app/config.py`: hardcoded Vendor/Buyer domain config per `INSTRUCTIONS.md` §2.
- `app/main.py`: app instance + health check route.
- **Depends on**: nothing. Do this first.

### BE-2 — LangGraph Negotiation Graph
- `app/graph.py`: `NegotiationState` TypedDict, nodes `buyer_agent`, `vendor_agent`, `guardrail_validator`, routing/edges, turn limit (`INSTRUCTIONS.md` §4).
- Use a **mock LLM function** (returns canned offers/counters) for `buyer_agent` / `vendor_agent` initially so the graph can be built and tested without BE-3.
- **Depends on**: BE-1.

### BE-3 — Promise Platform LLM Client `[PLACEHOLDER]`
- `app/llm_client.py`: `generate(system_prompt, messages) -> str` (`INSTRUCTIONS.md` §6).
- **STOP**: Ask the user for the Promise Platform base URL, auth mechanism, request/response format, and model name(s) before writing the real client. Until then, leave a stub that raises `NotImplementedError`.
- Once ready, swap into BE-2's agent nodes in place of the mock.
- **Depends on**: BE-1 (independent of BE-2 until integration).

### BE-4 — Stripe Payment Integration `[PLACEHOLDER]`
- `app/payments.py`: `create_payment_request(...)`, `authorize_payment(...)` (`INSTRUCTIONS.md` §5).
- Add `payment_request`, `payment_authorization`, `generate_invoice` nodes to the graph.
- **STOP**: Ask the user for Stripe API keys/mode and preferred flow (PaymentIntents vs. Checkout) before implementing. Stub with a mock "always succeeds" implementation until then.
- **Depends on**: BE-1, BE-2 (for node wiring).

### BE-5 — ClickHouse Telemetry `[PLACEHOLDER]`
- `app/telemetry.py`: `log_message(...)`, `log_tool_execution(...)`, table DDL (`INSTRUCTIONS.md` §7).
- **STOP**: Ask the user for ClickHouse host/port/database/credentials before implementing the real client. Stub with console-logging no-ops until then.
- Wire calls into all BE-2 / BE-4 nodes.
- **Depends on**: BE-1 (independent until integration).

### BE-6 — API Endpoints
- `POST /negotiations/start` and `GET /negotiations/{transaction_id}` per the Shared API Contract above. In-memory `dict` state store.
- **Depends on**: BE-2.

### BE-7 — Finalize ClickHouse Telemetry Integration
- Replace `app/telemetry.py`'s console-logging `_insert` with a real ClickHouse client (e.g. `clickhouse-connect`) writing to the `agent_message_logs` / `agent_tool_executions` tables (DDL already defined in `app/telemetry.py` / `INSTRUCTIONS.md` §7). Create the tables on startup if they don't exist.
- Config via env vars: `CLICKHOUSE_HOST`, `CLICKHOUSE_PORT`, `CLICKHOUSE_DATABASE`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_SECURE`.
  - `CLICKHOUSE_USER` / `CLICKHOUSE_PASSWORD` are already in `.env` (from `clickhouse_credentials.txt`, gitignored).
  - **STOP**: `CLICKHOUSE_HOST` / `CLICKHOUSE_PORT` / `CLICKHOUSE_DATABASE` are still unknown — ask the user before writing the real client.
- Preserve `_safe_insert` semantics: if a ClickHouse insert fails, log the error to console and continue — telemetry must never block the negotiation. Keep `log_message` / `log_tool_execution` signatures unchanged so BE-2/BE-4 call sites don't need to change.
- **Depends on**: BE-1 (independent of BE-2/BE-4, which already call `telemetry.log_message` / `log_tool_execution`).

### BE-8 — Mock Stripe Payment Tool (Payment Request & Payment Initiation)
- BE-4's `app/payments.py` stub returns a fresh, unrelated `payment_intent_id` from `authorize_payment` instead of confirming the one created by `create_payment_request` — fix this by giving the mock tool an in-memory `PaymentIntent` store keyed by `payment_intent_id`.
- `create_payment_request` (Vendor's payment-request tool): create and store a Stripe-shaped `PaymentIntent` (`id`, `object`, `amount` in cents, `currency`, `status="requires_confirmation"`, `created`); return it.
- `authorize_payment` (Buyer's payment-initiation/confirmation tool): look up the stored `PaymentIntent` by `payment_intent_id`, validate `authorized_amount` matches `amount`, then transition `status` to `"succeeded"`.
- Raise a `PaymentValidationError` for an unknown `payment_intent_id` or an amount mismatch. Update `graph.py`'s `_run_payment_tool` to catch this separately and log `execution_status="ValidationError"` (the enum value already defined in `telemetry.py` / `INSTRUCTIONS.md` §7.2 but never used).
- Update `graph.py`'s `payment_authorization` node to pass the `payment_intent_id` from the invoice (set by `payment_request`) through to `authorize_payment`, so the two calls reference the same mock `PaymentIntent`.
- This stays a pure mock — no real Stripe keys needed. Swapping in the real Stripe SDK is a separate future ticket (mirrors BE-7 for ClickHouse).
- **Depends on**: BE-4.

### BE-9 — Expose Vendor/Buyer Config via `GET /config`
- Extend `app/config.py`'s `VENDOR_CONFIG` / `BUYER_CONFIG` with the display fields the UI's negotiation context panel needs: `agent_id`, `company`, `product_name`, `product_unit`, and (vendor only) `product_description`. Existing keys (`Product_ID`, `Floor_Price`, etc.) are unchanged, so `graph.py` keeps working as-is.
- Add `GET /config` to `app/main.py` returning `{ "vendor": {...}, "buyer": {...} }` shaped per the Shared API Contract above, built from the extended config dicts.
- Add a test in `tests/test_main.py` asserting the response shape.
- Closes the gap left by UI-4 — see UI-7.
- **Depends on**: BE-1.
---

## UI Tickets (`UI/`)

### UI-1 — Project Scaffolding
- Vite + React app in `UI/`. Single page shell, minimal global CSS, no component library.
- **Depends on**: nothing.

### UI-2 — Negotiation Log Viewer
- "Start Negotiation" button → `POST /negotiations/start`. Poll `GET /negotiations/{transaction_id}` every ~1s.
- Render a scrolling message list (sender, text, price, quantity).
- Can be built against a local mock of the Shared API Contract before BE-6 is ready.
- **Depends on**: UI-1.

### UI-3 — Status & Invoice Display
- Status badge for `status`; invoice block rendered when `status === "FULFILLED"`.
- **Depends on**: UI-2.

### UI-4 — Negotiation Context Panels
- Vendor/Buyer inventory cards (company, product, stock/quantity, price range) plus a price-range bar showing the overlap ("deal zone") between the vendor's ask and the buyer's budget.
- Implemented in `InventoryContext.jsx`, rendered above the negotiation log.
- **Status**: ✅ Done — currently reads from a hardcoded `inventoryData.js`; see UI-7 to wire it to live backend config.
- **Depends on**: UI-1.

### UI-5 — Integrate UI with Real FastAPI Backend
- Replaced ad-hoc mock wiring with `api.js` (`startNegotiation`, `fetchNegotiation`) and a `VITE_USE_MOCK` flag in `useNegotiation.js` to switch between the real backend and `mock.js`.
- Added a Vite dev proxy (`vite.config.js`) so `/negotiations/*` and `/health` forward to the FastAPI backend without CORS issues.
- **Status**: ✅ Done.
- **Depends on**: UI-2, BE-6.

### UI-6 — Polish
- Typing indicator while waiting for the next agent turn, a TERMINATED banner, message fade-in animation, and an empty-state message before the first poll.
- **Status**: ✅ Done.
- **Depends on**: UI-2, UI-3.

### UI-7 — Wire Negotiation Context Panel to Live Config
- Add `fetchConfig()` to `api.js` and a `useConfig()` hook (mirrors `useNegotiation`'s mock/live split) that fetches `GET /config` once on mount.
- Add `mockConfig()` to `mock.js` for `VITE_USE_MOCK=true` mode, carrying over the static values currently in `inventoryData.js`.
- Update `InventoryContext.jsx` to render from `useConfig()` instead of the static import; show a small loading placeholder and a non-blocking inline error if the fetch fails.
- Delete `inventoryData.js`.
- **Depends on**: UI-4, BE-9.

---

## Notes for All Tickets
- This is a hackathon POC: no fallback/retry infrastructure, no auth, no persistence beyond in-memory state + ClickHouse.
- **[PLACEHOLDER]** tickets must not invent connection details, API keys, or integration shapes — ask the user when the ticket is picked up.
- **Git workflow** (see `INSTRUCTIONS.md` §11): work on a dedicated `ticket/<ID>-<slug>` branch off `master`, commit with clear messages referencing the ticket ID, and push that branch when the ticket is done. Never push directly to `master` — it must always stay in a working state.
