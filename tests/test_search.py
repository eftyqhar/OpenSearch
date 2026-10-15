"""
Unit tests for core/search_engine.py
Verifies search matching, filters, generation tokens for cancellation, and latency measurements.
"""

import tempfile
from pathlib import Path
import pytest
from database.database import DatabaseManager
from database.repositories import FileRepository
from core.search_engine import SearchEngine


@pytest.fixture
def search_setup():
    """Create isolated SQLite database and SearchEngine loaded with sample records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_search.db"
        manager = DatabaseManager(db_path=db_path)
        manager.init_database()
        repo = FileRepository(db=manager)

        sample_files = [
            ("project_plan.pdf", "D:\\Work\\project_plan.pdf", "D:\\Work", "pdf", 1887436, 100, 200, 300, 0, 0, 0, "D:"),
            ("project_notes.txt", "C:\\Users\\notes.txt", "C:\\Users", "txt", 12400, 100, 210, 300, 0, 0, 0, "C:"),
            ("project.py", "D:\\Dev\\project.py", "D:\\Dev", "py", 8192, 100, 220, 300, 0, 0, 0, "D:"),
            ("project-image.png", "D:\\Media\\project-image.png", "D:\\Media", "png", 1153433, 100, 190, 300, 0, 0, 0, "D:"),
            ("project", "D:\\Dev\\project", "D:\\Dev", "", 0, 50, 220, 300, 1, 0, 0, "D:"),
            ("random_data.db", "C:\\Data\\random_data.db", "C:\\Data", "db", 33554432, 100, 150, 300, 0, 0, 0, "C:"),
        ]
        repo.insert_batch(sample_files)
        engine = SearchEngine(db=manager)
        yield engine
        manager.close()


def test_basic_search(search_setup):
    res = search_setup.search("project")
    assert res.total_count == 5
    assert len(res.items) == 5
    assert res.execution_time_ms >= 0


def test_type_and_extension_filter(search_setup):
    res_pdf = search_setup.search("type:pdf")
    assert res_pdf.total_count == 1
    assert res_pdf.items[0]["name"] == "project_plan.pdf"

    res_doc = search_setup.search("type:document")
    assert res_doc.total_count == 2  # pdf and txt


def test_drive_filter(search_setup):
    res_d = search_setup.search("drive:D")
    assert res_d.total_count == 4
    for item in res_d.items:
        assert item["drive"] == "D:"


def test_size_filter(search_setup):
    res_large = search_setup.search("size:>10MB")
    assert res_large.total_count == 1
    assert res_large.items[0]["name"] == "random_data.db"


def test_query_cancellation(search_setup):
    # Simulate an obsolete query
    q1_id = search_setup.next_query_id()
    q2_id = search_setup.next_query_id()

    # Search with older q1_id
    res = search_setup.search("project", query_id=q1_id)
    assert res.is_cancelled is True
    assert len(res.items) == 0
