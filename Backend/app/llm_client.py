"""Promise Platform LLM client.

[PLACEHOLDER] Connection details (base URL, auth mechanism,
request/response format, model name) are not yet known -- see
INSTRUCTIONS.md Section 6. Ask the user for these before implementing
the real client.

Until then, `generate` is a stub so the negotiation graph (BE-2) can be
developed and tested against the mock LLM instead.
"""

import os

PROMISE_BASE_URL = os.environ.get("PROMISE_BASE_URL")
PROMISE_API_KEY = os.environ.get("PROMISE_API_KEY")
PROMISE_MODEL = os.environ.get("PROMISE_MODEL")


def generate(system_prompt: str, messages: list[dict]) -> str:
    raise NotImplementedError("Promise Platform not configured")
