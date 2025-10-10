import os
import time
import google.generativeai as genai

# --- 1. INITIALIZE THE CLIENT ---
# The API key is loaded and configured in main.py using genai.configure().
# We check here if the configuration was successful.
try:
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY environment variable not found.")
    # The genai library is configured globally in main.py, so we just need a model object later.
    genai_is_configured = True
except Exception as e:
    print(f"Error initializing Google GenAI: {e}")
    genai_is_configured = False

# --- 2. DEFINE PRICING (as of Q4 2025, from your paper's context) ---
# It's good practice to keep pricing explicit for cost calculations.
# Replace with the actual pricing for gemini-1.5-flash-latest when you run the final benchmark.
PRICE_PER_1M_INPUT_TOKENS = 0.35  # in USD
PRICE_PER_1M_OUTPUT_TOKENS = 1.05 # in USD


def call_google_api(model_name: str, prompt_text: str, system_prompt: str) -> dict:
    """
    Makes an API call to the specified Google Gemini model and returns a standardized dictionary.
    This function adheres to the standardized adapter interface.
    """
    if not genai_is_configured:
        return {
            "model_version": "N/A",
            "latency_ms": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
            "response_text": "",
            "error_message": "Google GenAI client failed to initialize."
        }
        
    try:
        # --- 3. PREPARE THE MODEL ---
        model = genai.GenerativeModel( # type: ignore
            model_name=model_name,
            system_instruction=system_prompt
        )

        # --- 4. PREPARE GENERATION CONFIG ---
        # Separating the generation config makes the code cleaner
        generation_config = genai.types.GenerationConfig( # type: ignore
            temperature=0.3,
            max_output_tokens=500
        )

        # --- 5. MAKE THE API CALL ---
        start_time = time.perf_counter()
        
        response = model.generate_content(prompt_text, generation_config=generation_config)
        
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        response_text = response.text

        # --- 6. PARSE THE RESPONSE (GET TOKEN COUNTS) ---
        # The Google API requires separate calls to count tokens.
        tokens_in = model.count_tokens(prompt_text).total_tokens
        tokens_out = model.count_tokens(response_text).total_tokens
        model_version = model_name # The response doesn't include a version identifier

        # --- 7. CALCULATE THE COST ---
        cost_usd = (
            (tokens_in / 1_000_000 * PRICE_PER_1M_INPUT_TOKENS) +
            (tokens_out / 1_000_000 * PRICE_PER_1M_OUTPUT_TOKENS)
        )

        # --- 8. RETURN STANDARDIZED DICTIONARY ---
        return {
            "model_version": model_version,
            "latency_ms": latency_ms,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost_usd,
            "response_text": response_text.strip(),
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

