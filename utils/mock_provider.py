"""Synthetic provider scaffolding for OpenAI and Anthropic.

The mock provider produces deterministic yet varied completions for each
prompt so downstream analytics can operate without live API calls. All
metadata (latency, token counts, headers) is synthesized to resemble
real responses and written to ``results/synthetic`` for auditing.
"""

from __future__ import annotations

import json
import logging
import math
import hashlib
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

PROMPT_FILE = Path("data/test_prompts.json")
SYNTHETIC_ROOT = Path(
    os.getenv("LLM_HARNESS_SYNTHETIC_DIR", str(Path("results") / "synthetic"))
)
PROVIDERS = {
    "openai": {
        "latency_ms": (620, 120),
        "tokens_out": (190, 35),
        "style": "coherent",
        "headers": {
            "x-ratelimit-limit-requests": "3s:200, 1m:4000",
            "x-ratelimit-remaining-requests": "synthetic",
            "x-request-id": "synthetic-openai",
        },
    },
    "anthropic": {
        "latency_ms": (780, 160),
        "tokens_out": (240, 45),
        "style": "cautious",
        "headers": {
            "x-ratelimit-limit-requests": "3s:100, 1m:2000",
            "x-ratelimit-remaining-requests": "synthetic",
            "x-request-id": "synthetic-anthropic",
        },
    },
}

logger = logging.getLogger(__name__)

_PROMPT_CACHE: Optional[Dict[str, Dict]] = None
_PROMPT_TEXT_LOOKUP: Optional[Dict[str, str]] = None


def _load_prompts() -> Dict[str, Dict]:
    global _PROMPT_CACHE, _PROMPT_TEXT_LOOKUP
    if _PROMPT_CACHE is None:
        with PROMPT_FILE.open("r", encoding="utf-8") as handle:
            prompts: List[Dict] = json.load(handle)
        _PROMPT_CACHE = {item["id"]: item for item in prompts}
        _PROMPT_TEXT_LOOKUP = {
            _normalise_text(item["prompt_text"]): item["id"]
            for item in prompts
        }
    return _PROMPT_CACHE


def _normalise_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _resolve_prompt_id(prompt_text: str) -> str:
    _load_prompts()
    normalised = _normalise_text(prompt_text)
    if _PROMPT_TEXT_LOOKUP and normalised in _PROMPT_TEXT_LOOKUP:
        return _PROMPT_TEXT_LOOKUP[normalised]
    # fallback to deterministic hash-based id
    digest = hashlib.md5(prompt_text.encode("utf-8")).hexdigest()[:10]
    return f"synthetic_{digest}"


def _provider_dir(provider: str) -> Path:
    path = SYNTHETIC_ROOT / provider
    path.mkdir(parents=True, exist_ok=True)
    return path


def _index_path(provider: str) -> Path:
    return _provider_dir(provider) / "index.json"


def _load_index(provider: str) -> Dict[str, Dict]:
    index_path = _index_path(provider)
    if index_path.exists():
        with index_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return {}


def _save_index(provider: str, index: Dict[str, Dict]) -> None:
    index_path = _index_path(provider)
    with index_path.open("w", encoding="utf-8") as handle:
        json.dump(index, handle, indent=2, ensure_ascii=False)


