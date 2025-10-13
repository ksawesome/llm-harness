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
- **Dynamic Model Loading**: Load model configurations from JSON file for easy customization
- **Model Categories**: Group models by categories (e.g., "fast", "accurate") for selective benchmarking
- **Configuration Validation**: Automatic validation of adapter functions and model configurations
- **Prompt Schema Validation**: JSON schema validation for prompt files to catch malformed data
- **Jinja2 Templating**: Support for dynamic prompt generation with template variables
- **HELM Integration**: Option to include HELM-style prompts for broader evaluation coverage
- **Automated Report Generation**: Create professional PDF/HTML reports with visualizations and insights
- **LLM-as-Judge Evaluation**: AI-powered response quality assessment using advanced language models
- **Comparative Analysis**: Statistical model comparisons with automated insights and recommendations
- **Data Management**: Automated cleanup and archiving of old results with compression
- **Database Storage**: SQLite-based persistent storage for efficient querying and analysis
- **Interactive Dashboard**: Modern web dashboard with real-time charts and model comparisons

The models under evaluation are:

  * OpenAI GPT-4o mini
  * Anthropic Claude 3 Sonnet
  * Google Gemini 2.5 Flash
  * Cohere Command R 08-2024
  * Meta Llama 4 Maverick 17B 128E Instruct (via Hugging Face)

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
|   |-- generate_visualizations.ipynb  # Jupyter notebook for charts and plots
|   |-- statistical_test.py            # Statistical analysis and significance tests
|   |-- generate_report.py             # Automated PDF/HTML report generation
|   |-- llm_judge_evaluation.py        # AI-powered response quality evaluation
|   |-- comparative_analysis.py        # Statistical model comparison and insights
|-- data/                 # Benchmark input data
|   |-- test_prompts.json     # Test prompts for evaluation
|   |-- system_prompts.json   # System prompt configurations
|-- logs/                 # Application logs
|-- results/              # Output directory
|   |-- raw_output/           # CSV benchmark results
|-- web/                  # Web interface and templates
|   |-- templates/            # Flask web UI templates
|   |   |-- dashboard.html         # Main dashboard page
|   |   |-- index.html            # Results dashboard
|   |   |-- results.html          # Detailed results viewer
|   |   |-- run_details.html      # Run details page
|   |-- dashboard.py          # Interactive web dashboard with charts
|   |-- web_ui.py             # Modern Flask web interface
|-- tests/                # Comprehensive test suite
|   |-- __init__.py
|   |-- test_main.py          # Core functionality tests
|   |-- test_models_config.py # Configuration tests
|   |-- test_openai_adapter.py # API adapter tests
|-- utils/                # Shared utility functions
|   |-- __init__.py
|   |-- check_models.py       # Model availability checker
|-- .github/              # GitHub Actions CI/CD
|   |-- workflows/
|       |-- ci.yml            # Automated testing pipeline
|-- .env                  # API keys (not version controlled)
|-- .env.example          # Environment template
|-- .gitignore            # Git ignore rules
|-- .pre-commit-config.yaml # Code quality hooks
|-- database.py           # SQLite database manager for results
|-- main.py               # Main benchmarking script
|-- manage_results.py     # Data cleanup and archiving utility
|-- models.json           # Model configurations (JSON format)
|-- pyproject.toml        # Project configuration
|-- requirements.txt      # Dependencies
|-- README.md             # This documentation
```

## ⚙️ Model Configuration

Models are configured in `models.json` for easy customization without code changes. Each model entry includes:

- `name`: Model identifier
- `adapter`: Python import path to the adapter function
- `rate_limit_seconds`: Minimum seconds between API calls
- `timeout_seconds`: API call timeout
- `temperature`: Sampling temperature (optional)
- `category`: Model category for grouping (e.g., "fast", "accurate")

Example configuration:

```json
{
  "gpt-4o-mini": {
    "name": "gpt-4o-mini",
    "adapter": "adapters.call_openai_api",
    "rate_limit_seconds": 10.0,
    "timeout_seconds": 30,
    "temperature": 0.3,
    "category": "fast"
  }
}
```

The system automatically validates all configurations on startup, ensuring adapters are importable and models are properly configured.

## 📝 Prompt System

The harness uses a robust prompt system with validation and templating capabilities.

### Prompt Files

- `data/test_prompts.json`: Test prompts with categories, expected keywords, and teacher context
- `data/system_prompts.json`: System prompt templates for different tutoring styles

### Features

- **Schema Validation**: Automatic validation of prompt file structure using JSON Schema
- **Jinja2 Templating**: Dynamic prompt generation with variables
- **HELM Integration**: Optional inclusion of HELM-style prompts for comprehensive evaluation
- **Category Filtering**: Prompts organized by categories for targeted testing

### Template Variables

Use `--template-vars` to provide variables for prompt templating:

```bash
python main.py --template-vars '{"vehicle_type": "car", "mass": "1200", "initial_speed": "0", "final_speed": "10", "time": "5"}'
```

Example template prompt:
```json
{
  "prompt_text": "Student: \"I need to calculate the power for a {{vehicle_type}} that weighs {{mass}}kg...\""
}
```

### HELM Prompts

Include HELM-style prompts for broader evaluation:

```bash
python main.py --include-helm
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

