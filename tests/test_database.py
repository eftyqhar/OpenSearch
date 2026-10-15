"""
Unit tests for database/schema.py, database/database.py, and database/repositories.py
Verifies SQLite schema, batch inserts, mutations, renames, recursive deletes, and statistics.
"""

import os
import tempfile
from pathlib import Path
import pytest
from database.database import DatabaseManager
from database.repositories import FileRepository


@pytest.fixture
def temp_repo():
    """Create a temporary isolated SQLite database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_index.db"
        manager = DatabaseManager(db_path=db_path)
        manager.init_database()
        repo = FileRepository(db=manager)
        yield repo
        manager.close()


def test_batch_insert_and_stats(temp_repo):
    records = [
        ("file1.txt", "C:\\docs\\file1.txt", "C:\\docs", "txt", 1024, 100, 200, 300, 0, 0, 0, "C:"),
        ("file2.pdf", "C:\\docs\\file2.pdf", "C:\\docs", "pdf", 2048, 100, 250, 350, 0, 0, 0, "C:"),
        ("docs", "C:\\docs", "C:\\", "", 0, 50, 250, 350, 1, 0, 0, "C:"),
    ]

    inserted = temp_repo.insert_batch(records)
    assert inserted == 3

    stats = temp_repo.get_stats()
    assert stats["total_files"] == 2
    assert stats["total_folders"] == 1
    assert stats["total_size"] == 3072


def test_update_and_rename_file(temp_repo):
    record = ("old.txt", "C:\\docs\\old.txt", "C:\\docs", "txt", 100, 1, 1, 1, 0, 0, 0, "C:")
    temp_repo.insert_batch([record])

    # Rename
    temp_repo.rename_file("C:\\docs\\old.txt", "C:\\docs\\new.txt", "new.txt", "C:\\docs", "txt")

    conn = temp_repo.db.get_connection()
    row = conn.execute("SELECT * FROM files WHERE path = ?", ("C:\\docs\\new.txt",)).fetchone()
    assert row is not None
    assert row["name"] == "new.txt"


def test_recursive_directory_rename(temp_repo):
    records = [
        ("projects", "D:\\projects", "D:\\", "", 0, 1, 1, 1, 1, 0, 0, "D:"),
        ("code.py", "D:\\projects\\code.py", "D:\\projects", "py", 500, 1, 1, 1, 0, 0, 0, "D:"),
        ("sub", "D:\\projects\\sub", "D:\\projects", "", 0, 1, 1, 1, 1, 0, 0, "D:"),
        ("data.json", "D:\\projects\\sub\\data.json", "D:\\projects\\sub", "json", 200, 1, 1, 1, 0, 0, 0, "D:"),
    ]
    temp_repo.insert_batch(records)

    # Rename directory D:\projects -> D:\development
    temp_repo.rename_directory("D:\\projects", "D:\\development", "development", "D:\\")

    conn = temp_repo.db.get_connection()
    # Check updated child paths
    r1 = conn.execute("SELECT * FROM files WHERE path = ?", ("D:\\development\\code.py",)).fetchone()
    assert r1 is not None
    assert r1["parent_path"] == "D:\\development"

    r2 = conn.execute("SELECT * FROM files WHERE path = ?", ("D:\\development\\sub\\data.json",)).fetchone()
    assert r2 is not None
    assert r2["parent_path"] == "D:\\development\\sub"


def test_delete_by_prefix(temp_repo):
    records = [
        ("folder", "C:\\folder", "C:\\", "", 0, 1, 1, 1, 1, 0, 0, "C:"),
        ("child1.txt", "C:\\folder\\child1.txt", "C:\\folder", "txt", 100, 1, 1, 1, 0, 0, 0, "C:"),
        ("child2.txt", "C:\\folder\\child2.txt", "C:\\folder", "txt", 200, 1, 1, 1, 0, 0, 0, "C:"),
        ("other.txt", "C:\\other.txt", "C:\\", "txt", 300, 1, 1, 1, 0, 0, 0, "C:"),
    ]
    temp_repo.insert_batch(records)

    temp_repo.delete_by_prefix("C:\\folder")
    stats = temp_repo.get_stats()
    assert stats["total_files"] == 1
    assert stats["total_folders"] == 0
