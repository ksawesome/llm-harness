# LLM Benchmarking Harness Technical Handbook

## 1. Purpose and Scope

This handbook complements the primary README by documenting how the harness is assembled, customized, and operated in practice. It is written for engineers and researchers who maintain Mettle's benchmarking infrastructure or who plan to integrate additional models, prompts, and analysis workflows.

The system measures pedagogical quality, responsiveness, and cost trade-offs for large language models drawn from OpenAI, Anthropic, Google, Cohere, and Hugging Face. Every component is built for repeatability, from deterministic synthetic fallbacks to database-backed storage and dual reporting channels (web dashboard plus formal reports).

## 2. Architecture Overview

### 2.1 High-Level Flow
+ Prompt catalogs are validated and expanded (templating, HELM, category filtering).
+ `main.py` coordinates asynchronous API calls through adapter functions with a `RateLimiter` guard.
+ Results are streamed to CSV, logged, and optionally persisted to SQLite via `database.py`.
+ Post-processing scripts in `analysis/` transform raw data into PDFs, HTML reports, comparative studies, and judge-based assessments.
+ The Flask web layer (`web/web_ui.py`) surfaces historical runs with drill-down charts.

### 2.2 Key Modules
+ `adapters/`: One module per provider. Each defines `call_<provider>_api` plus mocking hooks.
+ `utils/mock_provider.py`: Synthetic response factory with reproducible random seeds and persistence per provider.
+ `utils/result_loader.py`: Normalizes CSV directories, raw synthetic folders, and SQLite exports into Pandas DataFrames.
+ `analysis/`: Hosts reporting, comparative analytics, LLM-as-judge scoring, and visualization helpers.
+ `tests/`: Pytest suites covering adapters, orchestration logic, and code quality enforcement.

## 3. Feature Map

### 3.1 Benchmark Execution
- Asynchronous batch orchestration with concurrent semaphore control.
- Rate limit configuration per model, including cooldown windows and timeouts.
- Structured log events per request, including prompt metadata and response payloads.

### 3.2 Resilience Toolkit
- Synthetic fallback triggered automatically on API errors, flagged by `api_failed = True`.
- Provider-specific mock generation to simulate consistent failure and success scenarios.
- Graceful exception wrapping that captures stack traces without halting the run.

### 3.3 Reporting and Data Products
- `analysis/generate_report.py` produces rich PDF/HTML bundles with base64 visuals and filesystem PNG exports (`reports/images/`).
- `analysis/comparative_analysis.py` performs ANOVA, Wilcoxon, and rolling averages, outputting JSON narratives.
- `analysis/llm_judge_evaluation.py` leverages GPT-based judges to grade responses, generating detailed rubrics and descriptive insights.

### 3.4 Web and API Layer
- Flask application with modular blueprints for runs, results, and analytics views.
- REST-like endpoints returning JSON for integration with external dashboards.
- Bootstrap layout with responsive cards, tables, and modal dialogs for prompt-level exploration.

### 3.5 Developer Productivity
- Pre-commit automation: whitespace fixers, `black`, `isort`, `flake8`, `pyupgrade`, merge conflict detection, line ending normalization.
- Pyproject-managed dependencies with extras for development (`[dev]`) and visualization (`[viz]`).
- Docker image optimized for slim Python runtime, prepared directories, and health checks via `database.BenchmarkDatabase`.

## 4. Repository Structure and Ownership

```
llm-harness/
├── adapters/                    # Provider adapters, public API exported in adapters/__init__.py
├── analysis/                    # Reporting, statistical analysis, judge evaluation
├── data/                        # Prompt catalogs and optional HELM augmentations
├── docs/                        # Sphinx reference documentation
├── logs/                        # Runtime logs (rotated by deployment scripts)
├── results/                     # Benchmark outputs, synthetic archives, generated reports
├── templates/                   # HTML templates feeding the web dashboard
├── tests/                       # Pytest suites and smoke checks
├── utils/                       # Shared helpers (mock provider, result loader, etc.)
├── web/                         # Flask apps and static assets
├── .github/workflows/           # CI pipelines (pytest + pre-commit)
├── .gitignore                   # Root ignore rules (augmented with readme-temp.md)
├── templates/.gitignore         # Template-specific ignores
├── web/.gitignore               # Web asset ignores
├── Dockerfile                   # Production image build
├── README.md                    # Summary documentation
├── readme-temp.md               # Technical handbook (ignored in version control)
├── check_models.py              # Quick CLI to verify provider credentials
├── database.py                  # SQLite storage engine
├── environment.yml              # Conda environment (with comments for pip fallbacks)
├── main.py                      # Benchmark orchestrator and CLI entry point
├── manage_results.py            # Archival, compression, cleanup utilities
├── models.json                  # Model registry consumed by models_config.py
├── models_config.py             # Pydantic models and validation logic
├── prompt_utils.py              # Prompt loading, templating, and schema enforcement
├── pyproject.toml               # Build metadata and dependency locks
└── requirements.txt             # Frozen pip requirements for Docker builds
```

