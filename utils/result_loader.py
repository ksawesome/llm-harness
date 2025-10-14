"""Utilities for loading benchmark results, including synthetic data."""

from __future__ import annotations

import csv
import json
import os
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

STANDARD_COLUMNS: list[str] = [
    "prompt_id",
    "model",
    "model_version",
    "date_time",
    "latency_ms",
    "tokens_in",
    "tokens_out",
    "cost_usd",
    "response_text",
    "error_message",
    "response_length",
    "synthetic",
    "provider",
    "synthetic_source",
    "run_id",
    "source_file",
]


def load_results(
    source: str | Path,
    include_synthetic: bool = True,
    synthetic_root: str | Path | None = None,
) -> pd.DataFrame:
    """Load benchmark results from a CSV file or directory.

    Args:
        source: Path to a CSV file or directory containing results.
        include_synthetic: Whether to merge synthetic results.
        synthetic_root: Optional explicit path to the synthetic directory.

    Returns:
        DataFrame containing combined results with standardised columns.
    """

    source_path = Path(source)
    frames: list[pd.DataFrame] = []

    if source_path.is_file() and source_path.suffix.lower() == ".csv":
        frames.append(_load_csv(source_path))
        if include_synthetic:
            synthetic_dir = _resolve_synthetic_root(
                source_path, synthetic_root
            )
            if synthetic_dir:
                frames.append(_load_synthetic_dir(synthetic_dir))
    elif source_path.is_dir():
        frames.extend(_load_csvs_from_directory(source_path))
        if include_synthetic:
            synthetic_dir = _resolve_synthetic_root(
                source_path, synthetic_root
            )
            if synthetic_dir:
                frames.append(_load_synthetic_dir(synthetic_dir))
    else:
        raise FileNotFoundError(f"Unsupported result source: {source_path}")

    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    combined = pd.concat(frames, ignore_index=True, sort=False)
    return _ensure_columns(combined)


def _load_csvs_from_directory(directory: Path) -> list[pd.DataFrame]:
    csv_files: list[Path] = []
    csv_files.extend(sorted(directory.glob("*.csv")))

    raw_output = directory / "raw_output"
    if raw_output.exists() and raw_output.is_dir():
        csv_files.extend(sorted(raw_output.glob("*.csv")))

    frames: list[pd.DataFrame] = []
    for csv_file in csv_files:
        frames.append(_load_csv(csv_file))
    return frames


def _load_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, quoting=csv.QUOTE_ALL)

    if "response_text" in df.columns:
        df["response_text"] = df["response_text"].fillna("")
    else:
        df["response_text"] = ""

    if "response_length" not in df.columns:
        df["response_length"] = df["response_text"].apply(len)
    else:
        # Handle case where response_length might contain invalid data
        def safe_int_convert(x):
            try:
                return int(float(x)) if pd.notna(x) else 0
            except (ValueError, TypeError):
                return len(str(x))  # Fallback to length of the string

        df["response_length"] = df["response_length"].apply(safe_int_convert)

    if "error_message" in df.columns:
        df["error_message"] = df["error_message"].fillna("")
    else:
        df["error_message"] = ""

    if "latency_ms" in df.columns:
        df["latency_ms"] = df["latency_ms"].fillna(0).astype(float)
    else:
        df["latency_ms"] = 0.0

    for column in ("tokens_in", "tokens_out"):
        if column in df.columns:
            df[column] = df[column].fillna(0).astype(int)
        else:
            df[column] = 0

    if "cost_usd" in df.columns:
        df["cost_usd"] = df["cost_usd"].fillna(0.0).astype(float)
    else:
        df["cost_usd"] = 0.0

    if "model_version" not in df.columns:
        if "model" in df.columns:
            df["model_version"] = df["model"].fillna("")
        else:
            df["model_version"] = ""
    else:
        df["model_version"] = df["model_version"].fillna("")

    df["synthetic"] = False
    df["provider"] = df.get("provider") if "provider" in df.columns else None
    df["synthetic_source"] = (
        df.get("synthetic_source")
        if "synthetic_source" in df.columns
        else None
    )

    run_id = None
    if "run_id" in df.columns:
        run_id = (
            df["run_id"].iloc[0] if not df["run_id"].isna().all() else None
        )
    inferred_run_id = run_id or csv_path.stem
    df["run_id"] = df.get("run_id", pd.Series([None] * len(df))).fillna(
        inferred_run_id
    )

    if "date_time" not in df.columns:
        df["date_time"] = None

    df["source_file"] = str(csv_path)
    return _ensure_columns(df)


