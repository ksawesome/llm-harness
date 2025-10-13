"""
Visualization Dashboard for Benchmark Results
Local web application for viewing and analyzing benchmark results.
"""

import json
import logging
import os
import sys
from pathlib import Path

import plotly.express as px
from flask import Flask, jsonify, render_template

try:
    from database import BenchmarkDatabase
except ImportError:  # pragma: no cover - fallback for script execution
    ROOT_DIR = Path(__file__).resolve().parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from database import BenchmarkDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
db = BenchmarkDatabase()

# Create templates directory if it doesn't exist
os.makedirs("templates", exist_ok=True)


@app.route("/")
def dashboard():
    """Main dashboard page."""
    try:
        # Get recent runs
        runs = db.get_runs(limit=10)

        for run in runs:
            try:
                config = json.loads(run.get("config") or "{}")
            except json.JSONDecodeError:
                config = {}
            run["config"] = config
            run["is_synthetic"] = bool(config.get("synthetic"))
            run["providers"] = config.get("providers", [])

        # Get latest run stats
        if runs:
            latest_run = runs[0]["run_id"]
            model_stats = db.get_model_stats(latest_run)
            model_stats = (
                model_stats.to_dict("records") if not model_stats.empty else []
            )
        else:
            model_stats = []

        return render_template(
            "dashboard.html",
            runs=runs,
            model_stats=model_stats,
            latest_run=runs[0]["run_id"] if runs else None,
        )

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template(
            "dashboard.html", runs=[], model_stats=[], error=str(e)
        )


