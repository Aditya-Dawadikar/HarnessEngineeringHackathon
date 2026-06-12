"""Promise Platform LLM client.

Backed by the Pioneer.ai OpenAI-compatible chat completions API
(see PIONEER_SETUP.md for the integration notes). Config via env vars
(PIONEER_* names are accepted as aliases, matching Pioneer.ai's own docs):

    PROMISE_BASE_URL / PIONEER_BASE_URL  - defaults to https://api.pioneer.ai
    PROMISE_API_KEY  / PIONEER_API_KEY   - required; sent as the X-API-Key header
    PROMISE_MODEL    / PIONEER_MODEL     - defaults to "gpt-4.1-mini"

If no API key is set, `generate` raises NotImplementedError so the
negotiation graph (BE-2) can fall back to the mock LLM strategy.
"""

import os
from typing import Optional

import requests


def _env(*names: str, default: Optional[str] = None) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return default


PROMISE_BASE_URL = _env("PROMISE_BASE_URL", "PIONEER_BASE_URL", default="https://api.pioneer.ai")
PROMISE_API_KEY = _env("PROMISE_API_KEY", "PIONEER_API_KEY")
PROMISE_MODEL = _env("PROMISE_MODEL", "PIONEER_MODEL", default="gpt-4.1-mini")


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
