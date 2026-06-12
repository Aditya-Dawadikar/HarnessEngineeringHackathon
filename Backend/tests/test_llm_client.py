import pytest

from app import llm_client
from app.llm_client import generate


def test_generate_raises_not_implemented_when_api_key_missing(monkeypatch):
    monkeypatch.setattr(llm_client, "PROMISE_API_KEY", None)

    with pytest.raises(NotImplementedError, match="Promise Platform not configured"):
        generate("You are a helpful agent.", [])


def test_generate_posts_to_chat_completions_and_returns_message_content(monkeypatch):
    monkeypatch.setattr(llm_client, "PROMISE_API_KEY", "test-key")
    monkeypatch.setattr(llm_client, "PROMISE_BASE_URL", "https://api.pioneer.ai")
    monkeypatch.setattr(llm_client, "PROMISE_MODEL", "qwen2.5-72b-instruct")

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "[OFFER price=9.00 quantity=200 action=COUNTER]"}}]}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(llm_client.requests, "post", fake_post)

    result = generate(
        "You are a vendor agent.",
        [{"role": "user", "content": "I'd like to buy 200 units"}],
    )

    assert result == "[OFFER price=9.00 quantity=200 action=COUNTER]"
    assert captured["url"] == "https://api.pioneer.ai/v1/chat/completions"
    assert captured["headers"]["X-API-Key"] == "test-key"
    assert captured["headers"]["Content-Type"] == "application/json"
    assert captured["json"]["model"] == "qwen2.5-72b-instruct"
    assert captured["json"]["messages"][0] == {"role": "system", "content": "You are a vendor agent."}
    assert captured["json"]["messages"][1] == {"role": "user", "content": "I'd like to buy 200 units"}


def test_generate_raises_for_non_2xx_response(monkeypatch):
    monkeypatch.setattr(llm_client, "PROMISE_API_KEY", "test-key")
    monkeypatch.setattr(llm_client, "PROMISE_BASE_URL", "https://api.pioneer.ai")
    monkeypatch.setattr(llm_client, "PROMISE_MODEL", "qwen2.5-72b-instruct")

    class FakeResponse:
        def raise_for_status(self):
            raise llm_client.requests.HTTPError("500 Server Error")

        def json(self):
            return {}

    monkeypatch.setattr(llm_client.requests, "post", lambda *a, **k: FakeResponse())

    with pytest.raises(llm_client.requests.HTTPError):
        generate("You are a helpful agent.", [])
