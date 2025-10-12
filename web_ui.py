from flask import Flask, render_template
import pandas as pd
import os

app = Flask(__name__)

RESULTS_DIR = "results/raw_output"


@app.route("/")
def index():
    if not os.path.exists(RESULTS_DIR):
        return "Results directory not found. Run benchmarks first."
    files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".csv")]
    if not files:
        return "No result files found. Run benchmarks first."
    return render_template("index.html", files=files)


@app.route("/results/<filename>")
def results(filename):
    filepath = os.path.join(RESULTS_DIR, filename)
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        return render_template(
            "results.html",
            tables=[
                df.to_html(
                    classes="table table-striped table-hover",
                    table_id="results-table",
                )
            ],
            filename=filename,
            df=df,
        )
    return "File not found", 404


if __name__ == "__main__":
    app.run(debug=True)
