# Project Instructions: Agentic Negotiation & Procurement Platform (Hackathon POC)

This document is the specification for a quick hackathon proof-of-concept: two LLM agents (a **Vendor Agent** and a **Buyer Agent**) negotiate a deal inside a **LangGraph** state graph, backed by a minimal FastAPI backend and a bare-bones React log viewer.

**This is a POC.** No fallback/retry infrastructure, no multi-user config UI, hardcoded demo data. Spend zero time on visual polish.

---

## 1. Architecture Overview

```
                     +-----------------------------+
                     |   Promise Platform (LLMs)   |   <-- [PLACEHOLDER: connection details TBD]
                     +------+----------------+-----+
                            | LLM call        | LLM call
                            v                 v
 POST /negotiations/start ---->  +---------------------------------------+
                                  |       LangGraph Negotiation Graph       |
                                  |                                          |
                                  |   buyer_agent <-------> vendor_agent     |
                                  |          |                               |
                                  |   guardrail_validator (price caps)       |
                                  |          |                               |
                                  |   payment_request --> Stripe             |  <-- [PLACEHOLDER: Stripe details TBD]
                                  |          |                               |
                                  |   payment_authorization                  |
                                  |          |                               |
                                  |   generate_invoice                       |
                                  +-------------------+----------------------+
                                                       | log every step
                                                       v
                                          ClickHouse (msg + tool logs)        <-- [PLACEHOLDER: connection details TBD]

GET /negotiations/{id}  <--- in-memory negotiation state (source of truth for UI)
        ^
        |
   React UI (single page, poll loop, plain log viewer)
```

### Components
1. **Backend (`Backend/`)** — FastAPI app hosting a single LangGraph `StateGraph` that runs the entire negotiation, payment, and invoice flow in-process.
2. **LLM Access (Promise Platform)** — All LLM calls (Vendor + Buyer agent reasoning) go through a thin client targeting the **Promise Platform**. *Connection details are not yet known — see Section 6.*
3. **Payments (Stripe)** — The `payment_request` / `payment_authorization` tools are backed by Stripe. *Integration details are not yet known — see Section 5.*
4. **Observability (ClickHouse)** — Minimal, synchronous logging of agent messages and tool executions. No fallback buffer/queue. *Connection details are not yet known — see Section 7.*
5. **UI (`UI/`)** — Single-page React app that triggers a negotiation and polls for live updates. No config screens.

---

## 2. Entity & Domain Data Structures

Hardcoded for the demo in `Backend/app/config.py` — no UI forms.

### 2.1 Vendor Domain
* **`Product_ID`**: Unique alphanumeric identifier string.
* **`Stock_Quantity`**: Integer, units available.
* **`Floor_Price`** (minimum): Hard lower bound — Vendor Agent cannot finalize below this.
* **`Ceiling_Price`** (maximum): Opening anchor price.

### 2.2 Buyer Domain
* **`Target_Product_ID`**: Must match a Vendor's `Product_ID`.
* **`Desired_Quantity`**: Units required.
* **`Buyer_Floor_Price`**: Ideal/opening bid price.
* **`Buyer_Ceiling_Price`** (maximum): Hard upper bound — Buyer Agent cannot finalize above this.

---

## 3. Negotiation Protocol & State Machine

```
   [INITIATE]
       |
       v
+------+------+
|  NEGOTIATING |<-----------------+
+------+------+                   |
       |                          |
       | Counter-Offer / Reject   |
       v                          |
[EVALUATE & VALIDATE] ------------+
       |
       | Both sides accept, within bounds
       v
+------+------+
|  AGREEMENT   |
+------+------+
       |
       | Vendor calls payment_request
       v
[PAYMENT_PENDING]
       |
       | Buyer calls payment_authorization
       v
+------+------+
|  FULFILLED   | -> generate_invoice -> (END)
+--------------+

Any state -> [TERMINATED]  (turn limit reached, or guardrail violation)
```