This installs the package in editable mode with development dependencies (for testing and linting). All dependencies are pinned to specific versions to ensure reproducible builds and avoid breaking changes.

For visualization features, install optional dependencies:
```bash
pip install -e .[viz]
```

### 4\. Docker Setup (Optional)

For containerized deployment, use the provided Dockerfile:

```bash
# Build the Docker image
docker build -t llm-harness .

# Run the container
docker run -p 5000:5000 --env-file .env llm-harness python web/dashboard.py
```

### 5\. Development Setup (Optional)

For contributors, set up pre-commit hooks and run tests:

```bash
pre-commit install
pytest
```

### 6\. API Documentation (Optional)

Generate API documentation using Sphinx:

```bash
pip install -e .[dev]  # Includes Sphinx
cd docs
sphinx-build -b html . _build/html
# Open _build/html/index.html in browser
```

### 7\. Environment Variables

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

### Run Models by Category

Use the `--category` flag to run only models in a specific category (e.g., "fast" or "accurate").

```bash
python main.py --category fast
```

You can combine flags:

```bash
python main.py --model gemini-2.5-flash --system_prompt neutral_instruction --prompt-range 3
```

### Web UI (Optional)

For a simple web interface to view results, run:

```bash
python web/web_ui.py
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

After collecting benchmark data, use the comprehensive analysis toolkit:

#### Automated Report Generation
Generate professional PDF and HTML reports with visualizations and insights:

```bash
# Generate both PDF and HTML reports
python analysis/generate_report.py results/raw_output/benchmark_results.csv

# Generate only HTML report
python analysis/generate_report.py results/raw_output/benchmark_results.csv --type html

# Generate only PDF report
python analysis/generate_report.py results/raw_output/benchmark_results.csv --type pdf
```

**Features:**
- Executive summary with key metrics
- Model performance comparison tables
- Interactive visualizations (latency distributions, cost analysis, success rates)
- Automated recommendations for best models
- Professional formatting for sharing and presentations

#### LLM-as-Judge Evaluation
Use advanced AI evaluation to score model responses on multiple criteria:

```bash
# Evaluate responses using GPT-4 as judge
python analysis/llm_judge_evaluation.py results/raw_output/benchmark_results.csv

# Use custom judge model and columns
python analysis/llm_judge_evaluation.py results/raw_output/benchmark_results.csv \
    --judge-model gpt-4 \
    --prompt-column prompt \
    --response-column response_text \
    --model-column model
