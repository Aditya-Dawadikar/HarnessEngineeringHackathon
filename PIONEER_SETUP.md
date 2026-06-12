Read the below URL and related links on the site for support.
https://docs.pioneer.ai/quickstart


Use this setup for creating our Vendor and Buyer Agents

---

## Progress Notes (BE-3 follow-up)

### 1. Docs summary (`https://docs.pioneer.ai/quickstart`)
- Pioneer is an ML inference/fine-tuning platform; chat completions are
  exposed via an **OpenAI-compatible** endpoint.
- Auth: API key generated at pioneer.ai -> Settings -> API Keys, sent via
  the `X-API-Key` header.
- Base URL: `https://api.pioneer.ai`
- Chat endpoint: `POST /v1/chat/completions`
  - Request: `{"model": "...", "messages": [{"role": "...", "content": "..."}]}`
  - Response: standard OpenAI shape, content at
    `choices[0].message.content`
- Model list available via `GET /base-models` (LLM options include
  Qwen/Llama/DeepSeek families).
- No official Python SDK documented -- use `requests` directly.

### 2. Implementation done
- `Backend/app/llm_client.py`: `generate(system_prompt, messages)` now
  POSTs to `{PROMISE_BASE_URL}/v1/chat/completions` with the `X-API-Key`
  header and returns `choices[0].message.content`. Still raises
  `NotImplementedError("Promise Platform not configured")` when
  `PROMISE_API_KEY` is unset, so behavior is unchanged until credentials
  are provided.
- `Backend/app/graph.py`: `buyer_agent` / `vendor_agent` now call
  `llm_client.generate()` with a role-specific system prompt (negotiation
  bounds + required `[OFFER price=X.XX quantity=N action=ACCEPT|COUNTER|REJECT]`
  tag format) and the conversation history mapped to `assistant`/`user`
  roles. If the Promise Platform is not configured (`NotImplementedError`),
  the nodes fall back to the existing mock-LLM midpoint-convergence
  strategy -- so the graph still works end-to-end without credentials.
- `Backend/requirements.txt`: added `requests`.
- Tests: `Backend/tests/test_llm_client.py` and `Backend/tests/test_graph.py`
  cover both the real-client request/response handling and the
  Promise-Platform / mock fallback paths. Full suite: 39/39 passing.

### 3. Live verification (2026-06-12)
- `.env` already had `PIONEER_API_KEY` set (not `PROMISE_API_KEY`).
  `llm_client.py` now reads `PROMISE_*` first and falls back to `PIONEER_*`
  for `BASE_URL` / `API_KEY` / `MODEL`, so the existing `.env` works as-is.
- The placeholder default model `qwen2.5-72b-instruct` does **not** exist on
  Pioneer (`POST /v1/chat/completions` -> 404). Checked `GET /v1/models` --
  switched the default to `gpt-4.1-mini`, which is listed and works.
- Ran a full live negotiation through `build_graph().invoke(...)` against
  the real Pioneer.ai API (model `gpt-4.1-mini`): both agents produced
  well-formed `[OFFER price=... quantity=... action=...]` tags, converged to
  $9.50/unit x 200 units in 6 turns, status `FULFILLED`, invoice generated.
  **Vendor and Buyer Agents are live on Pioneer.ai.**

### 4. Optional follow-ups
- `PROMISE_BASE_URL` / `PIONEER_BASE_URL` default to `https://api.pioneer.ai`
  if unset.
- `PROMISE_MODEL` / `PIONEER_MODEL` default to `gpt-4.1-mini`; override via
  env var to try a different chat model from `GET /v1/models`.
