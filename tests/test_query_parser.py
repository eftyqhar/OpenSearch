"""
Unit tests for core/query_parser.py
Verifies parsing of filters, wildcards, sizes, dates, quotes, and combined search queries.
"""

import pytest
from core.query_parser import QueryParser, SearchQuery


def test_basic_terms():
    q = QueryParser.parse("project plan")
    assert q.terms == ["project", "plan"]
    assert not q.is_empty()


def test_quoted_phrases():
    q = QueryParser.parse('"project plan 2026" notes')
    assert q.phrases == ["project plan 2026"]
    assert q.terms == ["notes"]


def test_type_filters():
    q = QueryParser.parse("type:pdf")
    assert "pdf" in q.extensions

    q2 = QueryParser.parse("type:document")
    assert "document" in q2.categories

    q3 = QueryParser.parse("type:folder")
    assert q3.is_directory is True

    q4 = QueryParser.parse("type:file")
    assert q4.is_directory is False


def test_size_filters():
    q1 = QueryParser.parse("size:>1GB")
    assert q1.min_size == 1024 * 1024 * 1024

    q2 = QueryParser.parse("size:<10MB")
    assert q2.max_size == 10 * 1024 * 1024

    q3 = QueryParser.parse("size:1MB..50MB")
    assert q3.min_size == 1024 * 1024
    assert q3.max_size == 50 * 1024 * 1024


def test_modified_filters():
    q = QueryParser.parse("modified:today")
    assert q.min_modified is not None

    q2 = QueryParser.parse("modified:week")
    assert q2.min_modified is not None


def test_drive_and_path_filters():
    q = QueryParser.parse("drive:C")
    assert q.drive == "C:"

    q2 = QueryParser.parse("path:Projects")
    assert q2.path_contains == "Projects"


def test_wildcards():
    q1 = QueryParser.parse("*.pdf")
    assert "pdf" in q1.extensions

    q2 = QueryParser.parse("test_*_backup.py")
    assert q2.wildcard_pattern == "test_*_backup.py"


def test_negation():
    q = QueryParser.parse("project -temp !cache")
    assert "project" in q.terms
    assert "temp" in q.exclude_terms
    assert "cache" in q.exclude_terms


def test_combined_query():
    q = QueryParser.parse('type:pdf "Q3 Report" size:>500KB drive:D')
    assert "pdf" in q.extensions
    assert "Q3 Report" in q.phrases
    assert q.min_size == 500 * 1024
    assert q.drive == "D:"
