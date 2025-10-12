import os
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI, APIError, RateLimitError

# --- 1. INITIALIZE THE CLIENT ---
# The API key is loaded from .env in main.py and set as an environment variable
# The OpenAI client automatically reads the OPENAI_API_KEY environment variable.
try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

# --- 2. DEFINE PRICING (as of Q4 2025) ---
# It's good practice to keep pricing explicit for cost calculations.
# Replace with the actual pricing for gpt-4o-mini when you run the final benchmark.
PRICE_PER_1M_INPUT_TOKENS = 0.15  # in USD
PRICE_PER_1M_OUTPUT_TOKENS = 0.60 # in USD


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((APIError, RateLimitError))
)
def call_openai_api(model_name: str, prompt_text: str, system_prompt: str) -> dict:
    """
    Makes an API call to the specified OpenAI model and returns a standardized dictionary.
    This function adheres to the standardized adapter interface.
    """
    if not client:
        return {
            "model_version": "N/A",
            "latency_ms": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
            "response_text": "",
            "error_message": "OpenAI client failed to initialize."
        }

    try:
        # --- 3. MAKE THE API CALL ---
        start_time = time.perf_counter()

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.3, # Using the balanced setting from the paper's temp sweep
            max_tokens=500   # As specified in the paper's pseudo-code
        )
        
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # --- 4. PARSE THE RESPONSE ---
        response_text = response.choices[0].message.content
        model_version = response.model
        if response.usage is not None:
            tokens_in = response.usage.prompt_tokens
            tokens_out = response.usage.completion_tokens
        else:
            tokens_in = 0
            tokens_out = 0

        # --- 5. CALCULATE THE COST ---
        cost_usd = (
            (tokens_in / 1_000_000 * PRICE_PER_1M_INPUT_TOKENS) +
            (tokens_out / 1_000_000 * PRICE_PER_1M_OUTPUT_TOKENS)
        )

        # --- 6. RETURN STANDARDIZED DICTIONARY ---
        return {
            "model_version": model_version,
            "latency_ms": latency_ms,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost_usd,
            "response_text": response_text.strip() if response_text is not None else "",
            "error_message": None
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
            "error_message": str(e)
        }
