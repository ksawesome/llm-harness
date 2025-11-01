# LLM Benchmarking Harness for the Mettle Project

## 1. Project Overview

This repository contains the code for the research project, "Selection and Benchmarking of a Large Language Model for Mettle's Socratic and Adaptive Chatbot".

The LLM Benchmarking Harness is a Python toolkit used to evaluate, compare, and productionize large language models (LLMs) for Mettle's adaptive Socratic tutoring experiences. It orchestrates multi-provider benchmarks, captures detailed telemetry, generates executive-ready reports, and serves a web dashboard for exploring historical runs. The harness is designed for reliability in research environments where API quotas, network conditions, and model availability fluctuate daily.

*For detailed architectural information and operational workflows, see the technical handbook in `docs/technical-handbook.md`.*

The benchmark currently targets five providers (OpenAI, Anthropic, Google, Cohere, and Hugging Face) but is extensible to new adapters. All components are tested, configurable, and ready to embed in CI pipelines.

## 2. Feature Summary

- **Multi-Model Support**: Evaluate multiple LLM providers (OpenAI, Anthropic, Google, Cohere, Hugging Face) in a single, consistent pipeline.
- **Parallel Processing**: Concurrent API calls with per-model rate limiting to maximize throughput while respecting quotas.
- **Comprehensive Metrics**: Track latency, token usage, cost estimates, response length, **scope width**, and custom quality scores.
- **Robust Error Handling**: Automatic retries with exponential backoff and deterministic synthetic fallback on failure.
- **Modern Web UI**: Dashboard with run exploration, KPI panels, and downloadable artifacts.
- **Extensive Testing**: Pytest-based test suite covering adapters, configuration validation, and orchestration logic.
- **Human Trial Support**: 120-prompt bank with Google Form template for scope width evaluation.

### 2.1 Benchmark Orchestration

- Asynchronous execution via `main.py` with semaphore-controlled concurrency.
- Per-model `rate_limit_seconds`, `timeout_seconds`, and `temperature` settings.
- Structured logging and append-only CSV outputs for deterministic reproduction.

### 2.2 Resilience and Fallbacks

- Synthetic fallback responses are tagged (`api_failed = True`) so analyses can filter them.
- Mock providers are available for offline integration and CI smoke tests.
- Standardized error dictionaries and retry policies for consistent observability.

### 2.3 Analysis and Reporting

- PDF/HTML report generation with PNG exports for slides and documentation.
- Comparative analytics including statistical tests and radar charts.
- Optional LLM-as-judge workflow for qualitative scoring using strong judge models.
- **Scope Width Analysis**: Automated assessment of response focus (narrow/appropriate/too broad).

### 2.4 Data Management and Persistence

- Prompt schema validation and Jinja2 templating for dynamic prompt generation.
- CSV outputs stored under `results/raw_output/`; optional persistence to SQLite via `database.py`.
- Utilities for archiving, compressing, and pruning historical results.
- **Extended prompt bank**: 120 prompts across 6 categories with scope width ground truth.

### 2.5 Developer Experience

- Pre-commit hooks (black, isort, flake8, pyupgrade, whitespace fixers) and CI workflows.
- Extras for visualization (`[viz]`) and development (`[dev]`) in `pyproject.toml`.
- Dockerfile for containerized deployments with health checks and non-root runtime.

## 3. Models under Evaluation

- OpenAI GPT-4o mini
- Anthropic Claude 3 Sonnet
- Google Gemini 2.5 Flash
- Cohere Command R (example naming)
- Hugging Face-hosted models (e.g., Meta Llama variants)

## 4. Repository Layout

The repository is organized as follows:

```
llm-harness/
├── adapters/                # Provider adapters and mock integrations
├── analysis/                # Reporting, comparative analytics, judge tooling
├── data/                    # Prompt catalogs and schemas
├── docs/                    # Sphinx documentation and technical handbook
├── logs/                    # Runtime log output
├── results/                 # CSV results, synthetic responses, reports
├── templates/               # HTML templates consumed by the web UI
├── tests/                   # Pytest suite and support fixtures
├── utils/                   # Shared helpers (mock provider, result loader, etc.)
├── web/                     # Flask applications and static assets
├── .github/workflows/       # CI configuration
├── .gitignore               # Root ignore rules
├── Dockerfile               # Production image build
├── README.md                # This documentation
├── docs/technical-handbook.md # In-repo technical handbook
├── main.py                  # Benchmark orchestrator and CLI entry point
├── models.json              # Model registry consumed by models_config.py
├── prompt_utils.py          # Prompt loading, templating, and schema enforcement
├── pyproject.toml           # Build metadata and dependency extras
└── requirements.txt         # Optional pinned requirements for Docker builds
```

