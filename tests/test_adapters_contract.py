import adapters

REQUIRED_KEYS = {
    "model_version",
    "latency_ms",
    "tokens_in",
    "tokens_out",
    "cost_usd",
    "response_text",
    "error_message",
}


def test_adapters_return_contract():
    """Ensure every exported adapter returns the canonical keys and types.

    This test calls each adapter exported from `adapters.__init__` using the
    synthetic/mock providers so tests run without network access or API keys.
    """
    for name in adapters.__all__:
        fn = getattr(adapters, name)
        assert callable(fn), f"Adapter {name} is not callable"
        result = fn("test-model", "Hello world.", "system: be helpful")
        assert isinstance(result, dict), f"{name} did not return a dict"
        missing = REQUIRED_KEYS - set(result.keys())
        assert not missing, f"Adapter {name} missing keys: {missing}"

        # Basic type assertions
        assert isinstance(result["response_text"], str)
        assert isinstance(result["latency_ms"], (int, float))
        assert isinstance(result["tokens_in"], int)
        assert isinstance(result["tokens_out"], int)
