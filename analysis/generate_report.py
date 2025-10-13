"""
Automated Report Generation for LLM Benchmarking Results
Generates PDF and HTML reports from analysis data.
"""

import pandas as pd
import matplotlib.pyplot as plt
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
from typing import Dict
import base64
import io


class BenchmarkReportGenerator:
    """Generates comprehensive reports from LLM benchmarking results."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Set up matplotlib/seaborn styling
        sns.set_theme(style="whitegrid")
        plt.rcParams["figure.figsize"] = (10, 6)
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

    def generate_summary_stats(self, df: pd.DataFrame) -> Dict:
        """Generate summary statistics for the report."""
        summary = {}

        # Overall statistics
        summary["total_requests"] = len(df)
        summary["total_models"] = df["model"].nunique()
        summary["models_list"] = df["model"].unique().tolist()
        summary["avg_latency"] = df["latency_ms"].mean()
        summary["total_cost"] = df["cost_usd"].sum()
        summary["success_rate"] = (
            df["error_message"].isna() | (df["error_message"] == "")
        ).mean() * 100

        # Per-model statistics
        model_stats = []
        for model in df["model"].unique():
            model_df = df[df["model"] == model]
            stats = {
                "model": model,
                "requests": len(model_df),
                "avg_latency": model_df["latency_ms"].mean(),
                "median_latency": model_df["latency_ms"].median(),
                "total_cost": model_df["cost_usd"].sum(),
                "success_rate": (
                    model_df["error_message"].isna()
                    | (model_df["error_message"] == "")
                ).mean()
                * 100,
                "error_count": (
                    model_df["error_message"].notna()
                    & (model_df["error_message"] != "")
                ).sum(),
            }
            model_stats.append(stats)

        summary["model_stats"] = sorted(
            model_stats, key=lambda x: x["avg_latency"]
        )
        return summary

    def create_visualizations(self, df: pd.DataFrame) -> Dict[str, str]:
        """Create visualizations and return as base64 encoded images."""
        images = {}

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

        plt.close("all")
        return images

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
        story.append(Spacer(1, 24))

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
            </div>

            <h2>Model Performance Summary</h2>
            <table>
                <tr>
                    <th>Model</th>
                    <th>Requests</th>
                    <th>Avg Latency (ms)</th>
                    <th>Success Rate (%)</th>
                    <th>Total Cost ($)</th>
                </tr>
                {"".join(f'''
                <tr>
                    <td>{stats["model"]}</td>
                    <td>{stats["requests"]}</td>
                    <td>{stats["avg_latency"]:.0f}</td>
                    <td>{stats["success_rate"]:.1f}</td>
                    <td>{stats["total_cost"]:.4f}</td>
                </tr>
                ''' for stats in summary['model_stats'])}
            </table>

            <h2>Visualizations</h2>
            {"".join(f'''
            <div class="chart">
                <h3>{key.replace("_", " ").title()}</h3>
                <img src="{images[key]}" alt="{key}">
            </div>
            ''' for key in images.keys())}

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
        images = self.create_visualizations(df)

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