## 5. Model Configuration

Models are declared in `models.json` and validated by `models_config.py`. Each entry controls the adapter binding, throttling, and metadata.

*For advanced configuration options and adapter development details, see the technical handbook in `docs/technical-handbook.md`.*

## 6. Prompt System

- Primary prompt catalogs: `data/test_prompts.json` (benchmarks) and `data/system_prompts.json` (system directives/personas).
- Prompts support Jinja2 templating (e.g., `{{ vehicle_type }}`, `{{ student_grade }}`) and are validated against JSON Schema.
- Enable HELM-style prompts with `--include-helm` to broaden robustness and safety testing.

## 7. Environment Setup

1. Clone the repository:

```bash
git clone https://github.com/ksawesome/llm-harness
cd llm-harness
```

2. Create and activate a virtual environment (Conda recommended):

Option A — Conda (recommended):

```bash
conda create --name llm-harness-env python=3.11
conda activate llm-harness-env
```

Option B — venv:

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -e .[dev]
# Optional visualization extras
pip install -e .[viz]
```

4. Copy environment template and populate keys:

```bash
cp .env.example .env
# Edit .env to add provider API keys
```

5. Optional — Docker image (build and run):

```bash
docker build -t llm-harness .
docker run -p 5000:5000 --env-file .env llm-harness python web/dashboard.py
```

## 8. Running Benchmarks

### 8.1 Baseline (all prompts, all configured models)

```bash
python main.py
```

### 8.2 Targeted execution (single model or category)

```bash
python main.py --model gemini-2.5-flash
python main.py --category physics-word-problems
```

### 8.3 Useful flags

- `--system_prompt <name>`: choose system persona (`strict_socratic`, `neutral_instruction`, `hybrid_conversational`)
- `--category <name>`: filter by pedagogical category
- `--prompt-range start-end`: run a slice for smoke testing (e.g., `1-5`)
- `--dry-run`: validate configuration without issuing live API calls
- `--include-helm`: merge HELM prompts into the run

## 9. Analysis and Reporting

- Generate a report from a raw CSV:

```bash
python analysis/generate_report.py results/raw_output/<file>.csv --type html
python analysis/generate_report.py results/raw_output/<file>.csv --type pdf
```

- Comparative analysis:

```bash
python analysis/comparative_analysis.py results/raw_output/<file>.csv --output-file reports/comparative_<timestamp>.json
```

- LLM-as-judge evaluation:

```bash
python analysis/llm_judge_evaluation.py results/raw_output/<file>.csv --judge-model gpt-4 --prompt-column prompt --response-column response_text --model-column model
```

Reports and exported PNGs are saved under `reports/` and `reports/images/`.

## 10. Web Interfaces

Install development dependencies and start the web UI:

```bash
pip install -e .[dev]
# optional visualization extras
pip install -e .[viz]
python web/web_ui.py
```

The dashboard listens on port 5000 by default (http://127.0.0.1:5000/). The web UI supports CSV/JSON downloads and clearly marks synthetic fallback responses.

*For architecture and deployment notes, see `docs/technical-handbook.md`.*

## 11. Scope Width Evaluation

### 11.1 What is Scope Width?

**Scope width** measures whether an LLM response maintains appropriate pedagogical boundaries:

- **Narrow (score 1-2)**: Response is unhelpfully minimal, missing necessary context
- **Appropriate (score 3-4)**: Well-focused, provides relevant guidance without solving the problem
- **Too Broad (score 5-6)**: Includes excessive tangents, unrelated topics, or meta-discussion

### 11.2 Automated Analysis

Run scope width analysis on benchmark results:

```bash
python -m analysis.scope_width_analysis results/raw_output/benchmark_results_20251013.csv
```

This generates:
- Scope distribution percentages (narrow/appropriate/too_broad)
- Average scope score (1-6 scale)
- Confidence ratings for each assessment
- Detailed JSON output saved alongside results

### 11.3 Human Evaluation Trials

The repository includes infrastructure for human trials:

1. **120-prompt bank** (`data/test_prompts_120.json`): Diverse engineering scenarios with ground-truth scope labels
2. **Google Form template** (`data/human_trials_google_form_template.md`): Structured evaluation rubric
3. **Category distribution**: Socratic Probing (28), Contextualization (26), Feedback (24), Edge Cases (14), Safety (10), Templates (2)

#### Running Human Trials:

1. Generate LLM responses for all 120 prompts using the benchmark harness
2. Create 6 Google Form variants (20 prompts each, balanced across categories)
3. Recruit 15-20 evaluators per variant (90-120 total evaluations)
4. Analyze inter-rater reliability and compare human vs. automated scope assessments

See `data/human_trials_google_form_template.md` for complete implementation details, rubric definitions, and analysis scripts.

## 12. Testing and Quality Assurance

- Run all tests locally:

```bash
pytest
```

- Install and run pre-commit hooks:

```bash
pre-commit install
pre-commit run --all-files
```

- Focused test runs (example):

```bash
pytest tests/test_main.py -k synthetic
```

*For CI configuration and detailed testing workflows, see `docs/technical-handbook.md`.*

## 13. Performance and Reliability Practices

- Use `RateLimiter` to enforce per-model throttling and avoid quota violations.
- CSV writes are append-only and atomic; SQLite used for optional persistence.
- Synthetic responses are deterministic (seeded) to support reproducible regression tests.

## 14. Version History

- **v0.1.0** — Foundational benchmarking and dashboard skeleton.
- **v0.1.1** — Token accounting and validation improvements.
- **v0.1.2** — Data lifecycle utilities and visualization additions.
- **v0.1.3** — Synthetic fallback and reporting enhancements.
- **v0.1.4** — Observability, import tests, and documentation overhaul.
- **v0.2.0** — Scope width metric, 120-prompt bank, and human trial infrastructure.

## 14. Troubleshooting and Support

- Authentication failures: verify keys in `.env` and run `python check_models.py`.
- Rate limit errors: increase `rate_limit_seconds` or reduce concurrency.
- Missing adapters: make sure the adapter path in `models.json` points to a callable exported by `adapters/__init__.py`.
- Dashboard shows empty results: check that `results/` contains timestamped CSVs.

*For comprehensive troubleshooting tables, error code mappings, and log-gathering steps, consult `docs/technical-handbook.md`.*

## 15. Documentation

Build the Sphinx reference documentation:

```bash
pip install -e .[dev]
cd docs
sphinx-build -b html . _build/html
# Open _build/html/index.html in a browser
```

The `docs/` directory contains API references and the technical handbook used by maintainers.

## 16. Contributing

1. Fork and create a feature branch (`feature/<topic>`).
2. Run `pre-commit` and `pytest` locally.
3. Make changes, update docs, add tests, and submit a pull request.

## 17. Release Checklist

- Update version notes in Section 13 with date and highlights.
- Ensure `pyproject.toml` and `requirements.txt` remain in sync.
- Regenerate documentation and confirm the dashboard loads locally.
- Tag the release in Git (e.g., `v0.1.x`).

## 18. Support

- Primary contact: Mettle research engineering team (Slack `#llm-harness`).
- File GitHub issues for defects with reproduction steps and logs.