## 5. Model Configuration Deep-Dive

### 5.1 Adding a Provider
1. Implement a new function in `adapters/<provider>_adapter.py` returning a dictionary matching the schema used in existing adapters.
2. Export the function through `adapters/__init__.py` for dynamic retrieval.
3. Add the model entry to `models.json` with appropriate rate and timeout values.
4. Run `pytest tests/test_imports.py` to ensure the adapter loads correctly.
5. Execute `python main.py --model <new-model>` with `--dry-run` first, then with real calls.

### 5.2 Tuning Model Parameters
- Use `temperature` to control stochasticity during comparisons; set to `null` to preserve provider defaults.
- Categorize models (`category`) to drive `--category` filtering.
- Update `rate_limit_seconds` using official quota guidance; the harness enforces minimum spacing via `RateLimiter`.

### 5.3 Multi-Environment Support
- Keep multiple variants of `models.json` (e.g., staging vs. production) and pass them into `models_config.load_models_from_json` by pointing `--models-path` (CLI flag can be added if needed).
- Rapidly disable a model by removing its entry or by toggling a `disabled` flag (extend `ModelConfig` if desired).

## 6. Prompt System and HELM Usage

### 6.1 Schema Validation
- `prompt_utils.validate_json_data` validates prompt catalogs using schemas defined at the top of `prompt_utils.py`.
- Validation runs automatically when loading prompts; invalid structures raise explicit exceptions with file names for quick fixes.

### 6.2 Template Rendering Workflow
- Templated prompts allow scenario permutations. Example: include grade levels or domains via `student_grade`, `subject`, `difficulty` variables.
- Provide template variables through CLI, environment variables, or extend `main.py` to load from a JSON file.

### 6.3 HELM Integration Explained
- HELM scenarios focus on robustness, fairness, and safety. The harness ships with HELM-like prompts that simulate ambiguous or adversarial student queries.
- Activate HELM prompts using `--include-helm`; the system merges them, tagging each prompt with `source = "helm"` (see `mock_provider` index for caching).
- Use HELM prompts to stress-test fallback behavior and to compare providers on safety-critical benchmarks without risking real API quotas.

### 6.4 Recommended Operating Modes
- **Curriculum benchmarking**: Filter by categories (e.g., `reasoning`, `concept-check`) to produce subject-specific reports.
- **Adapter smoke tests**: Run `--prompt-range 1-3 --dry-run` after updating credentials or dependency versions.
- **Regression suites**: Combine HELM prompts with baseline prompts and run nightly in CI to detect degraded reasoning.

## 7. Execution Workflows

### 7.1 Standard Benchmark
```
python main.py
```
- Loads all prompts, expands templates, and evaluates every configured model.
- Writes timestamped CSV to `results/raw_output/` and logs to `logs/`.

### 7.2 Selective Runs
```
python main.py --model claude-3-sonnet --category writing --system_prompt neutral_instruction
```
- Ideal for adapter debugging or focused studies.

### 7.3 Synthetic-Only Trials
```
python main.py --dry-run
python main.py --model gpt-4o-mini --include-helm --prompt-range 1-5
```
- Use `--dry-run` to validate configuration; follow with a limited run to generate synthetic completions for integration smoke tests.

## 8. Output Artifacts and Storage Strategy

