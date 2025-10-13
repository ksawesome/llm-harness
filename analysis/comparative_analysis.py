"""
Comparative Analysis Script for LLM Benchmarking Results
Creates head-to-head comparisons between models and generates insights.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from typing import Dict, List, Optional
import os
from datetime import datetime


class ComparativeAnalyzer:
    """Analyzes and compares LLM benchmarking results across models."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Set up matplotlib/seaborn styling
        sns.set_theme(style="whitegrid")
        plt.rcParams["figure.figsize"] = (12, 8)
        plt.rcParams["font.size"] = 10

    def load_data(self, csv_path: str) -> pd.DataFrame:
        """Load benchmark results from CSV."""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(
                f"Benchmark results file not found: {csv_path}"
            )

        df = pd.read_csv(csv_path)

        # Basic data validation
        required_cols = ["model", "latency_ms", "cost_usd"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        return df

    def filter_successful_responses(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter to only successful responses (no errors)."""
        return df[df["error_message"].isna() | (df["error_message"] == "")]

    def create_model_comparison_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create a comparison matrix showing metrics for each model."""
        successful_df = self.filter_successful_responses(df)

        if successful_df.empty:
            raise ValueError("No successful responses found for comparison")

        # Group by model and calculate metrics
        comparison_data = []

        for model in successful_df["model"].unique():
            model_df = successful_df[successful_df["model"] == model]

            metrics = {
                "model": model,
                "total_requests": len(model_df),
                "successful_requests": len(model_df),
                "success_rate": 100.0,  # Already filtered to successful only
                "avg_latency_ms": model_df["latency_ms"].mean(),
                "median_latency_ms": model_df["latency_ms"].median(),
                "std_latency_ms": model_df["latency_ms"].std(),
                "min_latency_ms": model_df["latency_ms"].min(),
                "max_latency_ms": model_df["latency_ms"].max(),
                "total_cost_usd": model_df["cost_usd"].sum(),
                "avg_cost_per_request_usd": model_df["cost_usd"].mean(),
                "avg_tokens_in": (
                    model_df["tokens_in"].mean()
                    if "tokens_in" in model_df.columns
                    else 0
                ),
                "avg_tokens_out": (
                    model_df["tokens_out"].mean()
                    if "tokens_out" in model_df.columns
                    else 0
                ),
                "total_tokens": (
                    (model_df["tokens_in"] + model_df["tokens_out"]).mean()
                    if "tokens_in" in model_df.columns
                    and "tokens_out" in model_df.columns
                    else 0
                ),
            }
            comparison_data.append(metrics)

        return pd.DataFrame(comparison_data).sort_values("avg_latency_ms")

    def perform_statistical_tests(self, df: pd.DataFrame) -> Dict:
        """Perform statistical tests comparing model performance."""
        successful_df = self.filter_successful_responses(df)
        results = {}

        if len(successful_df["model"].unique()) < 2:
            results[
                "error"
            ] = "Need at least 2 models for statistical comparison"
            return results

        # Latency comparison
        latency_results = self._compare_metric(
            successful_df, "latency_ms", "Latency"
        )
        results["latency_comparison"] = latency_results

        # Cost comparison
        cost_results = self._compare_metric(successful_df, "cost_usd", "Cost")
        results["cost_comparison"] = cost_results

        return results

    def _compare_metric(
        self, df: pd.DataFrame, metric: str, metric_name: str
    ) -> Dict:
        """Compare a specific metric across models using statistical tests."""
        results = {}

        # Get data for each model
        model_data = {}
        for model in df["model"].unique():
            model_data[model] = df[df["model"] == model][metric].values

        # Remove models with insufficient data
        model_data = {k: v for k, v in model_data.items() if len(v) >= 3}

        if len(model_data) < 2:
            results[
                "error"
            ] = f"Need at least 2 models with sufficient data for {metric_name} comparison"
            return results

        # Calculate basic statistics
        stats_summary = {}
        for model, data in model_data.items():
            stats_summary[model] = {
                "mean": np.mean(data),
                "median": np.median(data),
                "std": np.std(data),
                "count": len(data),
            }

        results["statistics"] = stats_summary

        # Perform ANOVA if we have enough groups
        if len(model_data) >= 3:
            try:
                f_stat_result = stats.f_oneway(*model_data.values())
                # If the result is a tuple, unpack; if it's an object, extract values
                if isinstance(f_stat_result, tuple):
                    f_stat, p_value = f_stat_result
                else:
                    f_stat = getattr(f_stat_result, "statistic", None)
                    p_value = getattr(f_stat_result, "pvalue", None)
                results["anova"] = {
                    "f_statistic": f_stat,
                    "p_value": p_value,
                    "significant": (
                        float(p_value) < 0.05 if p_value is not None else False
                    ),
                }
            except Exception as e:
                results["anova_error"] = str(e)

        # Pairwise t-tests
        pairwise_results = []
        models = list(model_data.keys())

        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                model1, model2 = models[i], models[j]
                data1, data2 = model_data[model1], model_data[model2]

                try:
                    t_stat, p_value = stats.ttest_ind(
                        data1, data2, equal_var=False
                    )
                    # Ensure p_value is a float for comparison
                    if p_value is not None:
                        if (
                            isinstance(p_value, (tuple, list))
                            and len(p_value) > 0
                        ):
                            pval = p_value[0]
                        else:
                            pval = p_value
                        try:
                            # Ensure pval is a scalar and convertible to float before converting
                            if isinstance(pval, (tuple, list)):
                                pval_scalar = (
                                    pval[0] if len(pval) > 0 else None
                                )
                            else:
                                pval_scalar = pval
                            if pval_scalar is not None and isinstance(
                                pval_scalar, (int, float, np.number)
                            ):
                                significant = float(pval_scalar) < 0.05
                            else:
                                significant = False
                        except (TypeError, ValueError):
                            significant = False
                    else:
                        significant = False

                    pairwise_results.append(
                        {
                            "model1": model1,
                            "model2": model2,
                            "t_statistic": t_stat,
                            "p_value": p_value,
                            "significant": significant,
                            "mean_diff": np.mean(data1) - np.mean(data2),
                        }
                    )
                except Exception as e:
                    pairwise_results.append(
                        {"model1": model1, "model2": model2, "error": str(e)}
                    )

        results["pairwise_tests"] = pairwise_results
        return results

    def create_comparison_visualizations(
        self, df: pd.DataFrame
    ) -> Dict[str, str]:
        """Create visualizations comparing model performance."""
        successful_df = self.filter_successful_responses(df)
        images = {}

        if successful_df.empty:
            return images

        # 1. Latency comparison boxplot
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=successful_df, x="model", y="latency_ms")
        plt.title("Latency Distribution Comparison")
        plt.xticks(rotation=45)
        plt.ylabel("Latency (ms)")
        plt.tight_layout()
        images["latency_comparison"] = self._fig_to_base64()

        # 2. Cost comparison
        plt.figure(figsize=(12, 6))
        cost_by_model = (
            successful_df.groupby("model")["cost_usd"]
            .sum()
            .sort_values(ascending=False)
        )
        cost_by_model.plot(kind="bar")
        plt.title("Total Cost by Model")
        plt.ylabel("Total Cost (USD)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        images["cost_comparison"] = self._fig_to_base64()

        # 3. Success rate comparison (if we have error data)
        if "error_message" in df.columns:
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

        # 4. Performance radar chart (if we have multiple metrics)
        if len(successful_df["model"].unique()) >= 3:
            images["radar_chart"] = self._create_radar_chart(successful_df)

        plt.close("all")
        return images

    def _create_radar_chart(self, df: pd.DataFrame) -> str:
        """Create a radar chart comparing multiple metrics."""
        # Normalize metrics for radar chart
        models = df["model"].unique()
        metrics_data = {}

        for model in models:
            model_df = df[df["model"] == model]
            metrics_data[model] = {
                "latency": 1
                / (model_df["latency_ms"].mean() + 1),  # Inverse for speed
                "cost_efficiency": 1
                / (model_df["cost_usd"].mean() + 0.0001),  # Inverse for cost
                "consistency": 1
                / (
                    model_df["latency_ms"].std() + 1
                ),  # Inverse for variability
            }

        # Create radar chart
        fig, ax = plt.subplots(
            figsize=(8, 8), subplot_kw=dict(projection="polar")
        )

        # Calculate angles
        categories = list(metrics_data[models[0]].keys())
        angles = np.linspace(
            0, 2 * np.pi, len(categories), endpoint=False
        ).tolist()
        angles += angles[:1]  # Close the plot

        for model in models:
            values = [metrics_data[model][cat] for cat in categories]
            values += values[:1]  # Close the plot

            ax.plot(angles, values, "o-", linewidth=2, label=model)
            ax.fill(angles, values, alpha=0.25)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_title(
            "Model Performance Comparison (Normalized)", size=16, pad=20
        )
        ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.0))
        ax.grid(True)

        plt.tight_layout()
        return self._fig_to_base64()

    def _fig_to_base64(self) -> str:
        """Convert current matplotlib figure to base64 string."""
        import io
        import base64

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()
        return f"data:image/png;base64,{img_base64}"

    def generate_comparison_report(
        self, csv_path: str, output_path: Optional[str] = None
    ) -> Dict:
        """
        Generate comprehensive comparative analysis report.

        Args:
            csv_path: Path to benchmark results CSV
            output_path: Optional output path for the report

        Returns:
            Dictionary containing analysis results
        """
        print("Loading benchmark data...")
        df = self.load_data(csv_path)

        print("Creating comparison matrix...")
        comparison_df = self.create_model_comparison_matrix(df)

        print("Performing statistical tests...")
        stats_results = self.perform_statistical_tests(df)

        print("Creating visualizations...")
        visualizations = self.create_comparison_visualizations(df)

        # Generate insights
        insights = self._generate_insights(comparison_df, stats_results)

        # Save detailed results
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                self.output_dir, f"comparative_analysis_{timestamp}.json"
            )

        results = {
            "comparison_matrix": comparison_df.to_dict("records"),
            "statistical_tests": stats_results,
            "insights": insights,
            "visualizations": list(visualizations.keys()),
            "generated_at": datetime.now().isoformat(),
        }

        with open(output_path, "w") as f:
            import json

            json.dump(results, f, indent=2, default=str)

        print(f"Comparative analysis saved to {output_path}")
        return results

    def _generate_insights(
        self, comparison_df: pd.DataFrame, stats_results: Dict
    ) -> List[str]:
        """Generate human-readable insights from the analysis."""
        insights = []

        if comparison_df.empty:
            return ["No successful model responses found for analysis"]

        # Performance insights
        fastest_model = comparison_df.loc[
            comparison_df["avg_latency_ms"].idxmin()
        ]
        slowest_model = comparison_df.loc[
            comparison_df["avg_latency_ms"].idxmax()
        ]
        cheapest_model = comparison_df.loc[
            comparison_df["total_cost_usd"].idxmin()
        ]

        insights.append(
            f"Fastest model: {fastest_model['model']} ({fastest_model['avg_latency_ms']:.0f}ms avg)"
        )
        insights.append(
            f"Most cost-effective: {cheapest_model['model']} (${cheapest_model['total_cost_usd']:.4f} total)"
        )

        if len(comparison_df) > 1:
            latency_ratio = (
                slowest_model["avg_latency_ms"]
                / fastest_model["avg_latency_ms"]
            )
            insights.append(
                f"Speed difference: {latency_ratio:.1f}x between fastest and slowest models"
            )

        # Statistical insights
        if (
            "latency_comparison" in stats_results
            and "anova" in stats_results["latency_comparison"]
        ):
            anova = stats_results["latency_comparison"]["anova"]
            if anova["significant"]:
                insights.append(
                    "Statistical analysis shows significant differences in latency between models"
                )
            else:
                insights.append(
                    "No significant differences in latency found between models"
                )

        # Reliability insights
        most_reliable = comparison_df.loc[
            comparison_df["success_rate"].idxmax()
        ]
        insights.append(
            f"Most reliable: {most_reliable['model']} ({most_reliable['success_rate']:.1f}% success rate)"
        )

        return insights


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate comparative analysis of LLM benchmarking results"
    )
    parser.add_argument("csv_path", help="Path to benchmark results CSV file")
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Output directory for analysis results",
    )
    parser.add_argument(
        "--output-file",
        help="Output filename (optional, will auto-generate if not provided)",
    )

    args = parser.parse_args()

    analyzer = ComparativeAnalyzer(args.output_dir)
    results = analyzer.generate_comparison_report(
        args.csv_path, args.output_file
    )

    print("\n=== Comparative Analysis Summary ===")
    print(f"Models compared: {len(results['comparison_matrix'])}")
    print("\nKey Insights:")
    for insight in results["insights"]:
        print(f"• {insight}")


if __name__ == "__main__":
    main()
