"""Synthetic OpenAI adapter that delegates to the mock provider."""

from __future__ import annotations

import logging
from typing import Dict

from utils.mock_provider import call_mock_api

logger = logging.getLogger(__name__)


def call_openai_api(
    model_name: str, prompt_text: str, system_prompt: str
) -> Dict:
    """Return a synthetic response for an OpenAI model.

    The return payload mirrors the structure produced by the live adapter,
    including rate-limit metadata and error fields.
    """

    logger.info(
        "Using synthetic data for OpenAI model '%s'. No live API request was made.",
        model_name,
    )

    return call_mock_api(
        provider="openai",
        model_name=model_name,
        prompt_text=prompt_text,
        system_prompt=system_prompt,
    )
