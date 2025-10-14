"""Synthetic Anthropic adapter that routes requests through the mock provider."""

from __future__ import annotations

import logging

from utils.mock_provider import call_mock_api

logger = logging.getLogger(__name__)


def call_anthropic_api(
    model_name: str, prompt_text: str, system_prompt: str
) -> dict:
    """Return a synthetic response for an Anthropic model."""

    logger.info(
        "Using synthetic data for Anthropic model '%s'. No live API request was made.",
        model_name,
    )

    return call_mock_api(
        provider="anthropic",
        model_name=model_name,
        prompt_text=prompt_text,
        system_prompt=system_prompt,
    )
