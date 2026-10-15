"""
OpenSearch by DeepLogic — Search Result Ranking & Fuzzy Scoring
Computes relevance scores prioritizing exact matches, prefixes, substrings, and fuzzy subsequence alignment.
"""

from __future__ import annotations
from typing import Dict, Any, List


def calculate_match_score(name: str, path: str, query_term: str) -> int:
    """
    Calculate an integer relevance score for a file/folder given a search term.
    Higher score indicates higher relevance.
    """
    if not query_term:
        return 100

    q = query_term.lower()
    name_lower = name.lower()
    path_lower = path.lower()

    # Exact filename match (e.g. 'main.py' or 'project')
    if name_lower == q:
        return 1000

    # Exact base filename without extension
    dot_idx = name_lower.rfind(".")
    stem = name_lower[:dot_idx] if dot_idx > 0 else name_lower
    if stem == q:
        return 950

    # Prefix match in filename
    if name_lower.startswith(q):
        return 850

    # Word boundary prefix in filename (e.g. 'project-plan' or 'project_notes')
    for sep in ("-", "_", " ", "."):
        if f"{sep}{q}" in name_lower:
            return 750

    # Substring anywhere in filename
    if q in name_lower:
        # Shorter filenames get slightly higher boost for compactness
        length_penalty = min(50, len(name) - len(q))
        return 650 - length_penalty

    # Path contains query
    if q in path_lower:
        return 400

    # Subsequence fuzzy match (e.g. 'reqtxt' -> 'requirements.txt')
    if is_subsequence(q, name_lower):
        return 250

    return 50


def is_subsequence(pattern: str, text: str) -> bool:
    """Check if pattern characters appear sequentially in text."""
    p_len, t_len = len(pattern), len(text)
    if p_len > t_len:
        return False
    p_idx, t_idx = 0, 0
    while p_idx < p_len and t_idx < t_len:
        if pattern[p_idx] == text[t_idx]:
            p_idx += 1
        t_idx += 1
    return p_idx == p_len


def rank_search_results(results: List[Dict[str, Any]], query_terms: List[str]) -> List[Dict[str, Any]]:
    """Sort search result dictionaries by relevance score and tie-breakers."""
    if not query_terms or not results:
        return results

    primary_term = query_terms[0]
    for item in results:
        score = calculate_match_score(item["name"], item["path"], primary_term)
        # Surcharge for directories if exact match
        if item.get("is_directory"):
            score += 10
        item["_score"] = score

    # Sort descending by score, ascending by path length (shorter paths first), descending by modified date
    results.sort(
        key=lambda x: (
            -x.get("_score", 0),
            len(x.get("path", "")),
            -x.get("modified_time", 0),
        )
    )
    return results
