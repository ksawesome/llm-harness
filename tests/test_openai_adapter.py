from pathlib import Path

import pytest

from adapters.openai_adapter import call_openai_api


def test_call_openai_api_synthetic(tmp_path, monkeypatch):
    """Synthetic adapter should create deterministic mock responses."""

    monkeypatch.setenv("LLM_HARNESS_SYNTHETIC_DIR", str(tmp_path))

    result = call_openai_api(
        "gpt-4o-mini",
        "Explain why the sky appears blue during the day.",
        "Provide student-friendly reasoning.",
    )

    assert result["model_version"] == "gpt-4o-mini-synthetic"
    assert "OpenAI synthetic sample" in result["response_text"]
    assert result["tokens_out"] > 0
    assert result["error_message"] is None
    assert result["synthetic"] is True

    synthetic_source = result["synthetic_source"]
    assert synthetic_source is not None
    assert Path(synthetic_source).is_file()


@pytest.mark.parametrize(
    "prompt_text",
    ["", "   "],
)
def test_call_openai_api_empty_prompt_returns_error(prompt_text):
    """Blank prompts should return an error payload and avoid file writes."""

    result = call_openai_api("gpt-4o-mini", prompt_text, "")

    assert result["error_code"] == "invalid-prompt"
    assert result["response_text"] == ""
    assert result["synthetic_source"] is None