---

**Last Updated**: October 15, 2025

## Quickstart (5-minute)

Follow these minimal steps to run a quick benchmark locally.

1. Clone and enter the repository:

```bash
git clone https://github.com/ksawesome/llm-harness
cd llm-harness
```

2. Create a virtual environment and install dependencies (Conda recommended):

```bash
conda create --name llm-harness-env python=3.11 -y
conda activate llm-harness-env
pip install -e .[dev]
# Optional visualization extras
pip install -e .[viz]
```

3. Copy the example environment and add your keys (or rely on synthetic providers):

```bash
cp .env.example .env
# Edit .env to set provider keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
```

4. Run a dry-run to validate configuration without calling live APIs:

```bash
python main.py --dry-run --prompt-range 1-3
```

5. Run a quick, synthetic-only benchmark:

```bash
python main.py --model gpt-4o-mini --prompt-range 1-5 --include-helm
```

6. Start the web dashboard (for exploration of results):

```bash
python web/web_ui.py
# Open http://127.0.0.1:5000/ in your browser
```

If you need operational detail beyond the Quickstart, consult the technical handbook (`docs/technical-handbook.md`) which documents architecture, adapter contracts, and troubleshooting.

## CLI Reference (common flags)

The harness exposes a compact set of flags for targeted execution. Below are the most useful for daily work.