def _load_synthetic_dir(root: Path) -> pd.DataFrame:
    records: list[dict] = []

    if not root.exists():
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    for provider_dir in sorted(root.iterdir()):
        if not provider_dir.is_dir():
            continue
        index_path = provider_dir / "index.json"
        if not index_path.exists():
            continue

        with index_path.open("r", encoding="utf-8") as handle:
            index_data = json.load(handle)

        provider = provider_dir.name
        run_id = f"synthetic-{provider}"

        for prompt_id, record in index_data.items():
            model_name = record.get("model_name", "")
            response_text = record.get("response_text", "") or ""
            records.append(
                {
                    "prompt_id": prompt_id,
                    "model": model_name,
                    "model_version": record.get(
                        "model_version",
                        (
                            f"{model_name}-synthetic"
                            if model_name
                            else "synthetic"
                        ),
                    ),
                    "date_time": record.get("generated_at"),
                    "latency_ms": float(record.get("latency_ms", 0.0) or 0.0),
                    "tokens_in": int(record.get("tokens_in", 0) or 0),
                    "tokens_out": int(record.get("tokens_out", 0) or 0),
                    "cost_usd": float(record.get("cost_usd", 0.0) or 0.0),
                    "response_text": response_text,
                    "error_message": record.get("error_message") or "",
                    "response_length": len(response_text),
                    "synthetic": True,
                    "provider": provider,
                    "synthetic_source": str(
                        provider_dir / f"{prompt_id}.json"
                    ),
                    "run_id": run_id,
                    "source_file": str(index_path),
                }
            )

    if not records:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    df = pd.DataFrame(records)
    return _ensure_columns(df)


def _resolve_synthetic_root(
    base_path: Path, synthetic_root: str | Path | None
) -> Path | None:
    if synthetic_root:
        candidate = Path(synthetic_root)
        return candidate if candidate.exists() else None

    env_path = os.getenv("LLM_HARNESS_SYNTHETIC_DIR")
    if env_path:
        candidate = Path(env_path)
        if candidate.exists():
            return candidate

    candidates: Iterable[Path] = []

    if base_path.is_dir():
        candidates = [
            base_path / "synthetic",
            base_path.parent / "synthetic",
        ]
    else:
        candidates = [
            base_path.parent / "synthetic",
            base_path.parent.parent / "synthetic",
        ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    for column in STANDARD_COLUMNS:
        if column not in df.columns:
            if column == "synthetic":
                df[column] = False
            elif column in {"tokens_in", "tokens_out", "response_length"}:
                df[column] = 0
            elif column in {"cost_usd", "latency_ms"}:
                df[column] = 0.0
            else:
                df[column] = None
    df["synthetic"] = df["synthetic"].astype(bool)
    df["tokens_in"] = df["tokens_in"].astype(int)
    df["tokens_out"] = df["tokens_out"].astype(int)
    df["response_length"] = df["response_length"].astype(int)
    df["cost_usd"] = df["cost_usd"].astype(float)
    df["latency_ms"] = df["latency_ms"].astype(float)

    ordered = [col for col in STANDARD_COLUMNS if col in df.columns]
    remaining = [col for col in df.columns if col not in ordered]
    return df[ordered + remaining]