### Execution Flow Rules
1. **Initiation**: `buyer_agent` generates the opening message — bid price `P0`, quantity `Q0`.
2. **Turn loop**: `vendor_agent` and `buyer_agent` alternate. Each receives the full message history for the negotiation.
3. **Guardrails (application-enforced, not LLM-trusted)**:
   * After every agent turn, `guardrail_validator` parses the structured price/quantity from the message.
   * If the Vendor proposes/accepts a price `< Floor_Price`, or the Buyer accepts a price `> Buyer_Ceiling_Price`: transition immediately to `TERMINATED`. **No retries.**
   * If `turn` exceeds a fixed max-turns constant: transition to `TERMINATED`.
4. **Agreement → Payment**: Once both sides accept within bounds, status becomes `AGREEMENT` and the Vendor's node calls `payment_request`.
5. **Fulfillment**: The Buyer's node calls `payment_authorization`. On success, status becomes `FULFILLED` and `generate_invoice` runs.

---

## 4. LangGraph Orchestration Design

Single `StateGraph` in `Backend/app/graph.py`.

### Shared State (`NegotiationState`)
```python
class NegotiationState(TypedDict):
    transaction_id: str
    turn: int
    status: Literal["NEGOTIATING", "AGREEMENT", "PAYMENT_PENDING", "FULFILLED", "TERMINATED"]
    messages: list[dict]          # {sender, text, extracted_price, extracted_quantity, timestamp}
    current_price: float | None
    current_quantity: int | None
    vendor_config: dict            # from Section 2.1
    buyer_config: dict             # from Section 2.2
    invoice: dict | None
```

### Nodes
* **`buyer_agent`** — calls the Promise Platform LLM with the buyer system prompt + history, appends a message.
* **`vendor_agent`** — calls the Promise Platform LLM with the vendor system prompt + history, appends a message.
* **`guardrail_validator`** — parses the latest message for price/quantity and accept/counter/reject intent; applies bound checks and the turn-limit check; updates `status`.
* **`payment_request`** — Vendor-side tool call into Stripe (Section 5); sets `status = PAYMENT_PENDING`.
* **`payment_authorization`** — Buyer-side tool call into Stripe (Section 5); sets `status = FULFILLED`.
* **`generate_invoice`** — builds the final invoice dict from agreed price/quantity/transaction_id.

