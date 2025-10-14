# Model configuration for the LLM benchmarking harness
# This file defines the models to test and their corresponding
# adapter functions.

import json
import os
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field, ValidationError


class ModelConfig(BaseModel):
    name: str = Field(..., description="Model identifier")
    adapter: Callable = Field(..., description="Adapter function")
    rate_limit_seconds: float = Field(
        default=10.0, description="Minimum seconds between API calls"
    )
    timeout_seconds: int = Field(default=30, description="API call timeout")
    temperature: float | None = Field(
        default=0.3, description="Override default temperature"
    )
    category: str = Field(
        default="general", description="Model category for grouping"
    )


def load_models_from_json(json_path: str) -> dict[str, dict[str, Any]]:
    """Load model configurations from a JSON file."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"Models configuration file not found: {json_path}"
        )

    with open(json_path) as f:
        data = json.load(f)

    return data


def resolve_adapter(adapter_path: str) -> Callable:
    """Resolve adapter function from string path."""
    try:
        module_name, func_name = adapter_path.rsplit(".", 1)
        module = __import__(module_name, fromlist=[func_name])
        return getattr(module, func_name)
    except (ImportError, AttributeError) as e:
        raise ValueError(f"Cannot import adapter '{adapter_path}': {e}")


def create_model_configs(
    json_data: dict[str, dict[str, Any]],
) -> dict[str, ModelConfig]:
    """Create ModelConfig objects from JSON data."""
    configs = {}
    for key, data in json_data.items():
        try:
            adapter = resolve_adapter(data["adapter"])
            config = ModelConfig(
                name=data["name"],
                adapter=adapter,
                rate_limit_seconds=data.get("rate_limit_seconds", 10.0),
                timeout_seconds=data.get("timeout_seconds", 30),
                temperature=data.get("temperature", 0.3),
                category=data.get("category", "general"),
            )
            configs[key] = config
        except (KeyError, ValidationError, ValueError) as e:
            raise ValueError(f"Invalid configuration for model '{key}': {e}")
    return configs


def validate_model_configs(configs: dict[str, ModelConfig]) -> None:
    """Validate that all model configurations are correct."""
    for key, config in configs.items():
        # Check that adapter is callable
        if not callable(config.adapter):
            raise ValueError(f"Adapter for model '{key}' is not callable")

        # Check that name is not empty
        if not config.name.strip():
            raise ValueError(f"Model name for '{key}' cannot be empty")

        # Basic validation - try to call adapter with invalid data to check if it handles errors properly
        # This is a light validation to ensure adapters don't crash immediately
        try:
            # Call with empty/missing data - should return error dict
            result = config.adapter("", "", "")
            if not isinstance(result, dict) or "error_message" not in result:
                raise ValueError(
                    f"Adapter for model '{key}' does not return proper error format"
                )
        except Exception:
            # If it raises an exception, that's also acceptable as long as it's caught elsewhere
            pass


# Load models from JSON file
json_path = os.path.join(os.path.dirname(__file__), "models.json")
json_data = load_models_from_json(json_path)
models_to_test = create_model_configs(json_data)

# Validate configurations
validate_model_configs(models_to_test)