- `--model <model-key>`: Run only a single model defined in `models.json`.
- `--category <name>`: Run all models with the specified `category` value.
- `--system_prompt <name>`: Choose the system prompt (defaults to `strict_socratic`).
- `--include-helm`: Merge HELM-style prompts into the prompt set for robustness testing.
- `--prompt-range start-end` or `--prompt-range 5`: Execute a contiguous slice of prompts for quick validation.
- `--dry-run`: Validate configuration and show what would run without issuing API calls.
- `--template-vars '{"k1": "v1", "k2": 3}'`: Provide JSON-encoded template variables for Jinja2 expansion (note proper shell quoting).

Example — combining flags:

```bash
python main.py --model gemini-2.5-flash --prompt-range 1-5 --include-helm --template-vars '{"vehicle_type":"car"}' --system_prompt neutral_instruction
```

## Example `models.json` entry

A small example showing the fields the harness expects for each model. Keep this file declarative and lightweight.

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

Tip: Use `models_config.py` to validate entries before running a full benchmark.

## Interpreting Results (quick guide)

Every benchmark creates a timestamped CSV under `results/raw_output/`. Core columns are:

- `prompt_id`: Identifier from `data/test_prompts.json`.
- `model`: The model key (matches `models.json`).
- `model_version`: Adapter-provided model version string.
- `date_time`: ISO8601 timestamp for the row.
- `latency_ms`: Measured (or simulated) latency in milliseconds.
- `tokens_in` / `tokens_out`: Token accounting for the request/response.
- `cost_usd`: Estimated (or zero for synthetic) cost for the call.
- `response_text`: The model's output text.
- `response_length`: Character length of `response_text`.
- `api_failed`: `True` when the harness used a fallback instead of a live API.

Quick analysis snippet (Python / Pandas):

```python
import pandas as pd
df = pd.read_csv('results/raw_output/benchmark_results_2025XXXX_XXXXXX.csv')
# Ignore fallback rows
live = df[~df['api_failed']]
# Average latency and cost by model
live.groupby('model').agg({'latency_ms':'mean', 'cost_usd':'sum'})
```

For detailed report contents (PDF, PNG exports, and LLM-as-judge outputs) see `analysis/generate_report.py` and the technical handbook for interpretation guidance.

## Security & Secrets

- Never commit secrets to source control. Keep `.env` in `.gitignore` (use `.env.example` as a template).
- For CI, set provider keys as encrypted secrets in GitHub Actions (or use your organization's secret manager) and inject them into the environment at runtime.
- Rotate API keys regularly and use least-privilege keys when possible.
- When running third-party providers in CI, prefer the `--dry-run` and synthetic flows for smoke tests to avoid incurring costs or exposing secrets.

## FAQ (short)

Q: Why are synthetic responses useful?
A: They provide deterministic, reproducible outputs for offline testing, CI, and analysis development without incurring API costs or being rate-limited.

Q: How do I add a new provider adapter?
A: Implement a callable in `adapters/<provider>_adapter.py`, export it in `adapters/__init__.py`, and create a `models.json` entry. The technical handbook provides a complete adapter checklist.

Q: Sphinx documentation fails to build — what now?
A: Run `pip install -e .[dev]` and build docs locally; if autodoc fails, check that optional provider dependencies are installed or mock imports in `docs/conf.py`.

## Contributing (expanded)

When contributing, follow this PR checklist:

- Run `pre-commit run --all-files` and fix issues reported.
- Run full test suite with `pytest` and add tests for new behavior.
- Update `README.md` and `docs/technical-handbook.md` with operational or API changes.
- Write concise commit messages and prefer `feat:`, `fix:`, `docs:`, `test:` prefixes for clarity.

## License

See the repository `LICENSE` file for full licensing details. If no LICENSE is present, contact the maintainers before distributing derived work.
