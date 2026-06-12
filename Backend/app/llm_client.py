"""Promise Platform LLM client.

Backed by the Pioneer.ai OpenAI-compatible chat completions API
(see PIONEER_SETUP.md for the integration notes). Config via env vars:

    PROMISE_BASE_URL  - defaults to https://api.pioneer.ai
    PROMISE_API_KEY   - required; sent as the X-API-Key header
    PROMISE_MODEL     - defaults to "qwen2.5-72b-instruct"

If PROMISE_API_KEY is not set, `generate` raises NotImplementedError so the
negotiation graph (BE-2) can fall back to the mock LLM strategy.
"""

import os

import requests

PROMISE_BASE_URL = os.environ.get("PROMISE_BASE_URL", "https://api.pioneer.ai")
PROMISE_API_KEY = os.environ.get("PROMISE_API_KEY")
PROMISE_MODEL = os.environ.get("PROMISE_MODEL", "qwen2.5-72b-instruct")


def generate(system_prompt: str, messages: list[dict]) -> str:
    if not PROMISE_API_KEY:
        raise NotImplementedError("Promise Platform not configured")

    response = requests.post(
        f"{PROMISE_BASE_URL}/v1/chat/completions",
        headers={
            "X-API-Key": PROMISE_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "model": PROMISE_MODEL,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