@app.route("/api/runs")
def get_runs():
    """API endpoint for benchmark runs."""
    try:
        runs = db.get_runs(limit=50)
        return jsonify({"runs": runs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/model_stats/<run_id>")
def get_model_stats(run_id):
    """API endpoint for model statistics."""
    try:
        stats = db.get_model_stats(run_id)
        return jsonify({"stats": stats.to_dict("records")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/charts/<run_id>")
def get_charts(run_id):
    """API endpoint for chart data."""
    try:
        # Get results for the run
        results_df = db.get_results(run_id=run_id, limit=5000)

        if results_df.empty:
            return jsonify({"error": "No data found"}), 404

        charts = {}

        # Latency distribution
        successful_results = results_df[
            results_df["error_message"].isna()
            | (results_df["error_message"] == "")
        ]
        if not successful_results.empty:
            fig = px.box(
                successful_results,
                x="model",
                y="latency_ms",
                title="Latency Distribution by Model",
            )
            charts["latency"] = fig.to_json()

        # Cost by model
        cost_by_model = (
            results_df.groupby("model")["cost_usd"].sum().reset_index()
        )
        if not cost_by_model.empty:
            fig = px.bar(
                cost_by_model,
                x="model",
                y="cost_usd",
                title="Total Cost by Model",
            )
            charts["cost"] = fig.to_json()

        # Success rate
        success_rate = (
            results_df.groupby("model")
            .apply(
                lambda x: (
                    x["error_message"].isna() | (x["error_message"] == "")
                ).mean()
                * 100
            )
            .reset_index(name="success_rate")
        )

        if not success_rate.empty:
            fig = px.bar(
                success_rate,
                x="model",
                y="success_rate",
                title="Success Rate by Model (%)",
            )
            charts["success_rate"] = fig.to_json()

        return jsonify({"charts": charts})

    except Exception as e:
        logger.error(f"Charts error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/run/<run_id>")
def run_details(run_id):
    """Detailed view for a specific run."""
    try:
        # Get run info
        runs = db.get_runs(limit=100)
        run_info = next((r for r in runs if r["run_id"] == run_id), None)

        if not run_info:
            return render_template("error.html", error="Run not found"), 404

        # Get model stats
        model_stats = db.get_model_stats(run_id)
        model_stats = (
            model_stats.to_dict("records") if not model_stats.empty else []
        )

        return render_template(
            "run_details.html",
            run=run_info,
            model_stats=model_stats,
            run_id=run_id,
        )

    except Exception as e:
        logger.error(f"Run details error: {e}")
        return render_template("error.html", error=str(e)), 500


@app.route("/compare")
def compare_runs():
    """Compare multiple runs."""
    try:
        runs = db.get_runs(limit=20)
        return render_template("compare.html", runs=runs)
    except Exception as e:
        return render_template("error.html", error=str(e)), 500


@app.route("/api/compare/<run_ids>")
def compare_api(run_ids):
    """API for comparing runs."""
    try:
        run_list = run_ids.split(",")
        comparison = db.get_run_comparison(run_list)
        return jsonify({"comparison": comparison.to_dict("records")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_templates():
    """Create HTML templates for the dashboard."""

    # Main dashboard template
    dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>LLM Benchmark Dashboard</title>
    <script src="https://cdn.plotly.com/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; border: 1px solid #ddd; padding: 20px; border-radius: 5px; }
        .stat-value { font-size: 2em; font-weight: bold; color: #007bff; }
        .chart-container { background: white; border: 1px solid #ddd; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f8f9fa; }
        .run-link { color: #007bff; text-decoration: none; }
        .run-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="header">
        <h1>LLM Benchmark Dashboard</h1>
        <p>Monitor and analyze your language model benchmarks</p>
    </div>

    <div class="stats-grid" id="stats-container">
        <!-- Stats will be loaded here -->
    </div>

    <div class="chart-container">
        <h2>Model Performance</h2>
        <div id="latency-chart"></div>
    </div>

    <div class="chart-container">
        <h2>Cost Analysis</h2>
        <div id="cost-chart"></div>
    </div>

    <div class="chart-container">
        <h2>Success Rates</h2>
        <div id="success-chart"></div>
    </div>

    <script>
        async function loadDashboard() {
            try {
                // Load stats
                const statsResponse = await fetch('/api/model_stats/{{ latest_run }}');
                const statsData = await statsResponse.json();

                if (statsData.stats && statsData.stats.length > 0) {
                    const container = document.getElementById('stats-container');
                    container.innerHTML = statsData.stats.map(stat => `
                        <div class="stat-card">
                            <h3>${stat.model}</h3>
                            <div class="stat-value">${stat.avg_latency.toFixed(0)}ms</div>
                            <p>Avg Latency</p>
                            <p>Success: ${stat.success_rate.toFixed(1)}%</p>
                            <p>Cost: $${stat.total_cost.toFixed(4)}</p>
                        </div>
                    `).join('');
                }

                // Load charts
                const chartsResponse = await fetch('/api/charts/{{ latest_run }}');
                const chartsData = await chartsResponse.json();

                if (chartsData.charts) {
                    if (chartsData.charts.latency) {
                        Plotly.newPlot('latency-chart', JSON.parse(chartsData.charts.latency).data, JSON.parse(chartsData.charts.latency).layout);
                    }
                    if (chartsData.charts.cost) {
                        Plotly.newPlot('cost-chart', JSON.parse(chartsData.charts.cost).data, JSON.parse(chartsData.charts.cost).layout);
                    }
                    if (chartsData.charts.success_rate) {
                        Plotly.newPlot('success-chart', JSON.parse(chartsData.charts.success_rate).data, JSON.parse(chartsData.charts.success_rate).layout);
                    }
                }
            } catch (error) {
                console.error('Error loading dashboard:', error);
            }
        }

        // Load dashboard on page load
        loadDashboard();
    </script>
</body>
</html>
    """

    # Run details template
    run_details_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Run Details - {{ run_id }}</title>
    <script src="https://cdn.plotly.com/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; border: 1px solid #ddd; padding: 20px; border-radius: 5px; }
        .stat-value { font-size: 2em; font-weight: bold; color: #007bff; }
        .chart-container { background: white; border: 1px solid #ddd; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f8f9fa; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Run Details: {{ run_id }}</h1>
        <p>Executed: {{ run.timestamp }}</p>
        <a href="/">← Back to Dashboard</a>
    </div>

    <div class="stats-grid" id="stats-container">
        <!-- Stats will be loaded here -->
    </div>

    <div class="chart-container">
        <h2>Latency Distribution</h2>
        <div id="latency-chart"></div>
    </div>

    <div class="chart-container">
        <h2>Cost Analysis</h2>
        <div id="cost-chart"></div>
    </div>

    <script>
        async function loadRunDetails() {
            try {
                // Load stats
                const statsResponse = await fetch('/api/model_stats/{{ run_id }}');
                const statsData = await statsResponse.json();

                if (statsData.stats && statsData.stats.length > 0) {
                    const container = document.getElementById('stats-container');
                    container.innerHTML = statsData.stats.map(stat => `
                        <div class="stat-card">
                            <h3>${stat.model}</h3>
                            <div class="stat-value">${stat.avg_latency.toFixed(0)}ms</div>
                            <p>Avg Latency</p>
                            <p>Requests: ${stat.total_requests}</p>
                            <p>Success: ${stat.success_rate.toFixed(1)}%</p>
                            <p>Cost: $${stat.total_cost.toFixed(4)}</p>
                        </div>
                    `).join('');
                }

                // Load charts
                const chartsResponse = await fetch('/api/charts/{{ run_id }}');
                const chartsData = await chartsResponse.json();

                if (chartsData.charts) {
                    if (chartsData.charts.latency) {
                        Plotly.newPlot('latency-chart', JSON.parse(chartsData.charts.latency).data, JSON.parse(chartsData.charts.latency).layout);
                    }
                    if (chartsData.charts.cost) {
                        Plotly.newPlot('cost-chart', JSON.parse(chartsData.charts.cost).data, JSON.parse(chartsData.charts.cost).layout);
                    }
                }
            } catch (error) {
                console.error('Error loading run details:', error);
            }
        }

        loadRunDetails();
    </script>
</body>
</html>
    """

    # Error template
    error_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Error</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="error">
        <h1>Error</h1>
        <p>{{ error }}</p>
        <a href="/">← Back to Dashboard</a>
    </div>
</body>
</html>
    """

    # Write templates
    with open("templates/dashboard.html", "w") as f:
        f.write(dashboard_html)

    with open("templates/run_details.html", "w") as f:
        f.write(run_details_html)

    with open("templates/error.html", "w") as f:
        f.write(error_html)

    print("Templates created successfully!")


def main():
    """Run the dashboard server."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark Results Dashboard")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument(
        "--port", type=int, default=5000, help="Port to bind to"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode"
    )

    args = parser.parse_args()

    # Create templates if they don't exist
    if not os.path.exists("templates/dashboard.html"):
        create_templates()

    print(f"Starting dashboard at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
