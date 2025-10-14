"""
Result Management and Cleanup Script
Archives old results, compresses large files, and manages storage.
"""

import argparse
import gzip
import logging
import shutil
from datetime import datetime
from pathlib import Path


class ResultManager:
    """Manages benchmark results storage, cleanup, and archiving."""

    def __init__(
        self,
        results_dir: str = "results",
        archive_dir: str = "results/archive",
    ):
        self.results_dir = Path(results_dir)
        self.archive_dir = Path(archive_dir)
        self.raw_output_dir = self.results_dir / "raw_output"
        self.synthetic_dir = self.results_dir / "synthetic"

        # Create directories if they don't exist
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def get_csv_files(self) -> list[Path]:
        """Get all CSV files in the results directory."""
        if not self.raw_output_dir.exists():
            return []

        return list(self.raw_output_dir.glob("*.csv"))

    def get_synthetic_csv_files(self) -> list[Path]:
        """Get synthetic response CSV files."""
        if not self.synthetic_dir.exists():
            return []

        csv_files: list[Path] = []
        for provider_dir in self.synthetic_dir.iterdir():
            if not provider_dir.is_dir():
                continue
            responses = provider_dir / "responses.csv"
            if responses.exists():
                csv_files.append(responses)
        return csv_files

    def get_file_info(self, file_path: Path) -> dict:
        """Get information about a file."""
        stat = file_path.stat()
        return {
            "path": file_path,
            "size_mb": stat.st_size / (1024 * 1024),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "age_days": (
                datetime.now() - datetime.fromtimestamp(stat.st_mtime)
            ).days,
        }

    def compress_large_files(
        self, size_threshold_mb: float = 10.0
    ) -> list[Path]:
        """Compress CSV files larger than threshold."""
        compressed_files = []
        csv_files = self.get_csv_files() + self.get_synthetic_csv_files()

        for csv_file in csv_files:
            info = self.get_file_info(csv_file)

            if info["size_mb"] > size_threshold_mb:
                compressed_path = csv_file.with_suffix(".csv.gz")

                self.logger.info(
                    f"Compressing {csv_file.name} ({info['size_mb']:.1f} MB)"
                )

                with open(csv_file, "rb") as f_in:
                    with gzip.open(compressed_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # Remove original file after successful compression
                csv_file.unlink()
                compressed_files.append(compressed_path)

        return compressed_files

    def archive_old_files(self, days_threshold: int = 30) -> list[Path]:
        """Archive files older than threshold."""
        archived_files = []
        csv_files = self.get_csv_files() + self.get_synthetic_csv_files()

        for csv_file in csv_files:
            info = self.get_file_info(csv_file)

            if info["age_days"] > days_threshold:
                archive_path = self.archive_dir / csv_file.name

                self.logger.info(
                    f"Archiving {csv_file.name} ({info['age_days']} days old)"
                )
                shutil.move(str(csv_file), str(archive_path))
                archived_files.append(archive_path)

        return archived_files

    def cleanup_empty_directories(self) -> list[Path]:
        """Remove empty directories."""
        cleaned_dirs = []

        for dir_path in [
            self.results_dir,
            self.archive_dir,
            self.synthetic_dir,
        ]:
            if dir_path.exists():
                try:
                    dir_path.rmdir()  # Only removes if empty
                    cleaned_dirs.append(dir_path)
                    self.logger.info(f"Removed empty directory: {dir_path}")
                except OSError:
                    # Directory not empty
                    pass

        return cleaned_dirs

    def get_storage_stats(self) -> dict:
        """Get storage statistics."""
        stats = {
            "total_files": 0,
            "total_size_mb": 0.0,
            "old_files": 0,
            "large_files": 0,
            "compressed_files": 0,
            "synthetic_providers": 0,
            "synthetic_records": 0,
            "synthetic_size_mb": 0.0,
        }

        csv_files = self.get_csv_files()

        for csv_file in csv_files:
            info = self.get_file_info(csv_file)
            stats["total_files"] += 1
            stats["total_size_mb"] += info["size_mb"]

            if info["age_days"] > 30:
                stats["old_files"] += 1
            if info["size_mb"] > 10:
                stats["large_files"] += 1
            if csv_file.suffix == ".gz":
                stats["compressed_files"] += 1

        if self.synthetic_dir.exists():
            provider_dirs = [
                provider
                for provider in self.synthetic_dir.iterdir()
                if provider.is_dir()
            ]
            stats["synthetic_providers"] = len(provider_dirs)

            synthetic_files: list[Path] = []
            for provider in provider_dirs:
                synthetic_files.extend(provider.glob("*.json"))
                responses_csv = provider / "responses.csv"
                if responses_csv.exists():
                    synthetic_files.append(responses_csv)

            stats["synthetic_records"] = sum(
                1 for file in synthetic_files if file.suffix == ".json"
            )
            stats["synthetic_size_mb"] = sum(
                file.stat().st_size for file in synthetic_files
            ) / (1024 * 1024)

        return stats

    def run_maintenance(
        self,
        compress_threshold_mb: float = 10.0,
        archive_threshold_days: int = 30,
    ) -> dict:
        """Run complete maintenance routine."""
        self.logger.info("Starting result maintenance...")

        # Get initial stats
        initial_stats = self.get_storage_stats()
        self.logger.info(
            f"Initial: {initial_stats['total_files']} files, {initial_stats['total_size_mb']:.1f} MB"
        )

        # Compress large files
        compressed = self.compress_large_files(compress_threshold_mb)
        self.logger.info(f"Compressed {len(compressed)} files")

        # Archive old files
        archived = self.archive_old_files(archive_threshold_days)
        self.logger.info(f"Archived {len(archived)} files")

        # Cleanup empty directories
        cleaned = self.cleanup_empty_directories()
        self.logger.info(f"Cleaned {len(cleaned)} directories")

        # Get final stats
        final_stats = self.get_storage_stats()
        self.logger.info(
            f"Final: {final_stats['total_files']} files, {final_stats['total_size_mb']:.1f} MB"
        )

        return {
            "initial_stats": initial_stats,
            "final_stats": final_stats,
            "compressed_files": len(compressed),
            "archived_files": len(archived),
            "cleaned_directories": len(cleaned),
            "synthetic_providers": final_stats.get("synthetic_providers", 0),
            "synthetic_records": final_stats.get("synthetic_records", 0),
        }


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Manage benchmark result files"
    )
    parser.add_argument(
        "--results-dir", default="results", help="Results directory path"
    )
    parser.add_argument(
        "--archive-dir",
        default="results/archive",
        help="Archive directory path",
    )
    parser.add_argument(
        "--compress-threshold",
        type=float,
        default=10.0,
        help="Compress files larger than this size (MB)",
    )
    parser.add_argument(
        "--archive-threshold",
        type=int,
        default=30,
        help="Archive files older than this many days",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show statistics, do not perform maintenance",
    )

    args = parser.parse_args()

    manager = ResultManager(args.results_dir, args.archive_dir)

    if args.stats_only:
        stats = manager.get_storage_stats()
        print("=== Storage Statistics ===")
        print(f"Total files: {stats['total_files']}")
        print(f"Total size: {stats['total_size_mb']:.1f} MB")
        print(f"Old files (>30 days): {stats['old_files']}")
        print(f"Large files (>10 MB): {stats['large_files']}")
        print(f"Compressed files: {stats['compressed_files']}")
    else:
        results = manager.run_maintenance(
            args.compress_threshold, args.archive_threshold
        )
        print("=== Maintenance Complete ===")
        print(f"Compressed files: {results['compressed_files']}")
        print(f"Archived files: {results['archived_files']}")
        print(f"Cleaned directories: {results['cleaned_directories']}")
        print(
            f"Space saved: {results['initial_stats']['total_size_mb'] - results['final_stats']['total_size_mb']:.1f} MB"
        )


if __name__ == "__main__":
    main()
