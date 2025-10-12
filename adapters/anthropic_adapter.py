import time
import anthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# --- 1. INITIALIZE THE CLIENT ---
# The API key is loaded from the .env file in main.py and set as an
# environment variable.
# The Anthropic client automatically reads the ANTHROPIC_API_KEY
# environment variable.
try:
    client = anthropic.Anthropic()
except Exception as e:
    print(f"Error initializing Anthropic client: {e}")
    client = None

# --- 2. DEFINE PRICING (as of Q4 2025, from your paper's context) ---
# It's good practice to keep pricing explicit for cost calculations.
# Replace with the actual pricing for claude-3-sonnet-20240229 when
# you run the final benchmark.
PRICE_PER_1M_INPUT_TOKENS = 3.00  # in USD
PRICE_PER_1M_OUTPUT_TOKENS = 15.00  # in USD


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(anthropic.APIError),
)
def call_anthropic_api(
    model_name: str, prompt_text: str, system_prompt: str
) -> dict:
    """
    Makes an API call to the specified Anthropic model and returns a standardized dictionary.
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
            "error_message": "Anthropic client failed to initialize.",
        }

    try:
        # --- 3. MAKE THE API CALL ---
        start_time = time.perf_counter()

        response = client.messages.create(
            model=model_name,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.3,  # Using the balanced setting from your paper's temp sweep
            max_tokens=500,  # As specified in your paper's pseudo-code
        )

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        # --- 4. PARSE THE RESPONSE ---
        # Anthropic's response structure is slightly different from OpenAI's
        # Concatenate all text blocks in response.content
        # Only concatenate text from blocks of type TextBlock
        response_text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        model_version = response.model
        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens

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
