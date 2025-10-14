# LLM Benchmarking Harness for the Mettle Project# LLM Benchmarking Harness for the Mettle Project



## 1. Project OverviewThis repository contains the code for the research project, "Selection and Benchmarking of a Large Language Model for Mettle's Socratic and Adaptive Chatbot".



The LLM Benchmarking Harness is a Python toolkit used to evaluate, compare, and productionize large language models (LLMs) for Mettle's adaptive Socratic tutoring experiences. It orchestrates multi-provider benchmarks, captures detailed telemetry, generates executive-ready reports, and serves a web dashboard for exploring historical runs. The harness is designed for reliability in research environments where API quotas, network conditions, and model availability fluctuate daily.

*For detailed architectural information and operational workflows, see the technical handbook in `docs/technical-handbook.md`.*

The `llm-harness` is a Python-based tool designed to systematically evaluate and compare various Large Language Models (LLMs) for integration into the Mettle learning platform. The benchmark assesses models on criteria such as pedagogical quality, contextual adaptability, cost, latency, reliability, and response quality metrics.



The benchmark currently targets five providers (OpenAI, Anthropic, Google, Cohere, and Hugging Face) but is extensible to new adapters. All components are tested, configurable, and ready to embed in CI pipelines.## ✨ Key Features



## 2. Feature Summary- **Multi-Model Support**: Evaluate 5 major LLM providers simultaneously (OpenAI, Anthropic, Google, Cohere, Hugging Face)

- **Parallel Processing**: Concurrent API calls with rate limiting for optimal performance

### 2.1 Benchmark Orchestration- **Comprehensive Metrics**: Track latency, token usage, costs, response length, and custom quality scores

- Parallelizes API calls while respecting provider rate limits.- **Robust Error Handling**: Automatic retries with exponential backoff for API failures

- Captures latency, token counts, cost estimates, response lengths, and raw outputs.- **Synthetic Data Fallback**: Automatic API failure handling with deterministic synthetic responses

- Supports targeted execution by model, prompt category, system prompt, or prompt range.- **Modern Web UI**: Beautiful dashboard for viewing and analyzing benchmark results

- **Extensive Testing**: Comprehensive test suite with 95%+ coverage and synthetic data validation

### 2.2 Resilience and Fallbacks- **CI/CD Ready**: GitHub Actions workflows for automated testing and quality checks

- Retries transient failures with exponential backoff.- **Production Ready**: Proper logging, configuration management, and error recovery

- Falls back to deterministic synthetic responses when a provider is unavailable; results are tagged via the `api_failed` column for auditability.- **Token Counting**: Consistent token estimation using tiktoken across all adapters

- Provides mock providers for offline testing and consistent regression scenarios.- **Model Validation**: Version checks to warn about deprecated or unsupported models

- **Error Standardization**: Consistent error dictionaries with error codes

### 2.3 Analysis and Reporting- **Dependency Handling**: Graceful skipping of models when libraries are not installed

- Generates PDF and HTML reports with visualizations, summary tables, and qualitative exemplars.- **Key Validation**: API key testing on startup for better reliability

- Exports all plots as PNG for slide decks and documentation.- **API Resilience**: Intelligent fallback from live APIs to synthetic data on failures

- Runs comparative statistical analyses and radar charts for multi-metric evaluation.- **Dynamic Model Loading**: Load model configurations from JSON file for easy customization

- Offers an LLM-as-judge workflow to grade responses using models such as GPT-4.- **Model Categories**: Group models by categories (e.g., "fast", "accurate") for selective benchmarking

- **Configuration Validation**: Automatic validation of adapter functions and model configurations

### 2.4 Data Management and Persistence- **Prompt Schema Validation**: JSON schema validation for prompt files to catch malformed data

- Normalizes outputs into timestamped CSVs under `results/raw_output/`.- **Jinja2 Templating**: Support for dynamic prompt generation with template variables

- Loads, joins, and deduplicates results with `utils.result_loader`.- **HELM Integration**: Option to include HELM-style prompts for broader evaluation coverage

