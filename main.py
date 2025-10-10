import os
import json
import time
import argparse
import pandas as pd
from datetime import datetime

# Import the adapter functions from the adapters directory
from adapters import call_openai_api
from adapters import call_anthropic_api
from adapters import call_cohere_api
from adapters import call_google_api
from adapters import call_huggingface_api

from dotenv import load_dotenv

# --- 1. SETUP AND CONFIGURATION ---
def setup_environment():
    """Load environment variables from .env file."""
    load_dotenv()
    # No need to configure clients here, adapters will handle it.

def load_data(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        exit()
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} is not a valid JSON file.")
        exit()

# --- 2. MAIN EXECUTION LOGIC ---
def main(args):
    """
    Main function to run the benchmarking harness.
    """
    # Load the datasets
    test_prompts = load_data('data/test_prompts.json')
    system_prompts = load_data('data/system_prompts.json')

    # Define the models and their corresponding adapter functions
    # This makes the main loop cleaner and more extensible.
    models_to_test = {
        "gpt-4o-mini": call_openai_api,
        "claude-3-sonnet-20240229": call_anthropic_api,
        "gemini-1.5-flash-latest": call_google_api,
        "command-r": call_cohere_api,
        "meta-llama-3-8b-instruct": call_huggingface_api
    }

    # Filter models if a specific one was requested via command line
    if args.model:
        if args.model not in models_to_test:
            print(f"Error: Model '{args.model}' is not a valid choice. Available models are: {list(models_to_test.keys())}")
            return
        # Create a new dictionary with only the selected model
        models_to_run = {args.model: models_to_test[args.model]}
    else:
        models_to_run = models_to_test

    # Select the system prompt to use for this run
    try:
        system_prompt_text = system_prompts[args.system_prompt]
    except KeyError:
        print(f"Error: System prompt key '{args.system_prompt}' not found in system_prompts.json. Available keys: {list(system_prompts.keys())}")
        return

    # --- 3. LOGGING AND OUTPUT SETUP ---
    # Create results directory if it doesn't exist
    output_dir = "results/raw_output"
    os.makedirs(output_dir, exist_ok=True)

    # Generate a unique filename with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(output_dir, f"benchmark_results_{timestamp}.csv")

    # Create an empty DataFrame with the correct columns based on your paper's appendix
    results_df = pd.DataFrame(columns=[
        'prompt_id', 'model', 'model_version', 'date_time', 'latency_ms',
        'tokens_in', 'tokens_out', 'cost_usd', 'response_text', 'error_message'
    ])
    results_df.to_csv(output_filename, index=False) # Write header
    print(f"Logging results to {output_filename}")

    # --- 4. MAIN BENCHMARKING LOOP ---
    for model_name, adapter_function in models_to_run.items():
        print(f"\n--- Testing Model: {model_name} ---")
        for prompt_data in test_prompts:
            prompt_id = prompt_data['id']
            prompt_text = prompt_data['prompt_text']
            
            # Add teacher_context to the prompt if it exists
            if prompt_data.get('teacher_context'):
                full_prompt = f"Context: {prompt_data['teacher_context']}\n\n{prompt_text}"
            else:
                full_prompt = prompt_text

            print(f"  -> Running prompt: {prompt_id}...")

            try:
                # Call the correct adapter function
                # The adapter is responsible for handling API keys and the actual call
                response_dict = adapter_function(
                    model_name=model_name,
                    prompt_text=full_prompt,
                    system_prompt=system_prompt_text
                )
            except Exception as e:
                print(f"    ERROR: An exception occurred while calling the API: {e}")
                # Log the error but continue with the next prompt/model
                response_dict = {
                    'model_version': 'N/A', 'latency_ms': 0, 'tokens_in': 0,
                    'tokens_out': 0, 'cost_usd': 0.0, 'response_text': '',
                    'error_message': str(e)
                }

            # Prepare the data for logging
            log_entry = {
                'prompt_id': prompt_id,
                'model': model_name,
                'date_time': datetime.now().isoformat(),
                **response_dict  # Unpack the dictionary from the adapter
            }

            # Append the new result to the CSV file
            pd.DataFrame([log_entry]).to_csv(output_filename, mode='a', header=False, index=False)
            time.sleep(1) # Add a small delay to avoid hitting rate limits

    print(f"\n✅ Benchmark run complete. Results saved to {output_filename}")


if __name__ == "__main__":
    # --- 5. ARGUMENT PARSING for flexibility ---
    parser = argparse.ArgumentParser(description="Run the LLM Benchmarking Harness.")
    parser.add_argument(
        "--model",
        type=str,
        help="Run the benchmark for a single specified model.",
        choices=["gpt-4o-mini", "claude-3-sonnet-20240229", "gemini-1.5-flash-latest", "command-r", "meta-llama-3-8b-instruct"]
    )
    parser.add_argument(
        "--system_prompt",
        type=str,
        default="strict_socratic",
        help="Specify which system prompt to use for the run.",
        choices=["strict_socratic", "neutral_instruction", "hybrid_conversational"]
    )
    
    # Setup environment once
    setup_environment()
    
    # Parse arguments and run main function
    args = parser.parse_args()
    main(args)
