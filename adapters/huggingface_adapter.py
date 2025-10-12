import os
import time
import requests

# --- 1. DEFINE MODEL AND API DETAILS ---
# The specific model endpoint for Llama 3 8B Instruct
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"

# --- 2. DEFINE PRICING ---
# IMPORTANT: This is an ESTIMATE for a hosted provider. The free Hugging Face API has no direct cost,
# but also no performance guarantees. For the paper's cost model, a price must be assumed.
# This estimate is for a hypothetical pay-as-you-go service.
PRICE_PER_1M_INPUT_TOKENS = 0.20  # in USD (Example price)
PRICE_PER_1M_OUTPUT_TOKENS = 0.20  # in USD (Example price)


def call_huggingface_api(
    model_name: str, prompt_text: str, system_prompt: str
) -> dict:
    """
    Makes an API call to the Hugging Face Inference API for Llama 3.
    This function adheres to the standardized adapter interface.
    """
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        return {
            "model_version": model_name,
            "latency_ms": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
            "response_text": "",
            "error_message": "HUGGINGFACE_API_KEY environment variable not found.",
        }

    headers = {"Authorization": f"Bearer {api_key}"}

    # --- 3. FORMAT THE PROMPT FOR LLAMA 3 ---
    # Llama 3 Instruct uses a specific chat template.
    # See: https://llama.meta.com/docs/model-cards-and-prompt-formats/meta-llama-3/
    formatted_prompt = (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        f"{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
        f"{prompt_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    )

    # --- 4. PREPARE THE PAYLOAD ---
    payload = {
        "inputs": formatted_prompt,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.3,
            "return_full_text": False,  # Only return the generated part
        },
        "options": {
            "wait_for_model": True  # Handles cold starts by waiting for the model to load
        },
    }

    try:
        # --- 5. MAKE THE API CALL ---
        start_time = time.perf_counter()

        response = requests.post(API_URL, headers=headers, json=payload)

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        response_data = response.json()

        # --- 6. PARSE THE RESPONSE ---
        # The response is a list containing a dictionary
        response_text = response_data[0]["generated_text"]

        # --- 7. HANDLE TOKEN COUNTS & COST ---
        # LIMITATION: The Hugging Face Serverless Inference API does not return token counts.
        # This is a key finding for the benchmark. We will log 0 and note this limitation.
        tokens_in = 0
        tokens_out = 0
        cost_usd = 0.0  # Cannot be calculated without token counts.

        # --- 8. RETURN STANDARDIZED DICTIONARY ---
        return {
            "model_version": model_name,
            "latency_ms": latency_ms,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost_usd,
            "response_text": response_text.strip(),
            "error_message": None,
        }

    except requests.exceptions.HTTPError as http_err:
        error_message = (
            f"HTTP error occurred: {http_err} - Response: {response.text}"
        )
        return {
            "model_version": model_name,
            "latency_ms": latency_ms if "latency_ms" in locals() else 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
            "response_text": "",
            "error_message": error_message,
        }
    except Exception as e:
        return {
            "model_version": model_name,
            "latency_ms": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
            "response_text": "",
            "error_message": str(e),
        }
