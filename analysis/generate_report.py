"""
Automated Report Generation for LLM Benchmarking Results
Generates PDF and HTML reports from analysis data.
"""

import html
import math
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
import os
from datetime import datetime
from typing import Dict, List, Optional
import base64
import io

import pandas as pd

from utils.result_loader import load_results


class BenchmarkReportGenerator:
    """Generates comprehensive reports from LLM benchmarking results."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Set up matplotlib/seaborn styling
        sns.set_theme(style="whitegrid")
        plt.rcParams["figure.figsize"] = (10, 6)
        plt.rcParams["font.size"] = 10

    def load_data(self, source_path: str) -> pd.DataFrame:
        """Load benchmark results, including synthetic runs when present."""

        if not os.path.exists(source_path):
            raise FileNotFoundError(
                f"Benchmark results source not found: {source_path}"
            )

        df = load_results(source_path, include_synthetic=True)

        required_cols = ["model", "latency_ms", "cost_usd"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        return df

    def generate_summary_stats(self, df: pd.DataFrame) -> Dict:
        """Generate summary statistics for the report."""
        summary: Dict[str, object] = {}

        # Overall statistics
        summary["total_requests"] = len(df)
        summary["total_models"] = df["model"].nunique()
        summary["models_list"] = df["model"].unique().tolist()
        summary["avg_latency"] = df["latency_ms"].mean()
        summary["total_cost"] = df["cost_usd"].sum()
        success_mask = df["error_message"].fillna("") == ""
        summary["success_rate"] = success_mask.mean() * 100
        summary["overall_cost_per_1k"] = (
            (summary["total_cost"] / summary["total_requests"]) * 1000
            if summary["total_requests"]
            else 0.0
        )

        latency_quantiles = {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}
        if not df.empty:
            quantile_values = df["latency_ms"].quantile([0.5, 0.9, 0.95, 0.99])
            latency_quantiles.update(
                {
                    "p50": float(quantile_values.get(0.5, 0.0)),
                    "p90": float(quantile_values.get(0.9, 0.0)),
                    "p95": float(quantile_values.get(0.95, 0.0)),
                    "p99": float(quantile_values.get(0.99, 0.0)),
                }
            )
        summary["overall_latency_percentiles"] = latency_quantiles

        # Per-model statistics
        model_stats: List[Dict[str, object]] = []
        for model in df["model"].unique():
            model_df = df[df["model"] == model]
            request_count = len(model_df)
            latency_series = model_df["latency_ms"].dropna()
            quantiles = (
                latency_series.quantile([0.5, 0.9, 0.95, 0.99])
                if not latency_series.empty
                else pd.Series(
                    [0.0, 0.0, 0.0, 0.0], index=[0.5, 0.9, 0.95, 0.99]
                )
            )
            total_cost = self._safe_float(model_df["cost_usd"].sum(), 0.0)
            cost_per_request = (
                total_cost / request_count if request_count else 0.0
            )
            cost_per_request = self._safe_float(cost_per_request, 0.0)

            score_mean = (
                model_df["score"].mean()
                if "score" in model_df.columns
                else None
            )
            avg_score = None
            if score_mean is not None:
                parsed_score = self._safe_float(
                    score_mean, default=float("nan"), allow_nan=True
                )
                if not math.isnan(parsed_score):
                    avg_score = parsed_score

            avg_tokens_in = self._safe_float(
                (
                    model_df["tokens_in"].mean()
                    if "tokens_in" in model_df.columns
                    else None
                ),
                0.0,
            )
            avg_tokens_out = self._safe_float(
                (
                    model_df["tokens_out"].mean()
                    if "tokens_out" in model_df.columns
                    else None
                ),
                0.0,
            )

            stats = {
                "model": model,
                "requests": request_count,
                "avg_latency": self._safe_float(
                    model_df["latency_ms"].mean(), 0.0
                ),
                "median_latency": self._safe_float(
                    model_df["latency_ms"].median(), 0.0
                ),
                "latency_p50": float(quantiles.get(0.5, 0.0)),
                "latency_p90": float(quantiles.get(0.9, 0.0)),
                "latency_p95": float(quantiles.get(0.95, 0.0)),
                "latency_p99": float(quantiles.get(0.99, 0.0)),
                "total_cost": total_cost,
                "avg_cost_per_request": cost_per_request,
                "cost_per_1k": cost_per_request * 1000,
                "success_rate": (
                    model_df["error_message"].isna()
                    | (model_df["error_message"] == "")
                ).mean()
                * 100,
                "error_count": (
                    model_df["error_message"].notna()
                    & (model_df["error_message"] != "")
                ).sum(),
                "avg_tokens_in": avg_tokens_in,
                "avg_tokens_out": avg_tokens_out,
                "avg_score": avg_score,
            }
            model_stats.append(stats)

        summary["model_stats"] = sorted(
            model_stats,
            key=self._model_sort_key,
        )
        summary["has_quality_scores"] = any(
            stat.get("avg_score") is not None
            for stat in summary["model_stats"]
        )
        summary["error_categories"] = self._summarize_error_categories(df)
        summary["qualitative_examples"] = self._extract_qualitative_examples(
            df
        )
        return summary

    def create_visualizations(
        self, df: pd.DataFrame, summary: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Create visualizations and return as base64 encoded images."""
        images: Dict[str, str] = {}

        # 1. Latency distribution by model
        plt.figure(figsize=(12, 6))
        successful_df = df[
            df["error_message"].isna() | (df["error_message"] == "")
        ]
        if not successful_df.empty:
            sns.boxplot(data=successful_df, x="model", y="latency_ms")
            plt.title("Latency Distribution by Model")
            plt.xticks(rotation=45)
            plt.tight_layout()
            images["latency_boxplot"] = self._fig_to_base64()

        # 2. Cost comparison
        plt.figure(figsize=(10, 6))
        cost_by_model = (
            df.groupby("model")["cost_usd"].sum().sort_values(ascending=False)
        )
        cost_by_model.plot(kind="bar")
        plt.title("Total Cost by Model")
        plt.ylabel("Total Cost (USD)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        images["cost_barplot"] = self._fig_to_base64()

        # 3. Success rate comparison
        plt.figure(figsize=(10, 6))
        success_rate = (
            df.groupby("model")["error_message"]
            .apply(lambda x: (x.isna() | (x == "")).mean() * 100)
            .sort_values(ascending=False)
        )
        success_rate.plot(kind="bar", color="green")
        plt.title("Success Rate by Model (%)")
        plt.ylabel("Success Rate (%)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        images["success_rate"] = self._fig_to_base64()

        # 4. Cost vs quality scatterplot
        if summary and summary.get("model_stats"):
            plt.figure(figsize=(8, 6))
            stats_df = pd.DataFrame(summary["model_stats"])
            if not stats_df.empty:
                quality_col = (
                    "avg_score"
                    if summary.get("has_quality_scores")
                    else "success_rate"
                )
                cost_series = pd.to_numeric(
                    stats_df["cost_per_1k"], errors="coerce"
                ).fillna(0.0)
                quality_series = pd.to_numeric(
                    stats_df[quality_col], errors="coerce"
                ).fillna(0.0)

                plt.scatter(cost_series, quality_series)
                for idx, row in stats_df.iterrows():
                    x_val = self._safe_float(row.get("cost_per_1k"), 0.0)
                    y_val = self._safe_float(row.get(quality_col), 0.0)
                    plt.annotate(
                        row["model"],
                        (x_val, y_val),
                        textcoords="offset points",
                        xytext=(4, 4),
                        fontsize=8,
                    )
                plt.xlabel("Cost per 1K interactions (USD)")
                plt.ylabel(
                    "Average Quality Score"
                    if quality_col == "avg_score"
                    else "Success Rate (%)"
                )
                plt.title("Cost vs Quality")
                plt.grid(alpha=0.3)
                plt.tight_layout()
                images["cost_quality_scatter"] = self._fig_to_base64()

        # 5. Latency CDFs
        plt.figure(figsize=(10, 6))
        plotted = False
        for model, model_df in df.groupby("model"):
            latencies = model_df["latency_ms"].dropna().sort_values()
            if latencies.empty:
                continue
            cdf = np.arange(1, len(latencies) + 1) / len(latencies)
            plt.plot(latencies, cdf, label=model)
            plotted = True
        if plotted:
            plt.xlabel("Latency (ms)")
            plt.ylabel("CDF")
            plt.title("Latency CDF by Model")
            plt.legend()
            plt.tight_layout()
            images["latency_cdf"] = self._fig_to_base64()

        # 6. Radar chart of key metrics
        if summary and summary.get("model_stats"):
            radar_image = self._create_radar_chart(summary["model_stats"])
            if radar_image:
                images["model_radar"] = radar_image

        plt.close("all")
        return images

    def _create_radar_chart(
        self, model_stats: List[Dict[str, object]]
    ) -> Optional[str]:
        stats_df = pd.DataFrame(model_stats)
        if stats_df.empty:
            return None

        metric_specs = [
            ("success_rate", False, "Success Rate"),
            ("latency_p50", True, "Latency P50"),
            ("cost_per_1k", True, "Cost per 1K"),
        ]

        if (
            "avg_score" in stats_df.columns
            and not stats_df["avg_score"].isna().all()
        ):
            metric_specs.append(("avg_score", False, "Quality Score"))

        available_metrics = [
            spec for spec in metric_specs if spec[0] in stats_df.columns
        ]
        if len(available_metrics) < 3:
            return None

        normalized_values = {}
        for metric, invert, _label in available_metrics:
            series = pd.to_numeric(stats_df[metric], errors="coerce")
            normalized_values[metric] = self._normalize_series(series, invert)

        labels = [label for _metric, _invert, label in available_metrics]
        angles = np.linspace(
            0, 2 * np.pi, len(labels), endpoint=False
        ).tolist()
        angles += angles[:1]

        plt.figure(figsize=(8, 8))
        ax = plt.subplot(111, polar=True)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)
        ax.set_ylim(0, 1)
        ax.set_yticks(np.linspace(0.2, 1.0, 5))
        ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"])

        for idx, row in stats_df.iterrows():
            values = [
                normalized_values[metric][idx]
                for metric, _invert, _label in available_metrics
            ]
            values += values[:1]
            ax.plot(angles, values, label=row["model"])
            ax.fill(angles, values, alpha=0.1)

        ax.set_title("Model Radar Comparison")
        ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))
        image = self._fig_to_base64()
        plt.close()
        return image

    def _normalize_series(
        self, series: pd.Series, invert: bool = False
    ) -> pd.Series:
        cleaned = series.replace([np.inf, -np.inf], np.nan)
        if cleaned.dropna().empty:
            return pd.Series([0.5] * len(series), index=series.index)
        min_val = cleaned.min()
        max_val = cleaned.max()
        if np.isclose(max_val, min_val):
            scaled = pd.Series([1.0] * len(series), index=series.index)
        else:
            scaled = (cleaned - min_val) / (max_val - min_val)
        if invert:
            scaled = 1 - scaled
        return scaled.fillna(0.5)

    def _model_sort_key(self, stat: Dict[str, object]) -> float:
        return self._safe_float(stat.get("avg_latency"), default=float("inf"))

    def _safe_float(
        self, value: object, default: float = 0.0, allow_nan: bool = False
    ) -> float:
        if value is None:
            return default
        try:
            if isinstance(value, (int, float)):
                result = float(value)
            elif isinstance(value, str):
                stripped = value.strip()
                if not stripped:
                    return default
                result = float(stripped)
            else:
                return default
        except (TypeError, ValueError):
            return default
        if not allow_nan and math.isnan(result):
            return default
        return result

    def _summarize_error_categories(self, df: pd.DataFrame) -> Dict[str, int]:
        if "error_message" not in df.columns:
            return {}
        categories = (
            df["error_message"].fillna("").apply(self._categorize_error)
        )
        counts = categories.value_counts()
        counts = counts.drop(labels=["Success"], errors="ignore")
        return counts.to_dict()

    def _categorize_error(self, message: str) -> str:
        text = (message or "").strip()
        if not text:
            return "Success"
        lower = text.lower()
        if "hallucin" in lower or "made up" in lower:
            return "Hallucination"
        if "missing context" in lower or "need more context" in lower:
            return "Missing Context"
        if "unsafe" in lower or "tox" in lower or "harmful" in lower:
            return "Unsafe Tone"
        if "quota" in lower or "rate limit" in lower:
            return "Rate Limit"
        if "auth" in lower or "api key" in lower:
            return "Authentication"
        if "timeout" in lower or "timed out" in lower:
            return "Timeout"
        return "Other Failure"

    def _extract_qualitative_examples(
        self, df: pd.DataFrame, max_examples: Optional[int] = None
    ) -> List[Dict[str, object]]:
        if df.empty:
            return []

        examples: List[Dict[str, object]] = []
        for model in sorted(df["model"].unique()):
            model_df = df[df["model"] == model]
            success_df = model_df[model_df["error_message"].fillna("") == ""]
            failure_df = model_df[model_df["error_message"].fillna("") != ""]

            best_example = self._select_example(success_df, prefer_high=True)
            worst_example = self._select_example(
                failure_df, prefer_high=False, use_error_text=True
            )
            if worst_example is None:
                worst_example = self._select_example(
                    success_df, prefer_high=False
                )

            examples.append(
                {
                    "model": model,
                    "best": best_example,
                    "worst": worst_example,
                }
            )

        if max_examples and len(examples) > max_examples:
            return examples[:max_examples]
        return examples

    def _select_example(
        self,
        df: pd.DataFrame,
        prefer_high: bool,
        use_error_text: bool = False,
    ) -> Optional[Dict[str, object]]:
        if df.empty:
            return None

        working = df.copy()
        working["__quality__"] = working.apply(self._quality_metric, axis=1)
        working = working.sort_values("__quality__", ascending=not prefer_high)
        row = working.iloc[0]
        response_text = row.get("response_text") or ""
        if use_error_text and not response_text:
            response_text = row.get("error_message") or ""
        tokens_out = int(self._safe_float(row.get("tokens_out"), 0.0))
        raw_score = row.get("score")
        score_val: Optional[float] = None
        if raw_score is not None:
            parsed_score = self._safe_float(
                raw_score, default=float("nan"), allow_nan=True
            )
            if not math.isnan(parsed_score):
                score_val = parsed_score
        example = {
            "prompt_id": row.get("prompt_id"),
            "response": response_text,
            "error_message": row.get("error_message") or "",
            "category": self._categorize_error(
                str(row.get("error_message") or "")
            ),
            "tokens_out": tokens_out,
            "score": score_val,
        }
        return example

    def _quality_metric(self, row: pd.Series) -> float:
        score_val = self._safe_float(
            row.get("score"), default=float("nan"), allow_nan=True
        )
        if not math.isnan(score_val):
            return score_val
        length_val = self._safe_float(row.get("response_length"), 0.0)
        if length_val > 0:
            return length_val
        tokens_val = self._safe_float(row.get("tokens_out"), 0.0)
        if tokens_val > 0:
            return tokens_val
        response = row.get("response_text") or ""
        return float(len(response))

    def _truncate_text(self, text: str, length: int = 320) -> str:
        if len(text) <= length:
            return text
        return text[: length - 3] + "..."

    def _fig_to_base64(self) -> str:
        """Convert current matplotlib figure to base64 string."""
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()
        return f"data:image/png;base64,{img_base64}"

    def generate_pdf_report(
        self, summary: Dict, images: Dict[str, str], output_path: str
    ):
        """Generate PDF report."""
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        quote_style = ParagraphStyle(
            "Quote",
            parent=styles["BodyText"],
            fontSize=9,
            textColor=colors.grey,
            leading=12,
            italic=True,
        )
        story = []

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            spaceAfter=30,
        )
        story.append(Paragraph("LLM Benchmarking Report", title_style))
        story.append(Spacer(1, 12))

        # Generation timestamp
        story.append(
            Paragraph(
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 24))

        # Executive Summary
        story.append(Paragraph("Executive Summary", styles["Heading2"]))
        summary_text = f"""
        This report analyzes the performance of {summary['total_models']} LLM models across {summary['total_requests']} requests.
        Overall success rate: {summary['success_rate']:.1f}%. Total cost: ${summary['total_cost']:.4f}.
        Average latency: {summary['avg_latency']:.0f}ms.
        """
        story.append(Paragraph(summary_text, styles["Normal"]))
        story.append(Spacer(1, 12))

        # Model Performance Table
        story.append(
            Paragraph("Model Performance Summary", styles["Heading2"])
        )

        # Create table data
        table_data = [
            [
                "Model",
                "Requests",
                "Avg Latency (ms)",
                "Success Rate (%)",
                "Total Cost ($)",
            ]
        ]
        for stats in summary["model_stats"]:
            table_data.append(
                [
                    (
                        stats["model"][:20] + "..."
                        if len(stats["model"]) > 20
                        else stats["model"]
                    ),
                    str(stats["requests"]),
                    f"{stats['avg_latency']:.0f}",
                    f"{stats['success_rate']:.1f}",
                    f"{stats['total_cost']:.4f}",
                ]
            )

        table = Table(table_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 18))

        # Detailed quantitative metrics
        story.append(
            Paragraph("Detailed Quantitative Metrics", styles["Heading2"])
        )
        detail_table_data = [
            [
                "Model",
                "Success (%)",
                "Latency P50 (ms)",
                "Latency P95 (ms)",
                "Cost / 1K ($)",
                "Avg Score",
            ]
        ]
        for stats in summary["model_stats"]:
            score_display = (
                f"{stats['avg_score']:.2f}"
                if stats.get("avg_score") is not None
                else "-"
            )
            detail_table_data.append(
                [
                    stats["model"],
                    f"{stats['success_rate']:.1f}",
                    f"{stats['latency_p50']:.0f}",
                    f"{stats['latency_p95']:.0f}",
                    f"{stats['cost_per_1k']:.4f}",
                    score_display,
                ]
            )

        detail_table = Table(detail_table_data)
        detail_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ]
            )
        )
        story.append(detail_table)
        story.append(Spacer(1, 18))

        # Latency percentiles
        story.append(Paragraph("Latency Percentiles", styles["Heading2"]))
        percentiles = summary.get("overall_latency_percentiles", {})
        latency_text = (
            f"P50: {percentiles.get('p50', 0.0):.0f} ms | "
            f"P90: {percentiles.get('p90', 0.0):.0f} ms | "
            f"P95: {percentiles.get('p95', 0.0):.0f} ms | "
            f"P99: {percentiles.get('p99', 0.0):.0f} ms"
        )
        story.append(Paragraph(latency_text, styles["Normal"]))
        story.append(Spacer(1, 12))

        # Error analysis
        story.append(Paragraph("Error Analysis", styles["Heading2"]))
        error_counts = summary.get("error_categories", {})
        if error_counts:
            for category, count in sorted(
                error_counts.items(), key=lambda item: item[1], reverse=True
            ):
                story.append(
                    Paragraph(f"{category}: {count}", styles["Normal"])
                )
        else:
            story.append(Paragraph("No errors recorded.", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Qualitative transcripts
        story.append(
            Paragraph(
                "Representative Qualitative Transcripts",
                styles["Heading2"],
            )
        )
        examples = summary.get("qualitative_examples", [])
        if examples:
            for example in examples:
                model_name = html.escape(str(example.get("model", "")))
                story.append(Paragraph(model_name, styles["Heading3"]))

                best = example.get("best")
                if best:
                    best_meta_bits = []
                    if best.get("prompt_id"):
                        best_meta_bits.append(
                            f"prompt {html.escape(str(best['prompt_id']))}"
                        )
                    best_meta_bits.append(f"tokens out: {best['tokens_out']}")
                    if best.get("score") is not None:
                        best_meta_bits.append(f"score: {best['score']:.2f}")
                    best_meta = ", ".join(best_meta_bits)
                    best_text = html.escape(
                        self._truncate_text(best.get("response", ""))
                    )
                    story.append(
                        Paragraph(
                            f"<b>Best:</b> {best_meta}", styles["Normal"]
                        )
                    )
                    story.append(Paragraph(f"<i>{best_text}</i>", quote_style))
                else:
                    story.append(
                        Paragraph(
                            "Best: No successful responses.",
                            styles["Normal"],
                        )
                    )

                worst = example.get("worst")
                if worst:
                    worst_meta_bits = []
                    if worst.get("prompt_id"):
                        worst_meta_bits.append(
                            f"prompt {html.escape(str(worst['prompt_id']))}"
                        )
                    if worst.get("category"):
                        worst_meta_bits.append(worst["category"])
                    worst_meta_bits.append(
                        f"tokens out: {worst['tokens_out']}"
                    )
                    worst_text = html.escape(
                        self._truncate_text(
                            worst.get("response")
                            or worst.get("error_message", "")
                        )
                    )
                    story.append(
                        Paragraph(
                            f"<b>Challenging:</b> {', '.join(worst_meta_bits)}",
                            styles["Normal"],
                        )
                    )
                    story.append(
                        Paragraph(f"<i>{worst_text}</i>", quote_style)
                    )
                else:
                    story.append(
                        Paragraph(
                            "Challenging: No error samples captured.",
                            styles["Normal"],
                        )
                    )

                story.append(Spacer(1, 12))
        else:
            story.append(
                Paragraph(
                    "No qualitative examples available.", styles["Normal"]
                )
            )

        story.append(Spacer(1, 18))

        # Recommendations
        story.append(Paragraph("Recommendations", styles["Heading2"]))
        best_latency = min(
            summary["model_stats"], key=lambda x: x["avg_latency"]
        )
        best_cost = min(summary["model_stats"], key=lambda x: x["total_cost"])
        best_reliability = max(
            summary["model_stats"], key=lambda x: x["success_rate"]
        )

        recommendations = f"""
        • Best latency: {best_latency['model']} ({best_latency['avg_latency']:.0f}ms avg)
        • Most cost-effective: {best_cost['model']} (${best_cost['total_cost']:.4f} total)
        • Most reliable: {best_reliability['model']} ({best_reliability['success_rate']:.1f}% success rate)
        """
        story.append(Paragraph(recommendations, styles["Normal"]))

        doc.build(story)

    def generate_html_report(
        self, summary: Dict, images: Dict[str, str], output_path: str
    ):
        """Generate HTML report."""
        model_rows = "".join(
            f"""
                <tr>
                    <td>{html.escape(str(stats['model']))}</td>
                    <td>{stats['requests']}</td>
                    <td>{stats['success_rate']:.1f}%</td>
                    <td>{stats['latency_p50']:.0f}</td>
                    <td>{stats['latency_p95']:.0f}</td>
                    <td>{stats['cost_per_1k']:.4f}</td>
                    <td>{('-' if stats.get('avg_score') is None else f"{stats['avg_score']:.2f}")}</td>
                </tr>
            """
            for stats in summary["model_stats"]
        )

        percentiles = summary.get("overall_latency_percentiles", {})
        latency_summary_html = (
            f"<p><strong>P50:</strong> {percentiles.get('p50', 0.0):.0f} ms | "
            f"<strong>P90:</strong> {percentiles.get('p90', 0.0):.0f} ms | "
            f"<strong>P95:</strong> {percentiles.get('p95', 0.0):.0f} ms | "
            f"<strong>P99:</strong> {percentiles.get('p99', 0.0):.0f} ms</p>"
        )

        error_counts = summary.get("error_categories", {})
        if error_counts:
            error_list_html = "".join(
                f"<li><strong>{html.escape(category)}</strong>: {count}</li>"
                for category, count in sorted(
                    error_counts.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            )
        else:
            error_list_html = "<li>No errors recorded.</li>"

        qualitative_sections: List[str] = []
        for example in summary.get("qualitative_examples", []):
            model_name = html.escape(str(example.get("model", "")))

            best = example.get("best")
            if best:
                best_meta_parts = []
                if best.get("prompt_id"):
                    best_meta_parts.append(
                        f"prompt {html.escape(str(best['prompt_id']))}"
                    )
                best_meta_parts.append(f"tokens out: {best['tokens_out']}")
                if best.get("score") is not None:
                    best_meta_parts.append(f"score: {best['score']:.2f}")
                best_meta = ", ".join(best_meta_parts)
                best_meta_display = f" ({best_meta})" if best_meta else ""
                best_text = html.escape(
                    self._truncate_text(best.get("response", ""))
                )
                best_html = (
                    f"<p><strong>Best</strong>{best_meta_display}:<br>"
                    f"<em>{best_text}</em></p>"
                )
            else:
                best_html = (
                    "<p><em>No successful responses for this model.</em></p>"
                )

            worst = example.get("worst")
            if worst:
                worst_meta_parts = []
                if worst.get("prompt_id"):
                    worst_meta_parts.append(
                        f"prompt {html.escape(str(worst['prompt_id']))}"
                    )
                if worst.get("category"):
                    worst_meta_parts.append(
                        html.escape(str(worst["category"]))
                    )
                worst_meta_parts.append(f"tokens out: {worst['tokens_out']}")
                worst_text = html.escape(
                    self._truncate_text(
                        worst.get("response") or worst.get("error_message", "")
                    )
                )
                worst_meta = ", ".join(worst_meta_parts)
                worst_meta_display = f" ({worst_meta})" if worst_meta else ""
                worst_html = (
                    f"<p><strong>Challenging</strong>{worst_meta_display}:<br>"
                    f"<em>{worst_text}</em></p>"
                )
            else:
                worst_html = "<p><em>No error samples captured.</em></p>"

            qualitative_sections.append(
                f"""
                <details>
                    <summary>{model_name}</summary>
                    <div class="transcript">
                        {best_html}
                        {worst_html}
                    </div>
                </details>
                """
            )

        qualitative_sections_html = (
            "".join(qualitative_sections)
            if qualitative_sections
            else "<p>No qualitative examples available.</p>"
        )

        visual_blocks_html = "".join(
            f"""
            <div class=\"chart\">
                <h3>{key.replace('_', ' ').title()}</h3>
                <img src=\"{images[key]}\" alt=\"{key}\">
            </div>
            """
            for key in images
        )

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LLM Benchmarking Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-box {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
                th {{ background-color: #f8f9fa; }}
                .chart {{ margin: 20px 0; text-align: center; }}
                .chart img {{ max-width: 100%; height: auto; }}
                details {{ margin-bottom: 12px; }}
                summary {{ cursor: pointer; font-weight: 600; }}
                .transcript {{ background-color: #f6f7fb; padding: 12px; border-radius: 6px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>LLM Benchmarking Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <h2>Executive Summary</h2>
            <div class="stats">
                <div class="stat-box">
                    <h3>{summary['total_models']}</h3>
                    <p>Models Tested</p>
                </div>
                <div class="stat-box">
                    <h3>{summary['total_requests']}</h3>
                    <p>Total Requests</p>
                </div>
                <div class="stat-box">
                    <h3>{summary['success_rate']:.1f}%</h3>
                    <p>Success Rate</p>
                </div>
                <div class="stat-box">
                    <h3>${summary['total_cost']:.4f}</h3>
                    <p>Total Cost</p>
                </div>
                <div class="stat-box">
                    <h3>${summary['overall_cost_per_1k']:.4f}</h3>
                    <p>Cost per 1K</p>
                </div>
            </div>

            <h2>Model Performance Summary</h2>
            <table>
                <tr>
                    <th>Model</th>
                    <th>Requests</th>
                    <th>Success Rate (%)</th>
                    <th>Latency P50 (ms)</th>
                    <th>Latency P95 (ms)</th>
                    <th>Cost / 1K ($)</th>
                    <th>Avg Score</th>
                </tr>
                {model_rows}
            </table>

            <h2>Latency Percentiles</h2>
            {latency_summary_html}

            <h2>Error Analysis</h2>
            <ul>{error_list_html}</ul>

            <h2>Visualizations</h2>
            {visual_blocks_html}

            <h2>Qualitative Highlights</h2>
            {qualitative_sections_html}

            <h2>Recommendations</h2>
            <ul>
                <li><strong>Best latency:</strong> {min(summary['model_stats'], key=lambda x: x['avg_latency'])['model']}</li>
                <li><strong>Most cost-effective:</strong> {min(summary['model_stats'], key=lambda x: x['total_cost'])['model']}</li>
                <li><strong>Most reliable:</strong> {max(summary['model_stats'], key=lambda x: x['success_rate'])['model']}</li>
            </ul>
        </body>
        </html>
        """

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)

    def generate_report(self, csv_path: str, report_type: str = "both"):
        """
        Generate comprehensive benchmarking report.

        Args:
            csv_path: Path to benchmark results CSV
            report_type: 'pdf', 'html', or 'both'
        """
        print("Loading benchmark data...")
        df = self.load_data(csv_path)

        print("Generating summary statistics...")
        summary = self.generate_summary_stats(df)

        print("Creating visualizations...")
        images = self.create_visualizations(df, summary)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if report_type in ["pdf", "both"]:
            pdf_path = os.path.join(
                self.output_dir, f"benchmark_report_{timestamp}.pdf"
            )
            print(f"Generating PDF report: {pdf_path}")
            self.generate_pdf_report(summary, images, pdf_path)

        if report_type in ["html", "both"]:
            html_path = os.path.join(
                self.output_dir, f"benchmark_report_{timestamp}.html"
            )
            print(f"Generating HTML report: {html_path}")
            self.generate_html_report(summary, images, html_path)

        print("Report generation complete!")
        return summary


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate LLM benchmarking reports"
    )
    parser.add_argument("csv_path", help="Path to benchmark results CSV file")
    parser.add_argument(
        "--output-dir", default="reports", help="Output directory for reports"
    )
    parser.add_argument(
        "--type",
        choices=["pdf", "html", "both"],
        default="both",
        help="Type of report to generate",
    )

    args = parser.parse_args()

    generator = BenchmarkReportGenerator(args.output_dir)
    generator.generate_report(args.csv_path, args.type)


if __name__ == "__main__":
    main()
