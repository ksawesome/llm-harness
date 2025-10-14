from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
from flask import Flask, abort, render_template

from utils.result_loader import load_results

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(Path(__file__).resolve().parent / "templates"),
)

RAW_RESULTS_DIR = ROOT_DIR / "results" / "raw_output"
SYNTHETIC_RESULTS_DIR = Path(
    os.getenv(
        "LLM_HARNESS_SYNTHETIC_DIR",
        ROOT_DIR / "results" / "synthetic",
    )
)


def _prepare_table(df: pd.DataFrame) -> tuple[dict, str]:
    df = df.copy()
    success_mask = df["error_message"].fillna("") == ""
    stats = {
        "total": int(len(df)),
        "success": int(success_mask.sum()),
        "failure": int(len(df) - success_mask.sum()),
        "avg_latency": float(df["latency_ms"].mean()) if not df.empty else 0.0,
        "avg_response_length": (
            float(df["response_length"].mean())
            if "response_length" in df.columns and not df.empty
            else 0.0
        ),
    }

    table_html = df.to_html(
        index=False,
        classes="table table-striped table-hover",
        table_id="results-table",
    )
    return stats, table_html


@app.route("/")
def index():
    raw_files = (
        sorted([f.name for f in RAW_RESULTS_DIR.glob("*.csv")])
        if RAW_RESULTS_DIR.exists()
        else []
    )

    synthetic_providers = []
    if SYNTHETIC_RESULTS_DIR.exists():
        for provider_dir in SYNTHETIC_RESULTS_DIR.iterdir():
            if provider_dir.is_dir() and any(provider_dir.glob("*.json")):
                synthetic_providers.append(provider_dir.name)
    synthetic_providers.sort()

    if not raw_files and not synthetic_providers:
        return "No result files found. Run benchmarks first."

    return render_template(
        "index.html",
        raw_files=raw_files,
        synthetic_providers=synthetic_providers,
    )


@app.route("/results/<filename>")
def results(filename):
    file_path = RAW_RESULTS_DIR / filename
    if not file_path.exists():
        abort(404)

    df = load_results(file_path, include_synthetic=False)
    stats, table_html = _prepare_table(df)

    return render_template(
        "results.html",
        table_html=table_html,
        stats=stats,
        title=filename,
        synthetic=False,
    )


@app.route("/synthetic/<provider>")
def synthetic_results(provider: str):
    if not SYNTHETIC_RESULTS_DIR.exists():
        abort(404)

    df = load_results(SYNTHETIC_RESULTS_DIR, include_synthetic=True)
    df = df[df["provider"] == provider]

    if df.empty:
        abort(404)

    stats, table_html = _prepare_table(df)

    return render_template(
        "results.html",
        table_html=table_html,
        stats=stats,
        title=f"Synthetic: {provider}",
        synthetic=True,
        provider=provider,
    )


if __name__ == "__main__":
    app.run(debug=True)
