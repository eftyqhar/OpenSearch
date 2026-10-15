"""
Unit tests for core/ranking.py
Verifies scoring tiers: exact matches > prefixes > substrings > fuzzy subsequence matches.
"""

import pytest
from core.ranking import calculate_match_score, is_subsequence, rank_search_results


def test_scoring_tiers():
    query = "main"

    exact_score = calculate_match_score("main.py", "D:\\dev\\main.py", query)
    prefix_score = calculate_match_score("maintenance.py", "D:\\dev\\maintenance.py", query)
    word_boundary_score = calculate_match_score("app_main.py", "D:\\dev\\app_main.py", query)
    substring_score = calculate_match_score("domain_info.py", "D:\\dev\\domain_info.py", query)
    fuzzy_score = calculate_match_score("my_ancient_interface.py", "D:\\dev\\my_ancient_interface.py", query)

    assert exact_score > prefix_score
    assert prefix_score >= word_boundary_score
    assert word_boundary_score > substring_score
    assert substring_score > fuzzy_score


def test_subsequence_fuzzy():
    assert is_subsequence("reqtxt", "requirements.txt")
    assert is_subsequence("opnsrc", "opensearch.py")
    assert not is_subsequence("xyz", "requirements.txt")


def test_ranking_sort_order():
    items = [
        {"name": "backup_main_old.py", "path": "D:\\Projects\\backup_main_old.py", "modified_time": 100},
        {"name": "main.py", "path": "D:\\Projects\\main.py", "modified_time": 200},
        {"name": "main_test.py", "path": "D:\\Projects\\main_test.py", "modified_time": 150},
    ]

    ranked = rank_search_results(items, ["main"])
    assert ranked[0]["name"] == "main.py"
    assert ranked[1]["name"] == "main_test.py"
    assert ranked[2]["name"] == "backup_main_old.py"