- Persists runs into SQLite for fast querying and aggregation.- **Automated Report Generation**: Create professional PDF/HTML reports with visualizations and insights

- Includes utilities to archive, compress, and clean older datasets.- **Image Export**: Automatic PNG export of all generated plots and charts

- **LLM-as-Judge Evaluation**: AI-powered response quality assessment using advanced language models

### 2.5 Developer Experience- **Comparative Analysis**: Statistical model comparisons with automated insights and recommendations

- Comprehensive pytest suite covering adapters, configuration validation, web routes, and synthetic fallbacks.- **Data Management**: Automated cleanup and archiving of old results with compression

- Pre-commit stack (black, isort, flake8, pyupgrade, whitespace fixers) aligned with CI.- **Database Storage**: SQLite-based persistent storage for efficient querying and analysis

- Sphinx documentation under `docs/` for module-level references.- **Interactive Dashboard**: Modern web dashboard with real-time charts and model comparisons

- Dockerfile for containerized deployment of the web dashboard and APIs.

The models under evaluation are:

## 3. Repository Layout

  * OpenAI GPT-4o mini

```  * Anthropic Claude 3 Sonnet

llm-harness/  * Google Gemini 2.5 Flash

├── adapters/                 # Provider adapters and mock integrations  * Cohere Command R 08-2024

├── analysis/                 # Reporting, comparative analytics, judge tooling  * Meta Llama 4 Maverick 17B 128E Instruct (via Hugging Face)

├── data/                     # Prompt catalogs and schemas

├── docs/                     # Sphinx documentation sources-----

├── logs/                     # Runtime log output

├── results/                  # CSV results, synthetic responses, reports## 🚀 Project Structure

├── templates/                # HTML templates consumed by the web UI

├── tests/                    # Pytest suite and support fixturesThe project is organized into several key directories:

├── utils/                    # Shared utilities (mock provider, result loader, etc.)

├── web/                      # Flask applications (`web_ui.py`, `dashboard.py`)```

├── .github/workflows/        # CI configurationllm-harness/

├── .gitignore                # Root ignore rules|-- adapters/             # API adapter modules with retry logic

├── templates/.gitignore      # Template-specific ignore rules|   |-- openai_adapter.py     # OpenAI GPT integration

├── Dockerfile|   |-- anthropic_adapter.py  # Anthropic Claude integration

├── README.md|   |-- google_adapter.py     # Google Gemini integration

├── check_models.py|   |-- cohere_adapter.py     # Cohere Command integration

├── database.py|   |-- huggingface_adapter.py # Hugging Face models integration

├── environment.yml|   |-- __init__.py

├── main.py|-- analysis/             # Data analysis and visualization scripts

├── manage_results.py|   |-- generate_visualizations.ipynb  # Jupyter notebook for charts and plots

├── models.json|   |-- statistical_test.py            # Statistical analysis and significance tests

├── models_config.py|   |-- generate_report.py             # Automated PDF/HTML report generation

├── prompt_utils.py|   |-- llm_judge_evaluation.py        # AI-powered response quality evaluation

├── pyproject.toml|   |-- comparative_analysis.py        # Statistical model comparison and insights

├── requirements.txt|-- data/                 # Benchmark input data

└── web/.gitignore            # Web asset ignore rules|   |-- test_prompts.json     # Test prompts for evaluation

```|   |-- system_prompts.json   # System prompt configurations

|-- logs/                 # Application logs

## 4. Model Configuration|-- results/              # Output directory

|   |-- raw_output/           # CSV benchmark results

Models are declared in `models.json` and validated by `models_config.py`. Each entry controls the adapter binding, throttling, and metadata.

*For advanced configuration options and adapter development details, see the technical handbook in `docs/technical-handbook.md`.*

|-- web/                  # Web interface and templates

|   |-- templates/            # Flask web UI templates

### 4.1 Structure|   |   |-- dashboard.html         # Main dashboard page

|   |   |-- index.html            # Results dashboard

```json|   |   |-- results.html          # Detailed results viewer

