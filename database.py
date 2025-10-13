"""
Database Storage for Benchmark Results
Provides SQLite-based storage and querying for benchmark results.
"""

import sqlite3
import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging

from utils.result_loader import load_results


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

            # Ensure additional columns exist (for schema evolution)
            self._ensure_column(conn, "benchmark_results", "date_time", "TEXT")
            self._ensure_column(
                conn,
                "benchmark_results",
                "response_length",
                "INTEGER DEFAULT 0",
            )
            self._ensure_column(
                conn, "benchmark_results", "synthetic", "INTEGER DEFAULT 0"
            )
            self._ensure_column(conn, "benchmark_results", "provider", "TEXT")
            self._ensure_column(
                conn, "benchmark_results", "synthetic_source", "TEXT"
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

    def _ensure_column(
        self,
        conn: sqlite3.Connection,
        table: str,
        column: str,
        definition: str,
    ) -> None:
        existing = {
            row[1] for row in conn.execute(f"PRAGMA table_info({table})")
        }
        if column not in existing:
            conn.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
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

    def store_results_from_source(
        self,
        source_path: str,
        run_id: Optional[str] = None,
        include_synthetic: bool = True,
    ) -> bool:
        """Import benchmark results from a CSV file or directory."""

        try:
            df = load_results(source_path, include_synthetic=include_synthetic)
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.error(
                "Failed to load results from %s: %s", source_path, exc
            )
            return False

        if df.empty:
            self.logger.warning(
                "No benchmark records found in %s", source_path
            )
            return False

        default_run_id = run_id or Path(source_path).stem
        df["run_id"] = df["run_id"].fillna(default_run_id)

        if df["run_id"].isna().any():
            self.logger.error(
                "Run ID resolution failed for one or more rows from %s",
                source_path,
            )
            return False

        run_configs: Dict[str, Dict] = {}
        for rid, group in df.groupby("run_id"):
            config: Dict[str, object] = {
                "source": str(source_path),
                "row_count": int(len(group)),
            }
            if bool(group["synthetic"].all()):
                config["synthetic"] = True
                providers = sorted(
                    {
                        provider
                        for provider in group["provider"].dropna().unique()
                        if provider
                    }
                )
                if providers:
                    config["providers"] = providers
            run_configs[str(rid)] = config

        for rid, config in run_configs.items():
            self.store_benchmark_run(rid, config)

        def _optional(value: object) -> Optional[str]:
            if value in (None, ""):
                return None
            if isinstance(value, float) and pd.isna(value):
                return None
            return str(value)

        df["latency_ms"] = df["latency_ms"].astype(float)
        df["tokens_in"] = df["tokens_in"].astype(int)
        df["tokens_out"] = df["tokens_out"].astype(int)
        df["cost_usd"] = df["cost_usd"].astype(float)
        df["response_length"] = df["response_length"].astype(int)

        records = [
            (
                str(row.run_id),
                str(row.prompt_id),
                str(row.model),
                str(row.model_version),
                row.latency_ms,
                row.tokens_in,
                row.tokens_out,
                row.cost_usd,
                row.response_text or "",
                row.error_message or "",
                _optional(row.date_time),
                row.response_length,
                1 if bool(row.synthetic) else 0,
                _optional(row.provider),
                _optional(row.synthetic_source),
            )
            for row in df.itertuples(index=False)
        ]

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany(
                    """
                    INSERT INTO benchmark_results
                    (run_id, prompt_id, model, model_version, latency_ms, tokens_in, tokens_out, cost_usd, response_text, error_message, date_time, response_length, synthetic, provider, synthetic_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    records,
                )

            self.logger.info(
                "Stored %d records from %s", len(records), source_path
            )
            return True
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.error(
                "Failed to persist results from %s: %s", source_path, exc
            )
            return False

    def store_results_from_csv(self, csv_path: str, run_id: str) -> bool:
        """Backward-compatible wrapper for storing results from a CSV file."""

        return self.store_results_from_source(
            csv_path, run_id=run_id, include_synthetic=True
        )

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
        synthetic: Optional[bool] = None,
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

        if synthetic is not None:
            query += " AND synthetic = ?"
            params.append(1 if synthetic else 0)

        query += f" ORDER BY id DESC LIMIT {limit}"

        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_model_stats(
        self, run_id: Optional[str] = None, synthetic: Optional[bool] = None
    ) -> pd.DataFrame:
        """Get aggregated statistics by model."""
        query = """
            SELECT
                model,
                COUNT(*) as total_requests,
                SUM(CASE WHEN synthetic = 1 THEN 1 ELSE 0 END) as synthetic_requests,
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

        if synthetic is not None:
            query += " AND synthetic = ?"
            params.append(1 if synthetic else 0)

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
                SUM(CASE WHEN synthetic = 1 THEN 1 ELSE 0 END) as synthetic_requests,
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
            df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
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
    parser.add_argument(
        "--include-synthetic",
        action="store_true",
        help="Include synthetic results when importing",
    )

    args = parser.parse_args()

    db = BenchmarkDatabase(args.db_path)

    if args.action == "import":
        if not args.csv_file or not args.run_id:
            print("Error: --csv-file and --run-id required for import")
            return

        success = db.store_results_from_source(
            args.csv_file,
            run_id=args.run_id,
            include_synthetic=args.include_synthetic,
        )
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
