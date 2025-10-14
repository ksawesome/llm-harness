import argparse
import asyncio
import csv
import json
import logging
import os
import time
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from tqdm.asyncio import tqdm

from models_config import models_to_test
from prompt_utils import (
    add_helm_style_prompts,
    expand_prompts_with_templates,
    load_system_prompts,
    load_test_prompts,
)

# Import the adapter functions from the adapters directory
# (functions are accessed via getattr on the adapters module)


class RateLimiter:
    """Simple async rate limiter ensuring a minimum delay between calls."""

    def __init__(self, min_interval_seconds: float) -> None:
        self._min_interval = min_interval_seconds
        self._lock = asyncio.Lock()
        self._last_call = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait_time = self._min_interval - (now - self._last_call)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                now = time.monotonic()
            self._last_call = now


# --- 1. SETUP AND CONFIGURATION ---
def setup_environment():
    """Load environment variables from .env file."""
    load_dotenv()
    # No need to configure clients here, adapters will handle it.


def load_data(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        exit()
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} is not a valid JSON file.")
        exit()


# --- 2. MAIN EXECUTION LOGIC ---
async def run_benchmark(args):
    """
    Main function to run the benchmarking harness.
    """
    # Set up logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(
                os.path.join("logs", f"benchmark_{timestamp}.log")
            ),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(__name__)

    def filter_configs_for_api_keys(configs):
        """Remove configs requiring API keys that are not present."""

        adapter_requirements = {
            "call_google_api": ("GOOGLE_API_KEY", "Google"),
            "call_cohere_api": ("COHERE_API_KEY", "Cohere"),
            "call_huggingface_api": ("HUGGINGFACE_API_KEY", "Hugging Face"),
        }

        filtered = {}
        skipped = []

        for model_key, config in configs.items():
            adapter_name = getattr(config.adapter, "__name__", "")
            requirement = adapter_requirements.get(adapter_name)
            if requirement:
                env_key, provider = requirement
                if not os.getenv(env_key):
                    skipped.append((model_key, provider, env_key))
                    continue
            filtered[model_key] = config

        for model_key, provider, env_key in skipped:
            logger.warning(
                "Skipping %s because %s API key (%s) is not set.",
                model_key,
                provider,
                env_key,
            )

        return filtered

    # Load the datasets with validation
    test_prompts = load_test_prompts("data/test_prompts.json")
    system_prompts = load_system_prompts("data/system_prompts.json")

    # Optionally expand with HELM-style prompts
    if args.include_helm:
        test_prompts = add_helm_style_prompts(test_prompts)
        logger.info(
            f"Added HELM-style prompts. Total prompts: {len(test_prompts)}"
        )

    # Apply Jinja2 templating if template variables are provided
    template_vars = {}
    if args.template_vars:
        try:
            # Parse template variables as JSON
            import json

            template_vars = json.loads(args.template_vars)
        except json.JSONDecodeError:
            logger.error(
                f"Invalid JSON for template variables: {args.template_vars}"
            )
            return

    if template_vars:
        test_prompts = expand_prompts_with_templates(
            test_prompts, template_vars
        )
        logger.info(
            f"Applied template variables: {list(template_vars.keys())}"
        )

    # Handle prompt range
    if args.prompt_range:
        try:
            if "-" in args.prompt_range:
                start, end = map(int, args.prompt_range.split("-"))
                selected_prompts = test_prompts[start - 1 : end]
            else:
                idx = int(args.prompt_range) - 1
                selected_prompts = [test_prompts[idx]]
        except (ValueError, IndexError):
            logger.error(f"Invalid prompt range: {args.prompt_range}")
            return
    else:
        selected_prompts = test_prompts

    # Filter models if a specific one was requested via command line
    if args.model:
        if args.model not in models_to_test:
            logger.error(
                f"Model '{args.model}' is not a valid choice. "
                f"Available models are: {list(models_to_test.keys())}"
            )
            return
        # Create a new dictionary with only the selected model
        selected_configs = {args.model: models_to_test[args.model]}
    elif args.category:
        # Filter models by category
        selected_configs = {
            k: v
            for k, v in models_to_test.items()
            if v.category == args.category
        }
        if not selected_configs:
            logger.error(
                f"No models found for category '{args.category}'. "
                f"Available categories: {list(set(v.category for v in models_to_test.values()))}"
            )
            return
    else:
        selected_configs = models_to_test

    selected_configs = filter_configs_for_api_keys(selected_configs)

    if not selected_configs:
        logger.error(
            "No models available to run. Set the required API keys or choose synthetic providers."
        )
        return

    models_to_run = {k: v.adapter for k, v in selected_configs.items()}

    logger.info(
        "Running models: %s",
        list(models_to_run.keys()),
    )

    # Select the system prompt to use for this run
    try:
        system_prompt_text = system_prompts[args.system_prompt]
    except KeyError:
        available_keys = list(system_prompts.keys())
        logger.error(
            f"System prompt key '{args.system_prompt}' not found in "
            f"system_prompts.json. Available keys: {available_keys}"
        )
        return

    if args.dry_run:
        logger.info("Dry run mode: No API calls will be made.")
        logger.info(f"Selected prompts: {len(selected_prompts)}")
        logger.info(f"Selected models: {list(models_to_run.keys())}")
        logger.info(f"System prompt: {args.system_prompt}")
        return

    # --- 3. LOGGING AND OUTPUT SETUP ---
    # Create results directory if it doesn't exist
    output_dir = "results/raw_output"
    os.makedirs(output_dir, exist_ok=True)

    # Generate a unique filename with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(
        output_dir, f"benchmark_results_{timestamp}.csv"
    )
    temp_filename = output_filename + ".tmp"

    # Create an empty DataFrame with the correct columns based on your
    # paper's appendix
    results_df = pd.DataFrame(
        columns=[
            "prompt_id",
            "model",
            "model_version",
            "date_time",
            "latency_ms",
            "tokens_in",
            "tokens_out",
            "cost_usd",
            "response_text",
            "error_message",
            "response_length",
        ]
    )
    results_df.to_csv(
        temp_filename, index=False, quoting=csv.QUOTE_ALL
    )  # Write header
    logger.info(f"Logging results to {output_filename}")

    # --- 4. MAIN BENCHMARKING LOOP ---
    rate_limiters = {
        config.adapter: RateLimiter(config.rate_limit_seconds)
        for config in selected_configs.values()
    }

    async def call_model_with_rate_limit(
        model_name, adapter_function, prompt_text
    ):
        limiter = rate_limiters[adapter_function]
        await limiter.acquire()
        try:
            response_dict = await asyncio.to_thread(
                adapter_function,
                model_name=model_name,
                prompt_text=prompt_text,
                system_prompt=system_prompt_text,
            )

            # Check if API failed and fall back to synthetic data
            if response_dict.get("error_message"):
                logger.warning(
                    f"{model_name}: API failed - falling back to synthetic data"
                )
                from utils.mock_provider import call_mock_api

                synthetic_response = call_mock_api(
                    provider=adapter_function.__name__.replace(
                        "call_", ""
                    ).replace("_api", ""),
                    model_name=model_name,
                    prompt_text=prompt_text,
                    system_prompt=system_prompt_text,
                )
                synthetic_response["api_failed"] = True
                return model_name, synthetic_response

        except Exception as e:
            logger.error(
                f"Exception occurred while calling API for {model_name}: {e} - falling back to synthetic data"
            )
            # Fall back to synthetic data on exception
            try:
                from utils.mock_provider import call_mock_api

                synthetic_response = call_mock_api(
                    provider=adapter_function.__name__.replace(
                        "call_", ""
                    ).replace("_api", ""),
                    model_name=model_name,
                    prompt_text=prompt_text,
                    system_prompt=system_prompt_text,
                )
                synthetic_response["api_failed"] = True
                return model_name, synthetic_response
            except Exception as mock_e:
                logger.error(
                    f"Synthetic fallback also failed for {model_name}: {mock_e}"
                )
                return model_name, {
                    "model_version": "N/A",
                    "latency_ms": 0,
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "cost_usd": 0.0,
                    "response_text": "",
                    "error_message": f"API and synthetic fallback both failed: {str(e)}",
                    "api_failed": True,
                }
        return model_name, response_dict

    total_tasks = len(selected_prompts) * len(models_to_run)
    with tqdm(total=total_tasks, desc="Benchmarking Progress") as pbar:
        for prompt_data in selected_prompts:
            prompt_id = prompt_data["id"]
            prompt_text = prompt_data["prompt_text"]

            if prompt_data.get("teacher_context"):
                context = prompt_data["teacher_context"]
                full_prompt = f"Context: {context}\n\n{prompt_text}"
            else:
                full_prompt = prompt_text

            logger.info(f"Running prompt: {prompt_id}")

            tasks = [
                asyncio.create_task(
                    call_model_with_rate_limit(
                        model_name, adapter_function, full_prompt
                    )
                )
                for model_name, adapter_function in models_to_run.items()
            ]

            results = await asyncio.gather(*tasks)

            for model_name, response_dict in results:
                response_text = response_dict.get("response_text", "")
                response_length = (
                    len(response_text)
                    if not response_dict.get("error_message")
                    else 0
                )
                log_entry = {
                    "prompt_id": prompt_id,
                    "model": model_name,
                    **response_dict,
                    "response_length": response_length,
                    "date_time": datetime.now().isoformat(),
                    "api_failed": response_dict.get("api_failed", False),
                }

                pd.DataFrame([log_entry]).to_csv(
                    temp_filename,
                    mode="a",
                    header=False,
                    index=False,
                    quoting=csv.QUOTE_ALL,
                )

                if response_dict.get("error_message"):
                    logger.warning(
                        f"{model_name}: ERROR - "
                        f"{response_dict['error_message']}"
                    )
                else:
                    latency = response_dict.get("latency_ms") or 0
                    logger.info(f"{model_name}: completed in {latency:.0f} ms")
                pbar.update(1)

    # Atomic rename
    os.rename(temp_filename, output_filename)
    logger.info(f"Benchmark run complete. Results saved to {output_filename}")


if __name__ == "__main__":
    # --- 5. ARGUMENT PARSING for flexibility ---
    parser = argparse.ArgumentParser(
        description="Run the LLM Benchmarking Harness."
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Run the benchmark for a single specified model.",
        choices=list(models_to_test.keys()),
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Run the benchmark for models in a specific category (e.g., 'fast', 'accurate').",
    )
    parser.add_argument(
        "--system_prompt",
        type=str,
        default="strict_socratic",
        help="Specify which system prompt to use for the run.",
        choices=[
            "strict_socratic",
            "neutral_instruction",
            "hybrid_conversational",
        ],
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making API calls.",
    )
    parser.add_argument(
        "--prompt-range",
        type=str,
        help="Specify a range of prompts to run, e.g., '1-5' or '3'.",
    )
    parser.add_argument(
        "--include-helm",
        action="store_true",
        help="Include HELM-style prompts in the benchmark.",
    )
    parser.add_argument(
        "--template-vars",
        type=str,
        help="JSON string of template variables for prompt expansion.",
    )

    # Setup environment once
    setup_environment()

    # Parse arguments and run main function
    args = parser.parse_args()
    asyncio.run(run_benchmark(args))