```

**Evaluation Criteria:**
- Relevance: How well the response addresses the prompt
- Accuracy: Factual correctness and truthfulness
- Completeness: Thoroughness of the response
- Clarity: Clear and understandable language
- Helpfulness: Practical value to the user

**Output:** JSON file with detailed scores, reasoning, and statistical summaries.

#### Comparative Analysis
Perform statistical comparisons between models with automated insights:

```bash
# Generate comprehensive comparative analysis
python analysis/comparative_analysis.py results/raw_output/benchmark_results.csv

# Specify custom output location
python analysis/comparative_analysis.py results/raw_output/benchmark_results.csv \
    --output-file my_comparison.json
```

**Analysis Includes:**
- Performance comparison matrix
- Statistical significance testing (ANOVA, t-tests)
- Automated insights and recommendations
- Radar charts for multi-dimensional comparison
- Cost-benefit analysis

#### Data Management and Storage
Manage benchmark results with automated cleanup and persistent storage:

**Results Cleanup and Archiving:**
```bash
# Archive results older than 30 days
python manage_results.py archive --days 30

# Compress archived files
python manage_results.py compress

# Clean up temporary files
python manage_results.py cleanup
```

**Database Storage:**
The system now uses SQLite for persistent storage of benchmark results, enabling:
- Efficient querying of historical data
- Fast aggregation and analysis
- Data integrity and consistency
- Concurrent access support

**Interactive Web Dashboard:**
Launch the modern visualization dashboard for real-time analysis:

```bash
# Start the dashboard server
python web/dashboard.py

# Access at http://localhost:5000
```

**Dashboard Features:**
- Real-time model performance metrics
- Interactive charts (latency, cost, success rates)
- Run comparison and historical analysis
- Responsive design for desktop and mobile
- API endpoints for programmatic access

#### Legacy Analysis Tools
- **`analysis/statistical_test.py`**: Statistical analysis including Cohen's Kappa and Wilcoxon tests
- **`analysis/generate_visualizations.ipynb`**: Jupyter notebook for radar charts, scatterplots, and CDF plots

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

### v0.1.2 Data Management & Visualization
- ✅ **Results Management**: Automated cleanup and archiving of old CSV results with compression
- ✅ **Database Storage**: SQLite-based persistent storage for efficient querying and analysis
- ✅ **Interactive Dashboard**: Modern Flask-based web dashboard with real-time charts and comparisons
- ✅ **Data Integrity**: Robust error handling and data validation for database operations
- ✅ **API Endpoints**: RESTful APIs for programmatic access to benchmark data
- ✅ **Visualization**: Plotly-powered interactive charts for latency, cost, and success rate analysis

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

## 🔧 Troubleshooting

### Common Issues

#### API Key Errors
- **Error**: `AuthenticationError: Invalid API key`
- **Solution**: Check your `.env` file and ensure API keys are correctly set for the models you're using.

#### Model Deprecation Warnings
- **Error**: `Warning: Model 'xyz' is not in the list of supported models`
- **Solution**: Update `models.json` with current model names. Check provider documentation for latest model IDs.

#### Import Errors
- **Error**: `ModuleNotFoundError: No module named 'xyz'`
- **Solution**: Install missing dependencies: `pip install -e .[dev]`

#### Rate Limiting
- **Error**: `RateLimitError: Too many requests`
- **Solution**: Increase `rate_limit_seconds` in `models.json` or reduce concurrent requests.

#### Memory Issues
- **Error**: `MemoryError` or slow performance
- **Solution**: Reduce batch size or run fewer models simultaneously.

#### Docker Issues
- **Error**: Container fails to start
- **Solution**: Ensure `.env` file is mounted: `docker run --env-file .env ...`

### Getting Help

If you encounter issues not covered here:
1. Check the logs in the `logs/` directory
2. Run with `--dry-run` to test configuration
3. Open an issue on GitHub with error details

-----

## 📄 License

This project is part of the Mettle research initiative. See individual files for licensing details.

---

**Last Updated**: October 13, 2025
