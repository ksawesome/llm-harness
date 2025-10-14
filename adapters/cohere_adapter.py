import os
import time

import cohere

# --- 1. INITIALIZE THE CLIENT ---
# The API key is loaded from the .env file in main.py.
# The Cohere client takes the API key as an argument.
try:
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        raise ValueError("COHERE_API_KEY environment variable not found.")
    co = cohere.Client(api_key)
except Exception as e:
    print(f"Error initializing Cohere client: {e}")
    co = None

# --- 2. DEFINE PRICING (as of Q4 2025, from your paper's context) ---
# It's good practice to keep pricing explicit for cost calculations.
# Replace with the actual pricing for command-r when you run the final benchmark.
PRICE_PER_1M_INPUT_TOKENS = 0.50  # in USD
PRICE_PER_1M_OUTPUT_TOKENS = 1.50  # in USD


def call_cohere_api(
    model_name: str, prompt_text: str, system_prompt: str
) -> dict:
    """
    Makes an API call to the specified Cohere model and returns a standardized dictionary.
    This function adheres to the standardized adapter interface.
    """
    if not co:
        return {
            "model_version": "N/A",
            "latency_ms": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
            "response_text": "",
            "error_message": "Cohere client failed to initialize.",
        }

    try:
        # --- 3. MAKE THE API CALL ---
        start_time = time.perf_counter()

        # Cohere uses 'preamble' for the system prompt and 'message' for the user prompt.
        response = co.chat(
            model=model_name,
            preamble=system_prompt,
            message=prompt_text,
            temperature=0.3,  # Using the balanced setting from your paper's temp sweep
        )

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # --- 4. PARSE THE RESPONSE ---
        response_text = response.text
        # The meta object contains token usage information
        tokens_in = 0
        tokens_out = 0
        model_version = model_name
        meta = getattr(response, "meta", None)
        if meta and getattr(meta, "billed_units", None):
            tokens_in = getattr(meta.billed_units, "input_tokens", 0)
            tokens_out = getattr(meta.billed_units, "output_tokens", 0)
        if meta and getattr(meta, "api_version", None):
            model_version = getattr(meta.api_version, "version", model_name)

        # --- 5. CALCULATE THE COST ---
        cost_usd = (tokens_in / 1_000_000 * PRICE_PER_1M_INPUT_TOKENS) + (
            tokens_out / 1_000_000 * PRICE_PER_1M_OUTPUT_TOKENS
        )

        # --- 6. RETURN STANDARDIZED DICTIONARY ---
        return {
            "model_version": model_version,
            "latency_ms": latency_ms,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost_usd,
            "response_text": response_text.strip(),
            "error_message": None,
        }

    except Exception as e:
        # If the API call fails, return a dictionary with the error message
        return {
            "model_version": model_name,
            "latency_ms": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
            "response_text": "",
            "error_message": str(e),
        }
