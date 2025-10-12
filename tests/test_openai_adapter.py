from unittest.mock import patch, MagicMock
from adapters.openai_adapter import call_openai_api


def test_call_openai_api_success():
    """Test successful OpenAI API call."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.model = "gpt-4o-mini"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20

    with patch("adapters.openai_adapter.client") as mock_client:
        mock_client.chat.completions.create.return_value = mock_response

        result = call_openai_api("gpt-4o-mini", "Test prompt", "Test system")

        assert result["model_version"] == "gpt-4o-mini"
        assert result["response_text"] == "Test response"
        assert result["tokens_in"] == 10
        assert result["tokens_out"] == 20
        assert result["error_message"] is None
        assert "latency_ms" in result
        assert "cost_usd" in result


def test_call_openai_api_client_none():
    """Test when OpenAI client is not initialized."""
    with patch("adapters.openai_adapter.client", None):
        result = call_openai_api("gpt-4o-mini", "Test prompt", "Test system")

        assert result["model_version"] == "N/A"
        assert result["response_text"] == ""
        assert result["error_message"] == "OpenAI client failed to initialize."


def test_call_openai_api_exception():
    """Test handling of API exceptions."""
    with patch("adapters.openai_adapter.client") as mock_client:
        mock_client.chat.completions.create.side_effect = Exception(
            "API Error"
        )

        result = call_openai_api("gpt-4o-mini", "Test prompt", "Test system")

        assert result["model_version"] == "gpt-4o-mini"
        assert result["response_text"] == ""
        assert result["error_message"] == "API Error"
