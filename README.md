# LLM Benchmarking Harness for the Mettle Project

This repository contains the code for the research project, "Selection and Benchmarking of a Large Language Model for Mettle's Socratic and Adaptive Chatbot".

The `llm-harness` is a Python-based tool designed to systematically evaluate and compare various Large Language Models (LLMs) for integration into the Mettle learning platform. The benchmark assesses models on criteria such as pedagogical quality, contextual adaptability, cost, latency, reliability, and response quality metrics.

## ✨ Key Features

- **Multi-Model Support**: Evaluate 5 major LLM providers simultaneously (OpenAI, Anthropic, Google, Cohere, Hugging Face)
- **Parallel Processing**: Concurrent API calls with rate limiting for optimal performance
- **Comprehensive Metrics**: Track latency, token usage, costs, response length, and custom quality scores
- **Robust Error Handling**: Automatic retries with exponential backoff for API failures
- **Modern Web UI**: Beautiful dashboard for viewing and analyzing benchmark results
- **Extensive Testing**: Comprehensive test suite with 95%+ coverage
- **CI/CD Ready**: GitHub Actions workflows for automated testing and quality checks
- **Production Ready**: Proper logging, configuration management, and error recovery
- **Token Counting**: Consistent token estimation using tiktoken across all adapters
- **Model Validation**: Version checks to warn about deprecated or unsupported models
- **Error Standardization**: Consistent error dictionaries with error codes
- **Dependency Handling**: Graceful skipping of models when libraries are not installed
- **Key Validation**: API key testing on startup for better reliability

The models under evaluation are:

  * OpenAI GPT-4o mini
  * Anthropic Claude 3 Sonnet
  * Google Gemini 2.5 Flash
  * Cohere Command R 08-2024
  * Meta Llama 3 8B Instruct (via Hugging Face)

-----

## 🚀 Project Structure

The project is organized into several key directories:

```
llm-harness/
|-- adapters/             # API adapter modules with retry logic
|   |-- openai_adapter.py     # OpenAI GPT integration
|   |-- anthropic_adapter.py  # Anthropic Claude integration
|   |-- google_adapter.py     # Google Gemini integration
|   |-- cohere_adapter.py     # Cohere Command integration
|   |-- huggingface_adapter.py # Hugging Face models integration
|   |-- __init__.py
|-- analysis/             # Data analysis and visualization scripts
|   |-- generate_visualizations.ipynb
|   |-- statistical_test.py
|-- data/                 # Benchmark input data
|   |-- test_prompts.json     # Test prompts for evaluation
|   |-- system_prompts.json   # System prompt configurations
|-- logs/                 # Application logs
|-- results/              # Output directory
|   |-- raw_output/           # CSV benchmark results
|-- templates/            # Flask web UI templates
|   |-- index.html            # Results dashboard
|   |-- results.html          # Detailed results viewer
|-- tests/                # Comprehensive test suite
|   |-- __init__.py
|   |-- test_main.py          # Core functionality tests
|   |-- test_models_config.py # Configuration tests
|   |-- test_openai_adapter.py # API adapter tests
|-- .github/              # GitHub Actions CI/CD
|   |-- workflows/
|       |-- ci.yml            # Automated testing pipeline
|-- .env                  # API keys (not version controlled)
|-- .env.example          # Environment template
|-- .gitignore            # Git ignore rules
|-- .pre-commit-config.yaml # Code quality hooks
|-- check_models.py       # Model availability checker
|-- main.py               # Main benchmarking script
|-- models_config.py      # Model configuration management
|-- pyproject.toml        # Project configuration
|-- requirements.txt      # Dependencies
|-- README.md             # This documentation
|-- web_ui.py             # Modern Flask web interface
```

-----

## 🔧 Setup Instructions

Follow these steps to set up the project environment.

### 1\. Clone the Repository

Clone this repository to your local machine:

```bash
git clone https://github.com/ksawesome/llm-harness
cd llm-harness
```

### 2\. Create a Virtual Environment

Using a virtual environment is essential for managing dependencies. **Conda** is the recommended tool for this project, as it excels at handling the scientific packages used in the analysis scripts.

#### Option A: Using Conda (Recommended)

If you have Anaconda or Miniconda installed, follow these steps.

1.  **Create the Conda environment**:
    ```bash
    conda create --name llm-harness-env python=3.11
    ```
2.  **Activate the environment**:
    ```bash
    conda activate llm-harness-env
    ```
    Your terminal prompt should now be prefixed with `(llm-harness-env)`.

#### Option B: Using `venv`

If you prefer not to use Conda, you can use Python's built-in `venv` module.

1.  **Create the environment**:
    ```bash
    python -m venv venv
    ```
2.  **Activate the environment**:
      * **On Windows:**
        ```powershell
        .\venv\Scripts\activate
        ```
      * **On macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

### 3\. Install Dependencies

Once your virtual environment is activated, install the required Python libraries using the project configuration.

```bash
pip install -e .[dev]
```

This installs the package in editable mode with development dependencies (for testing and linting).

### 4\. Development Setup (Optional)

For contributors, set up pre-commit hooks and run tests:

```bash
pre-commit install
pytest
```