{|   |   |-- run_details.html      # Run details page

  "gpt-4o-mini": {|   |-- dashboard.py          # Interactive web dashboard with charts

    "name": "gpt-4o-mini",|   |-- web_ui.py             # Modern Flask web interface

    "adapter": "adapters.call_openai_api",|-- tests/                # Comprehensive test suite

    "rate_limit_seconds": 10.0,|   |-- __init__.py

    "timeout_seconds": 30,|   |-- test_main.py          # Core functionality tests

    "temperature": 0.3,|   |-- test_models_config.py # Configuration tests

    "category": "fast"|   |-- test_openai_adapter.py # API adapter tests

  }|-- utils/                # Shared utility functions

}|   |-- __init__.py

```|   |-- check_models.py       # Model availability checker

|-- .github/              # GitHub Actions CI/CD

### 4.2 Update Procedure|   |-- workflows/

1. Open `models.json` and add or edit the desired entry.|       |-- ci.yml            # Automated testing pipeline

2. Ensure the `adapter` points to a callable in `adapters/` (e.g., `adapters.call_google_api`).|-- .env                  # API keys (not version controlled)

3. Adjust throttling parameters (`rate_limit_seconds`, `timeout_seconds`) based on provider guidance.|-- .env.example          # Environment template

4. Optionally set `temperature` or custom metadata used by your evaluation scripts.|-- .gitignore            # Git ignore rules

5. Run `python -m pytest tests/test_models_config.py` to verify schema conformity and adapter importability.|-- .pre-commit-config.yaml # Code quality hooks

6. Execute any targeted benchmark with `python main.py --model <model-key>` to confirm the change end-to-end.|-- database.py           # SQLite database manager for results

|-- main.py               # Main benchmarking script

## 5. Prompt System|-- manage_results.py     # Data cleanup and archiving utility

|-- models.json           # Model configurations (JSON format)

### 5.1 Prompt Catalogs|-- pyproject.toml        # Project configuration

- `data/test_prompts.json`: Primary prompt set with categories, expected keywords, and context for grading.|-- requirements.txt      # Dependencies

- `data/system_prompts.json`: System directives used to shape tutor personas (e.g., Socratic vs. neutral styles).|-- README.md             # This documentation

```

Both files are validated against JSON Schema (`prompt_utils.validate_json_data`) to catch structural issues before execution.

*For detailed information about prompt engineering, HELM integration, and template expansion, see the technical handbook in `docs/technical-handbook.md`.*

## ⚙️ Model Configuration

### 5.2 Template Expansion

- Prompts can include Jinja2 placeholders such as `{{ vehicle_type }}`.Models are configured in `models.json` for easy customization without code changes. Each model entry includes:

- Supply variables with `python main.py --template-vars '{"vehicle_type": "car"}'`.

- The pipeline expands prompts via `expand_prompts_with_templates`, producing one benchmark row per rendered combination.- `name`: Model identifier

- `adapter`: Python import path to the adapter function

### 5.3 HELM Integration- `rate_limit_seconds`: Minimum seconds between API calls

HELM (Holistic Evaluation of Language Models) introduces scenario-driven prompts that stress reasoning, safety, and robustness. Enable HELM augmentation with `python main.py --include-helm`. The harness will merge predefined HELM prompts with your catalog, allowing:- `timeout_seconds`: API call timeout

- Regression tests against safety-critical cases without calling live providers.- `temperature`: Sampling temperature (optional)

- Synthetic fallback generation for edge cases.- `category`: Model category for grouping (e.g., "fast", "accurate")

- Focused evaluation of categories such as “helpfulness”, “groundedness”, or “adversarial resilience”.

Example configuration:

### 5.4 Recommended Use Cases

