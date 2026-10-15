"""
OpenSearch by DeepLogic — Search & Indexing Performance Benchmark
Generates synthetic file trees in an isolated SQLite index, measures ingestion throughput (records/sec),
evaluates search latencies across queries (keyword, wildcard, type filter, size range, date),
and monitors memory usage.
"""

from __future__ import annotations
import os
import sys
import time
import random
import argparse
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psutil
from database.database import DatabaseManager
from database.repositories import FileRepository
from core.search_engine import SearchEngine


EXTENSIONS = [
    "py", "pdf", "docx", "txt", "png", "jpg", "mp4", "zip", "json", "html",
    "css", "cpp", "h", "xlsx", "pptx", "xml", "csv", "md", "exe", "db"
]

SAMPLE_WORDS = [
    "project", "plan", "report", "data", "backup", "system", "client", "invoice",
    "image", "video", "notes", "archive", "document", "financial", "analysis",
    "design", "schema", "config", "server", "database", "deep", "logic", "search",
    "main", "test", "build", "release", "source", "output", "temp", "cache"
]

SAMPLE_DIRS = [
    "C:\\Users\\User\\Documents",
    "C:\\Users\\User\\Downloads",
    "C:\\Users\\User\\Pictures",
    "D:\\Development\\Projects",
    "D:\\Work\\Clients\\2026",
    "D:\\Media\\Videos\\Personal",
    "D:\\Backup\\Archives\\Monthly",
    "D:\\Data\\Databases\\Production",
]


def generate_synthetic_records(count: int) -> list:
    """Generate mock file records for testing."""
    records = []
    now = time.time()
    for i in range(count):
        words = random.sample(SAMPLE_WORDS, k=random.randint(1, 3))
        is_dir = (random.random() < 0.08)
        parent = random.choice(SAMPLE_DIRS)
        drive = parent[:2]

        if is_dir:
            name = "_".join(words)
            ext = ""
            size = 0
        else:
            ext = random.choice(EXTENSIONS)
            name = f"{'_'.join(words)}.{ext}"
            # Distribution from 1KB to 2GB
            size = int(random.expovariate(1.0 / (2 * 1024 * 1024)))

        path = f"{parent}\\{name}"
        ctime = now - random.randint(0, 86400 * 365)
        mtime = ctime + random.randint(0, 86400 * 30)
        atime = mtime + random.randint(0, 86400 * 5)

        records.append((
            name, path, parent, ext, size, ctime, mtime, atime,
            1 if is_dir else 0, 0, 0, drive
        ))
    return records


def run_benchmark(item_count: int = 100000, batch_size: int = 5000) -> None:
    """Run full synthetic indexing and search benchmark."""
    print("=" * 60)
    print("      OpenSearch by DeepLogic — Performance Benchmark")
    print("=" * 60)
    print(f"Target items to index: {item_count:,}")
    print(f"Batch size: {batch_size:,}")

    process = psutil.Process()
    mem_before = process.memory_info().rss / (1024 * 1024)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "benchmark.db"
        manager = DatabaseManager(db_path=db_path)
        manager.init_database()
        repo = FileRepository(db=manager)
        engine = SearchEngine(db=manager)

        # 1. Measure Ingestion Speed
        print("\n--- 1. Generating & Ingesting Records ---")
        t0 = time.perf_counter()

        total_inserted = 0
        while total_inserted < item_count:
            chunk_size = min(batch_size, item_count - total_inserted)
            chunk = generate_synthetic_records(chunk_size)
            repo.insert_batch(chunk)
            total_inserted += len(chunk)

        ingest_duration = time.perf_counter() - t0
        ingest_rate = item_count / ingest_duration if ingest_duration > 0 else 0

        stats = repo.get_stats()
        mem_after = process.memory_info().rss / (1024 * 1024)

        print(f"Indexed files:       {stats['total_files']:,}")
        print(f"Indexed folders:     {stats['total_folders']:,}")
        print(f"Total size:          {stats['total_size'] / (1024**3):.2f} GB")
        print(f"Ingestion time:      {ingest_duration:.2f} s")
        print(f"Ingestion rate:      {ingest_rate:,.0f} files/sec")
        print(f"Process RAM delta:   {mem_after - mem_before:+.1f} MB (Total: {mem_after:.1f} MB)")

        # 2. Measure Search Latencies
        test_queries = [
            ("python", "Simple keyword"),
            ("project", "Common filename term"),
            ("*.pdf", "Wildcard extension"),
            ("type:image size:>5MB", "Category + Size filter"),
            ("type:document modified:today", "Category + Date filter"),
            ("drive:D path:Projects", "Drive + Path filter"),
            ("reqtxt", "Subsequence fuzzy match"),
            ("plan size:1MB..50MB", "Keyword + Range filter"),
        ]

        print("\n--- 2. Search Latency Evaluation ---")
        print(f"{'Query':<32} {'Matches':>10} {'Latency (ms)':>14} {'Category':<22}")
        print("-" * 80)

        latencies = []
        for query_str, description in test_queries:
            # Warm run
            res = engine.search(query_str, max_results=1000)
            latencies.append(res.execution_time_ms)
            print(f"{query_str:<32} {res.total_count:>10,} {res.execution_time_ms:>13.2f} ms {description:<22}")

        avg_latency = sum(latencies) / len(latencies)
        print("-" * 80)
        print(f"Average Search Latency: {avg_latency:.2f} ms")

        # 3. Incremental update benchmark
        print("\n--- 3. Incremental Update Latency ---")
        t_inc = time.perf_counter()
        sample_path = f"C:\\Users\\User\\Documents\\live_update_test.txt"
        repo.insert_batch([(
            "live_update_test.txt", sample_path, "C:\\Users\\User\\Documents",
            "txt", 4096, time.time(), time.time(), time.time(), 0, 0, 0, "C:"
        )])
        single_insert_time = (time.perf_counter() - t_inc) * 1000.0
        print(f"Single file addition latency: {single_insert_time:.3f} ms")

        manager.close()
        print("\nBenchmark completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenSearch Performance Benchmark")
    parser.add_argument("--count", type=int, default=100000, help="Number of synthetic items to index (default: 100,000)")
    parser.add_argument("--batch", type=int, default=5000, help="Batch size for inserts (default: 5,000)")
    args = parser.parse_args()

    run_benchmark(item_count=args.count, batch_size=args.batch)
