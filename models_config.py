# Model configuration for the LLM benchmarking harness
# This file defines the models to test and their corresponding adapter functions.

from pydantic import BaseModel, Field
from typing import Dict, Callable, Optional
from adapters import (
    call_openai_api,
    call_anthropic_api,
    call_google_api,
    call_cohere_api,
    call_huggingface_api,
)


class ModelConfig(BaseModel):
    name: str = Field(..., description="Model identifier")
    adapter: Callable = Field(..., description="Adapter function")
    rate_limit_seconds: float = Field(
        default=10.0, description="Minimum seconds between API calls"
    )
    timeout_seconds: int = Field(default=30, description="API call timeout")
    temperature: Optional[float] = Field(
        default=0.3, description="Override default temperature"
    )


# Dictionary of models to test
models_to_test: Dict[str, ModelConfig] = {
    "gpt-4o-mini": ModelConfig(
        name="gpt-4o-mini",
        adapter=call_openai_api,
    ),
    "claude-3-sonnet-20240229": ModelConfig(
        name="claude-3-sonnet-20240229",
        adapter=call_anthropic_api,
    ),
    "gemini-2.5-flash": ModelConfig(
        name="gemini-2.5-flash",
        adapter=call_google_api,
    ),
    "command-r-08-2024": ModelConfig(
        name="command-r-08-2024",
        adapter=call_cohere_api,
    ),
    "meta-llama-3-8b-instruct": ModelConfig(
        name="meta-llama-3-8b-instruct",
        adapter=call_huggingface_api,
    ),
}

# For backward compatibility, create a simple dict
models_to_test_legacy = {k: v.adapter for k, v in models_to_test.items()}
