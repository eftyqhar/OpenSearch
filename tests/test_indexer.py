"""
Unit tests for indexing/scanner.py and indexing/watcher.py
Verifies scandir directory crawling, exclusion matching, and watcher event handling.
"""

import os
import tempfile
from pathlib import Path
import pytest
from indexing.scanner import FilesystemScanner
from indexing.watcher import FilesystemWatcher
from database.database import DatabaseManager
from database.repositories import FileRepository


def test_scanner_traversal_and_exclusions():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure
        p = Path(tmpdir)
        (p / "folder1").mkdir()
        (p / "folder1" / "file1.txt").write_text("hello")
        (p / "node_modules").mkdir()
        (p / "node_modules" / "ignored.js").write_text("ignore")

        scanner = FilesystemScanner(
            batch_size=10,
            excluded_patterns=["node_modules"],
            index_hidden=True,
        )

        batches = list(scanner.scan_directory(str(p), "C:"))
        all_items = [item for b in batches for item in b]
        names = [item[0] for item in all_items]

        assert "file1.txt" in names
        assert "folder1" in names
        assert "ignored.js" not in names


def test_watcher_event_processing():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_watcher.db"
        manager = DatabaseManager(db_path=db_path)
        manager.init_database()
        repo = FileRepository(db=manager)
        watcher = FilesystemWatcher(repo=repo)

        # Test simulated create event
        test_file = Path(tmpdir) / "new_document.txt"
        test_file.write_text("content")

        watcher._handle_created(str(test_file), is_dir=False)

        stats = repo.get_stats()
        assert stats["total_files"] == 1

        # Test simulated delete event
        watcher._handle_deleted(str(test_file), is_dir=False)
        stats_after = repo.get_stats()
        assert stats_after["total_files"] == 0

        manager.close()