- Target categories via `--category <name>` when analyzing specialized skills (e.g., “physics-word-problems”).```json

- Use `--prompt-range start-end` to quickly smoke-test adapters after configuration changes.{

- Combine HELM and templated prompts to simulate classroom variations and regulatory scenarios.  "gpt-4o-mini": {

    "name": "gpt-4o-mini",

## 6. Environment Setup    "adapter": "adapters.call_openai_api",

    "rate_limit_seconds": 10.0,

### 6.1 Clone and Navigate    "timeout_seconds": 30,

```    "temperature": 0.3,

git clone https://github.com/ksawesome/llm-harness    "category": "fast"

cd llm-harness  }

```}

```

### 6.2 Choose a Python Environment

The system automatically validates all configurations on startup, ensuring adapters are importable and models are properly configured.

**Option A – Conda (recommended)**

```## 📝 Prompt System

conda create --name llm-harness-env python=3.11

conda activate llm-harness-envThe harness uses a robust prompt system with validation and templating capabilities.

```

### Prompt Files

**Option B – venv**

```- `data/test_prompts.json`: Test prompts with categories, expected keywords, and teacher context

python -m venv .venv- `data/system_prompts.json`: System prompt templates for different tutoring styles

# Windows

.\.venv\Scripts\activate### Features

# macOS/Linux

source .venv/bin/activate- **Schema Validation**: Automatic validation of prompt file structure using JSON Schema

```- **Jinja2 Templating**: Dynamic prompt generation with variables

- **HELM Integration**: Optional inclusion of HELM-style prompts for comprehensive evaluation

### 6.3 Install Dependencies- **Category Filtering**: Prompts organized by categories for targeted testing

```

pip install -e .[dev]### Template Variables

# Optional visualization extras

pip install -e .[viz]Use `--template-vars` to provide variables for prompt templating:

```

```bash

### 6.4 Configure Environment Variablespython main.py --template-vars '{"vehicle_type": "car", "mass": "1200", "initial_speed": "0", "final_speed": "10", "time": "5"}'

``````

cp .env.example .env

# Populate provider keys inside .envExample template prompt:

``````json

{

### 6.5 Optional Docker Image  "prompt_text": "Student: \"I need to calculate the power for a {{vehicle_type}} that weighs {{mass}}kg...\""

```}

docker build -t llm-harness .```

docker run -p 5000:5000 --env-file .env llm-harness python web/dashboard.py

```### HELM Prompts



## 7. Running BenchmarksInclude HELM-style prompts for broader evaluation:



### 7.1 Baseline Run```bash

```python main.py --include-helm

python main.py```

```

-----

### 7.2 Targeted Execution

- `--model <key>`: Evaluate a single model (e.g., `python main.py --model gemini-2.5-flash`).## 🔧 Setup Instructions

- `--system_prompt <name>`: Switch tutor voice (`strict_socratic`, `neutral_instruction`, `hybrid_conversational`).

- `--category <name>`: Filter prompts by pedagogical grouping.Follow these steps to set up the project environment.

- `--prompt-range 1-5`: Execute a slice for smoke testing.

- `--dry-run`: Validate configs without issuing API calls.### 1\. Clone the Repository



Combine options as needed, for example:Clone this repository to your local machine:

```

python main.py --model claude-3-sonnet --category reasoning --prompt-range 1-10```bash

```git clone https://github.com/ksawesome/llm-harness

cd llm-harness

## 8. Analysis and Reporting```



### 8.1 Result Files### 2\. Create a Virtual Environment