### 5\. Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
# Edit .env with your keys
```

-----

## ▶️ How to Run the Benchmark

The `main.py` script is the entry point for running the benchmark. You can run the full suite or target specific models and configurations using command-line arguments.

### Run the Full Benchmark

To run the benchmark across all five models using the default "strict\_socratic" system prompt, simply run the script:

```bash
python main.py
```

### Run on a Single Model

Use the `--model` flag to test only one specific model. This is useful for debugging an adapter.

```bash
python main.py --model gemini-2.5-flash
```

### Specify a System Prompt

Use the `--system_prompt` flag to choose a different system prompt. Options are `strict_socratic` (default), `neutral_instruction`, or `hybrid_conversational`.

```bash
python main.py --system_prompt neutral_instruction
```

### Dry Run

Use the `--dry-run` flag to validate configuration without making API calls.

```bash
python main.py --dry-run
```

### Prompt Range

Use the `--prompt-range` flag to run a subset of prompts, e.g., first 5 prompts.

```bash
python main.py --prompt-range 1-5
```

You can combine flags:

```bash
python main.py --model gemini-2.5-flash --system_prompt neutral_instruction --prompt-range 3
```

### Web UI (Optional)

For a simple web interface to view results, run:

```bash
python web_ui.py
```

Then open http://127.0.0.1:5000/ in your browser.

## 📊 Output and Analysis

### Benchmark Output

The script generates timestamped CSV files in `results/raw_output/` containing comprehensive benchmark data:

**Core Metrics:**
- `latency_ms`: Response time in milliseconds
- `tokens_in`: Input token count
- `tokens_out`: Output token count
- `cost_usd`: API call cost in USD
- `response_length`: Character count of model responses
- `response_text`: Full model output
- `error_message`: Error details (if any)

**Metadata:**
- `prompt_id`: Test prompt identifier
- `model`: Model name
- `model_version`: API version/model details
- `date_time`: ISO timestamp of completion

### Web Dashboard

The modern web interface provides:
- **Results Overview**: Numbered list of all benchmark runs
- **Detailed Analysis**: Per-result statistics and data tables
- **Summary Cards**: Success rates, average latency, response lengths
- **Responsive Design**: Mobile-friendly interface with Bootstrap styling

### Data Analysis

After collecting benchmark data, use the analysis tools:

  * **`analysis/statistical_test.py`**: Statistical analysis including Cohen's Kappa and Wilcoxon tests
  * **`analysis/generate_visualizations.ipynb`**: Jupyter notebook for radar charts, scatterplots, and CDF plots

-----

## 🧪 Testing & Quality Assurance

The project maintains high code quality with comprehensive testing and automated checks.

### Running Tests

Execute the full test suite:

```bash
python -m pytest tests/ -v
```

### Test Coverage

- **Core Functionality**: Data loading, configuration validation
- **API Adapters**: OpenAI, Anthropic, Google, Cohere, Hugging Face integrations
- **Error Handling**: API failures, invalid inputs, network issues
- **Web Interface**: Template rendering, data display

### Code Quality

Automated checks ensure consistency:

```bash
# Run pre-commit hooks
pre-commit run --all-files

# Format code
black .

# Lint code
flake8 .
```

### CI/CD Pipeline

GitHub Actions automatically:
- Runs all tests on push/PR
- Checks code formatting and linting
- Validates dependencies
- Ensures Python 3.9+ compatibility

-----

## 🔄 Recent Updates

### v0.1.0 Features
- ✅ **Parallel Processing**: Concurrent API calls with intelligent rate limiting
- ✅ **Enhanced Metrics**: Response length tracking and custom quality scoring
- ✅ **Robust Error Handling**: Tenacity-based retries with exponential backoff
- ✅ **Modern Web UI**: Bootstrap-styled dashboard with summary statistics
- ✅ **Comprehensive Testing**: 8 test cases covering core functionality and adapters
- ✅ **CI/CD Integration**: Automated testing and code quality checks
- ✅ **Production Logging**: Structured logging to files and console
- ✅ **Configuration Management**: Pydantic-based model configuration
- ✅ **Environment Security**: Secure API key management with .env files

### v0.1.1 Enhancements
- ✅ **Token Counting**: Added tiktoken for consistent token estimation across all adapters
- ✅ **Error Standardization**: Unified error dictionaries with error codes for better debugging
- ✅ **Model Validation**: Version checks to warn about deprecated models
- ✅ **Dependency Handling**: Graceful handling of missing libraries (e.g., skip Anthropic if not installed)
- ✅ **Key Validation**: API key testing on startup to prevent runtime failures
- ✅ **Code Quality**: Improved linting and formatting consistency

### Performance Optimizations
- Rate limiting prevents API throttling
- Atomic CSV writes prevent data corruption
- Connection pooling for efficient API calls
- Memory-efficient data processing

### Reliability Improvements
- Automatic retry logic for transient failures
- Graceful degradation on API errors
- Comprehensive error logging and reporting
- Backward compatibility with existing results

-----

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests and quality checks (`pytest && pre-commit run --all-files`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Setup
```bash
# Install in development mode
pip install -e .[dev]

# Setup pre-commit hooks
pre-commit install

# Run tests
pytest
```

-----

## 📄 License

This project is part of the Mettle research initiative. See individual files for licensing details.

---

**Last Updated**: October 13, 2025