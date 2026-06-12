# Backend — Agentic Negotiation & Procurement Platform

FastAPI service hosting a LangGraph `StateGraph` that runs a Vendor/Buyer
agent negotiation, payment, and invoicing flow in-process. See
`../INSTRUCTIONS.md` for the full spec.

> To run this alongside the UI with one command, use `../startup.sh` from
> the repo root.

## Requirements

- Python 3.11+

## Setup

```bash
cd Backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Environment Variables

LLM calls (`app/llm_client.py`) go through Pioneer.ai's OpenAI-compatible
chat completions API. Config is read from env vars, with `PIONEER_*` names
accepted as aliases for the `PROMISE_*` names:

| Variable | Alias | Default | Notes |
| --- | --- | --- | --- |
| `PROMISE_API_KEY` | `PIONEER_API_KEY` | — | Required for live LLM calls. From pioneer.ai -> Settings -> API Keys. |
| `PROMISE_BASE_URL` | `PIONEER_BASE_URL` | `https://api.pioneer.ai` | |
| `PROMISE_MODEL` | `PIONEER_MODEL` | `gpt-4.1-mini` | Any chat-capable model from `GET /v1/models`. |

The repo's `.env` currently sets `PIONEER_MODEL` to the fine-tuned
negotiation model produced by `../eval/pioneer_mlops.py` (see
`../PIONEER_SETUP.md` Section 5 for the model id and live verification).

If no API key is set, `buyer_agent`/`vendor_agent` fall back to a
deterministic mock-LLM negotiation strategy, so the API works end-to-end
without credentials.

Keep credentials in a `.env` file at the repo root (already gitignored) and
load it into your shell before running the server, e.g.:

```bash
# bash
set -a && source ../.env && set +a

# PowerShell
Get-Content ..\.env | ForEach-Object {
  if ($_ -match '^\s*([^#=]+)=(.*)$') { Set-Item "Env:$($Matches[1])" $Matches[2] }
}
```

## Running the server

```bash
uvicorn app.main:app --reload
```

- `GET /health` — health check
- `POST /negotiations/start` — starts a negotiation in the background, returns `{"transaction_id": ...}`
- `GET /negotiations/{transaction_id}` — current status, message log, and invoice for a negotiation

## Running tests

```bash
pytest
```
