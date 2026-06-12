import pytest

from app.llm_client import generate


def test_generate_raises_not_implemented_until_promise_platform_is_configured():
    with pytest.raises(NotImplementedError, match="Promise Platform not configured"):
        generate("You are a helpful agent.", [])
