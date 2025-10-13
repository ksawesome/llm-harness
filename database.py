"""
Database Storage for Benchmark Results
Provides SQLite-based storage and querying for benchmark results.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging


class BenchmarkDatabase:
    """SQLite database for storing and querying benchmark results."""

    def __init__(self, db_path: str = "results/benchmark.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.init_database()

    def init_database(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS benchmark_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE,
                    timestamp TEXT,
                    config TEXT,
                    created_at REAL
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS benchmark_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    prompt_id TEXT,
                    model TEXT,
                    model_version TEXT,
                    latency_ms REAL,
                    tokens_in INTEGER,
                    tokens_out INTEGER,
                    cost_usd REAL,
                    response_text TEXT,
                    error_message TEXT,
                    FOREIGN KEY (run_id) REFERENCES benchmark_runs (run_id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    analysis_type TEXT,
                    analysis_data TEXT,
                    created_at REAL,
                    FOREIGN KEY (run_id) REFERENCES benchmark_runs (run_id)
                )
            """
            )

            # Create indexes for better query performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_results_run_id ON benchmark_results(run_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_results_model ON benchmark_results(model)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_analysis_run_id ON analysis_results(run_id)"
            )

    def store_benchmark_run(self, run_id: str, config: Dict) -> bool:
        """Store a benchmark run configuration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO benchmark_runs (run_id, timestamp, config, created_at) VALUES (?, ?, ?, ?)",
                    (
                        run_id,
                        datetime.now().isoformat(),
                        json.dumps(config),
                        datetime.now().timestamp(),
                    ),
                )
                self.logger.info(f"Stored benchmark run: {run_id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to store benchmark run: {e}")
            return False

    def store_results_from_csv(self, csv_path: str, run_id: str) -> bool:
        """Import benchmark results from CSV file."""
        try:
            df = pd.read_csv(csv_path)

            # Ensure required columns exist
            required_cols = ["prompt_id", "model", "latency_ms", "cost_usd"]
            missing_cols = [
                col for col in required_cols if col not in df.columns
            ]
            if missing_cols:
                self.logger.error(f"Missing required columns: {missing_cols}")
                return False

            with sqlite3.connect(self.db_path) as conn:
                # Store results in batches for better performance
                results = []
                for _, row in df.iterrows():
                    result = (
                        run_id,
                        str(row.get("prompt_id", "")),
                        str(row.get("model", "")),
                        str(row.get("model_version", "")),
                        float(row.get("latency_ms", 0)),
                        int(row.get("tokens_in", 0)),
                        int(row.get("tokens_out", 0)),
                        float(row.get("cost_usd", 0)),
                        str(row.get("response_text", "")),
                        str(row.get("error_message", "")),
                    )
                    results.append(result)

                conn.executemany(
                    """
                    INSERT INTO benchmark_results
                    (run_id, prompt_id, model, model_version, latency_ms, tokens_in, tokens_out, cost_usd, response_text, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    results,
                )

                self.logger.info(
                    f"Stored {len(results)} results from {csv_path}"
                )
                return True

        except Exception as e:
            self.logger.error(f"Failed to store results from CSV: {e}")
            return False

    def store_analysis_result(
        self, run_id: str, analysis_type: str, analysis_data: Dict
    ) -> bool:
        """Store analysis results."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO analysis_results (run_id, analysis_type, analysis_data, created_at) VALUES (?, ?, ?, ?)",
                    (
                        run_id,
                        analysis_type,
                        json.dumps(analysis_data),
                        datetime.now().timestamp(),
                    ),
                )
                self.logger.info(
                    f"Stored {analysis_type} analysis for run: {run_id}"
                )
                return True
        except Exception as e:
            self.logger.error(f"Failed to store analysis result: {e}")
            return False

    def get_runs(self, limit: int = 10) -> List[Dict]:
        """Get list of benchmark runs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM benchmark_runs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_results(
        self,
        run_id: Optional[str] = None,
        model: Optional[str] = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Query benchmark results."""
        query = "SELECT * FROM benchmark_results WHERE 1=1"
        params = []

        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)

        if model:
            query += " AND model = ?"
            params.append(model)

        query += f" ORDER BY id DESC LIMIT {limit}"

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_model_stats(self, run_id: Optional[str] = None) -> pd.DataFrame:
        """Get aggregated statistics by model."""
        query = """
            SELECT
                model,
                COUNT(*) as total_requests,
                AVG(latency_ms) as avg_latency,
                MIN(latency_ms) as min_latency,
                MAX(latency_ms) as max_latency,
                SUM(cost_usd) as total_cost,
                AVG(cost_usd) as avg_cost,
                SUM(CASE WHEN error_message IS NULL OR error_message = '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
            FROM benchmark_results
            WHERE 1=1
        """

        params = []
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)

        query += " GROUP BY model ORDER BY avg_latency"

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_run_comparison(self, run_ids: List[str]) -> pd.DataFrame:
        """Compare multiple runs."""
        placeholders = ",".join("?" * len(run_ids))

        query = f"""
            SELECT
                run_id,
                model,
                COUNT(*) as requests,
                AVG(latency_ms) as avg_latency,
                SUM(cost_usd) as total_cost,
                SUM(CASE WHEN error_message IS NULL OR error_message = '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
            FROM benchmark_results
            WHERE run_id IN ({placeholders})
            GROUP BY run_id, model
            ORDER BY run_id, avg_latency
        """

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=tuple(run_ids))

    def export_to_csv(self, run_id: str, output_path: str) -> bool:
        """Export run results to CSV."""
        try:
            df = self.get_results(
                run_id=run_id, limit=10000
            )  # Reasonable limit
            df.to_csv(output_path, index=False)
            self.logger.info(f"Exported {len(df)} results to {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export to CSV: {e}")
            return False

    def cleanup_old_runs(self, days_to_keep: int = 90) -> int:
        """Remove runs older than specified days."""
        cutoff_time = datetime.now().timestamp() - (
            days_to_keep * 24 * 60 * 60
        )

        with sqlite3.connect(self.db_path) as conn:
            # Get run IDs to delete
            cursor = conn.execute(
                "SELECT run_id FROM benchmark_runs WHERE created_at < ?",
                (cutoff_time,),
            )
            old_runs = [row[0] for row in cursor.fetchall()]

            if not old_runs:
                return 0

            # Delete in transaction
            placeholders = ",".join("?" * len(old_runs))

            conn.execute(
                f"DELETE FROM analysis_results WHERE run_id IN ({placeholders})",
                old_runs,
            )
            conn.execute(
                f"DELETE FROM benchmark_results WHERE run_id IN ({placeholders})",
                old_runs,
            )
            conn.execute(
                f"DELETE FROM benchmark_runs WHERE run_id IN ({placeholders})",
                old_runs,
            )

            deleted_count = len(old_runs)
            self.logger.info(f"Cleaned up {deleted_count} old runs")
            return deleted_count

    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Get table counts
            tables = {}
            for table in [
                "benchmark_runs",
                "benchmark_results",
                "analysis_results",
            ]:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                tables[table] = cursor.fetchone()[0]

            # Get database file size
            db_size = Path(self.db_path).stat().st_size / (1024 * 1024)  # MB

            return {
                "database_size_mb": round(db_size, 2),
                "total_runs": tables["benchmark_runs"],
                "total_results": tables["benchmark_results"],
                "total_analyses": tables["analysis_results"],
            }


def main():
    """Command-line interface for database operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark Database Manager")
    parser.add_argument(
        "action",
        choices=["import", "export", "stats", "cleanup"],
        help="Action to perform",
    )
    parser.add_argument("--csv-file", help="CSV file for import/export")
    parser.add_argument("--run-id", help="Run ID for operations")
    parser.add_argument(
        "--db-path", default="results/benchmark.db", help="Database path"
    )
    parser.add_argument(
        "--cleanup-days", type=int, default=90, help="Days to keep for cleanup"
    )

    args = parser.parse_args()

    db = BenchmarkDatabase(args.db_path)

    if args.action == "import":
        if not args.csv_file or not args.run_id:
            print("Error: --csv-file and --run-id required for import")
            return

        success = db.store_results_from_csv(args.csv_file, args.run_id)
        print(f"Import {'successful' if success else 'failed'}")

    elif args.action == "export":
        if not args.csv_file or not args.run_id:
            print("Error: --csv-file and --run-id required for export")
            return

        success = db.export_to_csv(args.run_id, args.csv_file)
        print(f"Export {'successful' if success else 'failed'}")

    elif args.action == "stats":
        stats = db.get_database_stats()
        print("=== Database Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")

    elif args.action == "cleanup":
        deleted = db.cleanup_old_runs(args.cleanup_days)
        print(f"Cleaned up {deleted} old runs")


if __name__ == "__main__":
    main()