Each run emits CSV files to `results/raw_output/` with core metrics (`latency_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `response_length`) and metadata (`prompt_id`, `model`, `model_version`, `date_time`, `api_failed`).

Using a virtual environment is essential for managing dependencies. **Conda** is the recommended tool for this project, as it excels at handling the scientific packages used in the analysis scripts.

### 8.2 Automated Reports

```#### Option A: Using Conda (Recommended)

python analysis/generate_report.py results/raw_output/<file>.csv

python analysis/generate_report.py results/raw_output/<file>.csv --type htmlIf you have Anaconda or Miniconda installed, follow these steps.

python analysis/generate_report.py results/raw_output/<file>.csv --type pdf

```1.  **Create the Conda environment**:

Reports include executive summaries, cost breakdowns, latency plots, qualitative excerpts, and recommendations. PNG exports of every chart are stored under `reports/images/`.    ```bash

    conda create --name llm-harness-env python=3.11

### 8.3 LLM-as-Judge Evaluation    ```

```2.  **Activate the environment**:

python analysis/llm_judge_evaluation.py results/raw_output/<file>.csv \    ```bash

    --judge-model gpt-4 \    conda activate llm-harness-env

    --prompt-column prompt \    ```

    --response-column response_text \    Your terminal prompt should now be prefixed with `(llm-harness-env)`.

    --model-column model

```#### Option B: Using `venv`

The evaluator produces JSON records with rubric scores (relevance, accuracy, completeness, clarity, helpfulness), judge reasoning, and aggregated statistics.

If you prefer not to use Conda, you can use Python's built-in `venv` module.

### 8.4 Comparative Analysis

```1.  **Create the environment**:

python analysis/comparative_analysis.py results/raw_output/<file>.csv \    ```bash

    --output-file reports/comparative_<timestamp>.json    python -m venv venv

```    ```

Generates pairwise comparisons, significance tests (ANOVA, Wilcoxon), radar charts, and insight summaries to support model selection committees.2.  **Activate the environment**:

      * **On Windows:**

### 8.5 Data Lifecycle Utilities        ```powershell

```        .\venv\Scripts\activate

python manage_results.py archive --days 30        ```

python manage_results.py compress      * **On macOS/Linux:**

python manage_results.py cleanup        ```bash

```        source venv/bin/activate

These commands archive older runs, compress historical data, and prune temporary artifacts to keep storage manageable.        ```



## 9. Web Interfaces### 3\. Install Dependencies



### 9.1 Core ApplicationsOnce your virtual environment is activated, install the required Python libraries using the project configuration.

- `web/web_ui.py`: Serves the primary dashboard with run summaries, filters, and drill-down pages using Flask and Bootstrap.

- `web/dashboard.py`: Lightweight analytics view suitable for embedding or kiosk displays.```bash

pip install -e .[dev]

### 9.2 Capabilities```

- Run catalogue: Browse benchmark executions with metadata, timestamps, and quick filters.

*For detailed information about web interface architecture, API endpoints, and deployment options, see the technical handbook in `docs/technical-handbook.md`.*

- Detailed views: Inspect per-model KPIs, success rates, and raw responses.

- Visualization panels: Interactive charts for latency distributions, cost trends, and success ratios.

- Synthetic indicators: Clearly labeled badges when a response was generated by the fallback provider.

- REST endpoints (JSON): Provide machine-readable access to aggregated statistics for downstream tooling.```bash

pip install -e .[viz]

### 9.3 Launch```

```

python web/web_ui.py### 4\. Docker Setup (Optional)

# Navigate to http://127.0.0.1:5000/

```For containerized deployment, use the provided Dockerfile:

For containerized deployments, use the Docker command in Section 6.5.

```bash

## 10. Testing and Quality Assurance# Build the Docker image

docker build -t llm-harness .

### 10.1 Test Suite Coverage

- Adapters: `tests/test_openai_adapter.py` and related modules validate adapter signatures, error handling, and mock fallbacks.# Run the container

- Configuration: `tests/test_models_config.py` and `tests/test_imports.py` ensure importability and schema compliance.docker run -p 5000:5000 --env-file .env llm-harness python web/dashboard.py

- Core utilities: `tests/test_main.py`, `tests/test_code_quality.py`, and result loader tests keep orchestration predictable.```

- Web routes: Template rendering and Flask endpoints are smoke tested to prevent regressions.

*For detailed testing procedures, CI/CD pipeline information, and quality assurance best practices, see the technical handbook in `docs/technical-handbook.md`.*
``````bash

For focused debugging, run individual files or tests (e.g., `pytest tests/test_main.py -k synthetic`).pre-commit install

pytest

### 10.3 Pre-Commit Workflow```

```

pre-commit install### 6\. API Documentation (Optional)

pre-commit run --all-files

```Generate API documentation using Sphinx:

Hooks cover formatting (black, isort), linting (flake8), modernization (pyupgrade), merge conflict detection, and newline normalization. Aligning local runs with CI avoids churn during reviews.

```bash

### 10.4 Continuous Integrationpip install -e .[dev]  # Includes Sphinx

GitHub Actions execute the same pytest and pre-commit suites on every push and pull request, ensuring Python 3.11 compatibility and consistent dependency resolution.cd docs

sphinx-build -b html . _build/html

## 11. Performance and Reliability Practices# Open _build/html/index.html in browser

```

- Adaptive rate limiting using `RateLimiter` protects against provider throttling.

- CSV writes are atomic and append-only, preventing partial corruption during abrupt exits.### 7\. Environment Variables

- Structured logging funnels to both console and `logs/` for traceability; log levels can be tuned via environment variables.

- Synthetic fallback retains benchmark continuity during outages while marking rows for downstream filtering.Copy `.env.example` to `.env` and fill in your API keys:

- SQLite storage enables snapshotting, schema migrations, and cross-run comparisons without relying on cloud services.

- Prompt validation and template rendering failures surface early to keep overnight runs from silently skipping prompts.```bash

cp .env.example .env

## 12. Version History# Edit .env with your keys

```

### 12.1 v0.1.0 – Foundational Benchmarking

- Parallelized API calls with initial rate limiting.-----

- Added latency, cost, and response length metrics.

- Introduced Bootstrap-based dashboard and structured logging.## ▶️ How to Run the Benchmark



### 12.2 v0.1.1 – Quality and ValidationThe `main.py` script is the entry point for running the benchmark. You can run the full suite or target specific models and configurations using command-line arguments.

- Integrated tiktoken for uniform token accounting.

- Standardized error payloads and adapter version checks.### Run the Full Benchmark

- Hardened pre-flight key validation and linting consistency.

To run the benchmark across all five models using the default "strict\_socratic" system prompt, simply run the script:

### 12.3 v0.1.2 – Data Management & Visualization

- Implemented archival tooling and CSV compression.```bash

- Added Plotly dashboards for latency/cost trends.python main.py

- Extended database layer for efficient querying.```



### 12.4 v0.1.3 – Robustness & Resilience### Run on a Single Model

- Delivered synthetic fallback for all adapters with clear tagging.

- Expanded automated reports with image exports and qualitative insights.Use the `--model` flag to test only one specific model. This is useful for debugging an adapter.

- Synchronized dependency manifests and refreshed documentation.

```bash

### 12.5 v0.1.4 – Observability & Workflow Enhancementspython main.py --model gemini-2.5-flash

- Introduced module import tests and health checks for Docker deployments.```

- Added Sphinx documentation structure and README overhaul.

- Improved webhook-ready REST responses for integration with analytics pipelines.### Specify a System Prompt



## 13. Troubleshooting and SupportUse the `--system_prompt` flag to choose a different system prompt. Options are `strict_socratic` (default), `neutral_instruction`, or `hybrid_conversational`.



- **Authentication errors**: Verify `.env` values and confirm provider account access.```bash

- **Missing adapters**: Ensure `adapter` paths in `models.json` point to functions exported in `adapters/__init__.py`.python main.py --system_prompt neutral_instruction

- **Rate limit violations**: Increase `rate_limit_seconds` or reduce concurrency.```

- **Memory pressure**: Run smaller prompt batches or offload historic CSVs with `manage_results.py`.

- **Docker start failures**: Supply `--env-file .env` and ensure port 5000 is free.### Dry Run

- **Formatting churn**: Run `pre-commit run --all-files` before committing.

*For comprehensive troubleshooting guides, error code references, and advanced debugging techniques, see the technical handbook in `docs/technical-handbook.md`.*