def _write_csv(provider: str, index: Dict[str, Dict]) -> None:
    import csv

    csv_path = _provider_dir(provider) / "responses.csv"
    fieldnames = [
        "prompt_id",
        "model_name",
        "provider",
        "response_text",
        "latency_ms",
        "tokens_in",
        "tokens_out",
        "cost_usd",
        "seed",
        "generated_at",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in index.values():
            writer.writerow({key: record.get(key) for key in fieldnames})


def _seed(provider: str, prompt_id: str) -> int:
    digest = hashlib.sha256(f"{provider}:{prompt_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _rng(provider: str, prompt_id: str) -> random.Random:
    return random.Random(_seed(provider, prompt_id))


def _base_template(prompt: Dict, provider: str, rng: random.Random) -> str:
    category = prompt.get("category", "General")
    expected = prompt.get("expected_keywords", [])
    intro_options = [
        "Let's unpack this step by step.",
        "Here's a way to reason through it.",
        "We can ground this in a quick check.",
    ]
    guidance_options = [
        "focus on the core quantities that drive the result",
        "organise the work by identifying the knowns and unknowns",
        "compare the student's claim with the governing relationships",
    ]
    callouts = [
        "tie the explanation back to the scenario",
        "surface an assumption the student made",
        "quantify an intermediate step to make it concrete",
    ]
    closing = [
        "Ask a follow-up question to confirm their understanding.",
        "Invite them to compute a small example to check the idea.",
        "Encourage them to summarise the updated reasoning in their own words.",
    ]

    intro = rng.choice(intro_options)
    guidance = rng.choice(guidance_options)
    callout = rng.choice(callouts)
    outro = rng.choice(closing)

    keyword_phrase = ""  # Optional snippet referencing keywords
    if expected:
        sampled = rng.sample(expected, k=min(2, len(expected)))
        keyword_phrase = f" Emphasise {', '.join(sampled)} in the explanation."

    body = (
        f"{intro} Because this falls under {category.lower()}, {guidance}. "
        f"Make sure to {callout}.{keyword_phrase} {outro}"
    )

    if provider == "anthropic":
        body += (
            "\n\nAnthropic safety reminder: keep the response supportive,"
            " highlight ethical use, and note boundaries where relevant."
        )
    elif provider == "openai":
        body += (
            "\n\nOpenAI synthetic sample: language is tuned for concise,"
            " connected reasoning with minimal redundancy."
        )

    return body


def _simulate_metrics(
    provider: str,
    prompt_text: str,
    system_prompt: str,
    response_text: str,
) -> Dict[str, float]:
    settings = PROVIDERS[provider]
    rng = random.Random(_seed(provider, response_text))
    mean_latency, std_latency = settings["latency_ms"]
    latency = max(
        120.0,
        rng.gauss(mean_latency, std_latency / 2),
    )
    mean_tokens, std_tokens = settings["tokens_out"]
    tokens_out = max(80, int(rng.gauss(mean_tokens, std_tokens)))

    prompt_tokens = max(60, math.ceil(len(prompt_text.split()) * 1.2))
    system_tokens = math.ceil(len(system_prompt.split()) * 1.1)
    tokens_in = prompt_tokens + system_tokens

    cost = 0.0  # Synthetic runs report zero cost but keep the key for downstream code

    return {
        "latency_ms": round(latency, 2),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": cost,
    }


def _build_record(
    provider: str,
    model_name: str,
    prompt: Dict,
    prompt_text: str,
    system_prompt: str,
) -> Dict:
    prompt_id = prompt["id"]
    rng = _rng(provider, prompt_id)
    response_text = _base_template(prompt, provider, rng)
    metrics = _simulate_metrics(
        provider, prompt_text, system_prompt, response_text
    )

    record = {
        "prompt_id": prompt_id,
        "provider": provider,
        "model_name": model_name,
        "response_text": response_text.strip(),
        "latency_ms": metrics["latency_ms"],
        "tokens_in": metrics["tokens_in"],
        "tokens_out": metrics["tokens_out"],
        "cost_usd": metrics["cost_usd"],
        "seed": _seed(provider, prompt_id),
        "headers": PROVIDERS[provider]["headers"],
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "synthetic": True,
        "synthetic_note": (
            "Generated from canonical prompt set with deterministic paraphrasing."
        ),
        "system_prompt": system_prompt,
        "prompt_text": prompt_text,
    }
    return record


def _ensure_record(
    provider: str,
    model_name: str,
    prompt_id: str,
    prompt_text: str,
    system_prompt: str,
) -> Dict:
    index = _load_index(provider)
    if prompt_id not in index:
        prompt_catalog = _load_prompts()
        prompt = prompt_catalog.get(prompt_id)
        if prompt is None:
            prompt = {
                "id": prompt_id,
                "category": "Synthetic",
                "expected_keywords": [],
            }
        record = _build_record(
            provider, model_name, prompt, prompt_text, system_prompt
        )
        index[prompt_id] = record
        _save_index(provider, index)
        _write_csv(provider, index)
        record_path = _provider_dir(provider) / f"{prompt_id}.json"
        with record_path.open("w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, ensure_ascii=False)
    return index[prompt_id]


def call_mock_api(
    provider: str,
    model_name: str,
    prompt_text: str,
    system_prompt: str,
) -> Dict:
    """Return a synthetic completion for the requested provider."""

    provider_key = provider.lower()
    if provider_key not in PROVIDERS:
        raise ValueError(f"Unsupported synthetic provider '{provider}'.")

    prompt_text = prompt_text or ""
    system_prompt = system_prompt or ""

    if not prompt_text.strip():
        return {
            "model_version": f"{model_name}-synthetic",
            "latency_ms": 0.0,
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
            "response_text": "",
            "error_message": "Synthetic provider requires non-empty prompt text.",
            "error_code": "invalid-prompt",
            "headers": {},
            "synthetic": True,
            "synthetic_source": None,
        }

    prompt_id = _resolve_prompt_id(prompt_text)
    record = _ensure_record(
        provider_key, model_name, prompt_id, prompt_text, system_prompt
    )

    logger.debug(
        "Synthetic %s completion served for prompt '%s' (seed=%s)",
        provider_key,
        prompt_id,
        record["seed"],
    )

    return {
        "model_version": f"{model_name}-synthetic",
        "latency_ms": record["latency_ms"],
        "tokens_in": record["tokens_in"],
        "tokens_out": record["tokens_out"],
        "cost_usd": record["cost_usd"],
        "response_text": record["response_text"],
        "error_message": None,
        "error_code": None,
        "headers": record["headers"],
        "synthetic": True,
        "synthetic_source": str(
            _provider_dir(provider_key) / f"{prompt_id}.json"
        ),
    }


def ensure_synthetic_runs(providers: Optional[Iterable[str]] = None) -> None:
    """Generate synthetic data for all prompts for the specified providers."""

    target_providers = providers or PROVIDERS.keys()
    prompt_catalog = _load_prompts()

    for provider in target_providers:
        provider_key = provider.lower()
        for prompt in prompt_catalog.values():
            _ensure_record(
                provider_key,
                model_name=f"{provider_key}-synthetic",
                prompt_id=prompt["id"],
                prompt_text=prompt["prompt_text"],
                system_prompt=prompt.get("teacher_context", "") or "",
            )

        logger.info(
            "Synthetic store refreshed for provider %s (%d prompts)",
            provider_key,
            len(prompt_catalog),
        )