### Routing
* `START -> buyer_agent -> guardrail_validator`
* `guardrail_validator -> vendor_agent` or `guardrail_validator -> buyer_agent` (whichever's turn, while `status == NEGOTIATING`)
* `guardrail_validator -> payment_request` (if `status == AGREEMENT`)
* `guardrail_validator -> END` (if `status == TERMINATED`)
* `payment_request -> payment_authorization -> generate_invoice -> END`

Every node also calls `telemetry.log_message()` / `telemetry.log_tool_execution()` (Section 7) synchronously.

---

## 5. Payment Integration — Stripe `[PLACEHOLDER]`

> **Before implementing this section**: ask the user for Stripe API keys (test mode), preferred flow (PaymentIntents vs. Checkout vs. Invoices API), and any sandbox payment method tokens to use for `payment_authorization`.

### 5.1 `payment_request` (Vendor Agent exclusive)
Input schema:
```json
{
  "transaction_id": "UUIDv4",
  "buyer_agent_id": "STRING",
  "product_id": "STRING",
  "agreed_unit_price": "DECIMAL",
  "quantity": "INTEGER",
  "total_amount": "DECIMAL"
}
```
Suggested default behavior (confirm with user): create a Stripe `PaymentIntent` for `total_amount`, return its ID, transition state to `PAYMENT_PENDING`.

### 5.2 `payment_authorization` (Buyer Agent exclusive)
Input schema:
```json
{
  "transaction_id": "UUIDv4",
  "payment_method_token": "STRING",
  "authorized_amount": "DECIMAL"
}
```
Suggested default behavior (confirm with user): confirm/capture the `PaymentIntent` using a Stripe test payment method. On success, transition to `FULFILLED`.

---

## 6. LLM Integration — Promise Platform `[PLACEHOLDER]`

> **Before implementing this section**: ask the user for the Promise Platform base URL, auth mechanism, request/response format, and model name(s) to use for the Vendor and Buyer agents.

`Backend/app/llm_client.py` exposes a single function, e.g. `generate(system_prompt: str, messages: list[dict]) -> str`, used by the `buyer_agent` and `vendor_agent` nodes. Config via env vars:
```
PROMISE_BASE_URL=
PROMISE_API_KEY=
PROMISE_MODEL=
```
Until details are available, stub `generate()` to raise `NotImplementedError("Promise Platform not configured")` so the rest of the graph can be developed/tested with a mock LLM.

---

## 7. Telemetry — ClickHouse (minimal) `[PLACEHOLDER connection]`

> **Before implementing this section**: ask the user for ClickHouse connection details (host, port, database, credentials).

No fallback buffer/queue — `Backend/app/telemetry.py` performs direct synchronous inserts. If an insert fails, log the error to console and continue; telemetry must never block the negotiation.

### 7.1 Table: `agent_message_logs`
```sql
CREATE TABLE default.agent_message_logs (
    message_id UUID,
    transaction_id UUID,
    timestamp DateTime64(3, 'UTC'),
    conversation_turn UInt32,
    sender_type Enum8('VendorAgent' = 1, 'BuyerAgent' = 2, 'System' = 3),
    sender_id String,
    receiver_id String,
    raw_message String,
    extracted_price Decimal(18, 4),
    extracted_quantity UInt32,
    llm_metadata String  -- JSON string: token count, latency, model name
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (transaction_id, timestamp);
```

### 7.2 Table: `agent_tool_executions`
```sql
CREATE TABLE default.agent_tool_executions (
    tool_execution_id UUID,
    transaction_id UUID,
    timestamp DateTime64(3, 'UTC'),
    agent_id String,
    tool_name LowCardinality(String), -- 'payment_request' or 'payment_authorization'
    payload String,
    execution_status Enum8('Success' = 1, 'Failed' = 2, 'ValidationError' = 3),
    error_message String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (tool_name, transaction_id, timestamp);
```

---

## 8. Backend API (FastAPI)

| Endpoint | Method | Description |
|---|---|---|
| `/negotiations/start` | POST | Generates a `transaction_id`, runs the LangGraph negotiation as a background task, returns `{ "transaction_id": "..." }` immediately. |
| `/negotiations/{transaction_id}` | GET | Returns `{ "transaction_id", "status", "turn", "messages": [...], "invoice": {...} \| null }` from in-memory state. |

An in-memory store (`dict[str, NegotiationState]`) is sufficient for the POC — no persistence layer needed.

---

## 9. Minimal UI

Single-page React app (Vite, no UI component library, minimal CSS):
* "Start Negotiation" button → `POST /negotiations/start`.
* Poll `GET /negotiations/{transaction_id}` every ~1s.
* Render: a scrolling message list (sender, text, price, quantity), a status badge (`NEGOTIATING` / `AGREEMENT` / `PAYMENT_PENDING` / `FULFILLED` / `TERMINATED`), and an invoice block once complete.
* No configuration screens — vendor/buyer params are fixed in the backend.

---

## 10. Out of Scope (explicitly excluded for this POC)
* No fallback/retry buffers for telemetry.
* No retry loops on guardrail violations — immediate termination.
* No multi-user UI, auth, or config forms.
* No persistence beyond in-memory state + ClickHouse logs.

---

## 11. Git Workflow for Tickets

* **`master` must always remain in a working state.** Do not push directly to `master` once ticket work begins (the only exception is the initial project setup commit).
* **One branch per ticket**, branched from the latest `master`: `ticket/<TICKET-ID>-<short-slug>` (e.g. `ticket/BE-2-langgraph-graph`, `ticket/UI-2-log-viewer`).
* **Commit messages**: short imperative summary referencing the ticket ID, e.g. `[BE-2] Add LangGraph negotiation state graph`. Add a body line only if the *why* isn't obvious from the diff.
* **On ticket completion**: commit your changes with a clear message and push the ticket branch to `origin`. Merge into `master` only once that piece runs without errors.

---

For the implementation breakdown by ticket, see `TICKETS.md`.
