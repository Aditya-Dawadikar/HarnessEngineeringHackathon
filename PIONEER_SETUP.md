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

### 5. Switched to the fine-tuned negotiation model (2026-06-12)
- `eval/pioneer_mlops.py` generated a synthetic `negotiation-agent-evals`
  dataset and fine-tuned `Qwen/Qwen3-8B` (LoRA) on it via Pioneer's
  `/felix/training-jobs` API. Job/dataset/model ids are recorded in
  `eval/pioneer_mlops.log`:
  - `training_job_id`: `45ad5870-ba44-42d0-ad44-5c0902043fca`
  - `model_name`: `negotiation-agent-evals-20260612211958`
  - `base_model`: `Qwen/Qwen3-8B`
  - `dataset`: `negotiation-agent-evals` (version 2)
- Checked `GET /felix/training-jobs`: this job is `status=deployed`,
  `normalized_status=complete`, `is_terminal_status=true`,
  `provider_deployments.modal.status=active` -- the fine-tuned adapter is
  live and callable.
- `.env` now sets `PIONEER_MODEL=45ad5870-ba44-42d0-ad44-5c0902043fca`
  (the training job id is the model id for `/v1/chat/completions`), so
  `llm_client.generate()` -- and therefore both `buyer_agent` and
  `vendor_agent` -- now call this fine-tuned model instead of
  `gpt-4.1-mini`. This keeps the live agents in sync with the model
  produced by `eval/pioneer_mlops.py`.
- Live verification: ran `build_graph().invoke(...)` with the default
  `VENDOR_CONFIG`/`BUYER_CONFIG` (`Backend/app/config.py`). All 7 turns
  show `llm_metadata.source == "promise_platform"`. Negotiation converged
  to $9.50/unit x 200 units ($1900 total) in 7 turns, status `FULFILLED`,
  invoice + mock Stripe payment flow (BE-8) completed successfully.
- A single turn against this model uses ~120 total tokens (per
  `usage.total_tokens` in the raw `/v1/chat/completions` response),
  noticeably cheaper than a general-purpose model for this task.