### 8.1 CSV Structure
- `prompt_id`, `model`, `model_version`, `latency_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `response_length`, `response_text`, `api_failed`, `error_message`, `date_time`.
- Synthetic rows share the structure but set `api_failed = True` and include annotations from `mock_provider`.

### 8.2 Database Integration
- `database.BenchmarkDatabase` stores run configurations, results, and analysis artifacts.
- Methods such as `get_model_stats` and `get_results` allow backend services to query aggregated metrics directly.

### 8.3 Report Generation
- `generate_report.py` saves PDFs/HTML plus PNG chart exports to `reports/`.
- Comparative JSON files live under `reports/` as well, ready for ingestion by analytics pipelines.

### 8.4 Archival and Cleanup
```
python manage_results.py archive --days 30
python manage_results.py compress
python manage_results.py cleanup
```
- Archives older runs into zip files, compresses raw CSVs, and removes transient files (e.g., temporary charts).

## 9. Web Experience Deep Dive

### 9.1 Flask Application Flow
- `web/web_ui.py` initializes Flask, loads run metadata from CSV/SQLite through `utils.result_loader`, and renders pages under `templates/`.
- Routes include `/`, `/runs/<run_id>`, `/results/<run_id>/<model>` for hierarchical drill-down.

### 9.2 Dashboard Features
- Summary cards for average latency, token usage, success rate, and cost.
- Charts for latency distributions, success by prompt category, and cost breakdowns.
- Tabs separating live API runs from synthetic fallback entries.
- Download links for CSV, PDF, and JSON artifacts.

### 9.3 Deployment Notes
- Default port: 5000. Override via CLI options or environment variables.
- Production deployments run behind a reverse proxy; use the Dockerfile to build hardened images with non-root users and health checks.

## 10. Testing and Quality Assurance Expansion

### 10.1 Test Types
- **Unit tests**: Validate adapters, prompt utilities, and database functions.
- **Integration tests**: `tests/test_main.py` loads prompts, runs synthetic flows, and validates output columns.
- **Structural tests**: `tests/test_imports.py` ensures every module is importable under the current packaging configuration.
- **Code quality tests**: `tests/test_code_quality.py` verifies `black` is enforced within the repository.

### 10.2 Suggested Workflow
1. Run `pre-commit run --all-files` before staging changes to catch formatting drift.
2. Execute `pytest` (or targeted tests) locally.
3. After a successful run, stage files and use the provided pre-commit message template.
4. Allow GitHub Actions to serve as final gate.

### 10.3 Coverage Targets
- Maintain adapter and prompt utility coverage above 90% to catch schema regressions.
- Add regression tests when introducing new prompt categories or LLM-as-judge scoring rules.

## 11. Performance and Reliability Enhancements

- Rate limiting uses monotonic timing to avoid clock-skew issues.
- CSV writes rely on Pandas with `mode="a"` and header guards for first writes only.
- Synthetic fallback uses deterministic seeds derived from `provider` and `prompt_id`, guaranteeing reproducible outputs.
- The Dockerfile installs system packages (gcc, g++, freetype, fontconfig) required for Matplotlib and ReportLab to ensure reports render identically across environments.
- Health checks in Docker confirm the SQLite database can be opened before the container reports healthy.

## 12. Version History Details

### 12.1 v0.1.0 – Foundation
- Established multi-provider benchmarking, baseline metrics, and dashboard skeleton.

### 12.2 v0.1.1 – Quality Pass
- Introduced token accounting, standardized error payloads, and enhanced linting.

### 12.3 v0.1.2 – Data Lifecycle
- Added archival utilities, compression flows, and early visualization notebooks.

### 12.4 v0.1.3 – Resilience Upgrade
- Implemented synthetic fallback, image exports, and tightened configuration validation.

### 12.5 v0.1.4 – Observability & Docs
- Delivered import structure tests, Docker health checks, and expanded documentation (current release).

## 13. Troubleshooting Reference

| Symptom | Likely Cause | Mitigation |
|---------|--------------|------------|
| `AuthenticationError` | Missing or stale API key | Update `.env`, rerun `check_models.py` |
| `RateLimitError` | Aggressive concurrency | Increase `rate_limit_seconds`, rerun |
| `ModuleNotFoundError` | Adapter not exported | Add to `adapters/__init__.py`, rerun tests |
| Empty dashboard tables | Results not loaded | Verify CSV paths, ensure `results/` populated |
| PDF charts missing | Dependencies missing | Reinstall `[viz]` extras or rebuild Docker image |

## 14. Documentation Strategy

- Sphinx configuration (`docs/conf.py`) adds the project root to `sys.path`, enabling autodoc imports.
- `docs/index.rst` outlines adapters, analysis, utils, and web modules; extend by creating topic-specific `.rst` files.
- Publish docs by running `sphinx-build` (see README Section 14) and hosting the `_build/html` directory via static site hosting.

## 15. Contribution Process

1. Fork and branch (`feature/<topic>` naming suggested).
2. Implement changes with descriptive docstrings; add inline comments only where logic is non-obvious.
3. Update both README documents if new features touch user workflows.
4. Run pre-commit and pytest.
5. Submit pull request referencing Jira or GitHub issue IDs.

## 16. Release Checklist

- Update version notes in Section 12 with date and highlights.
- Ensure `pyproject.toml` and `requirements.txt` remain in sync.
- Regenerate documentation (`sphinx-build`) and confirm dashboards load locally.
- Tag releases in Git with `v0.1.x` for traceability.

## 17. Support and Escalation

- Primary contact: Mettle research engineering team (Slack channel `#llm-harness`).
- Escalate provider outages to the integrations squad; provide CSV excerpts and log bundles.
- Use GitHub issues for defects; include reproduction steps, environment details, and relevant logs.

## 18. Appendix: Useful Commands

```
# Validate adapters and configuration
python check_models.py

# Inspect SQLite stats
python - <<'PY'
from database import BenchmarkDatabase
print(BenchmarkDatabase().get_database_stats())
PY

# Generate synthetic runs for all providers
python - <<'PY'
from utils.mock_provider import ensure_synthetic_runs
ensure_synthetic_runs()
PY
```

---

**Last Updated**: October 15, 2025
