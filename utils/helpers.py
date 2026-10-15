"""
OpenSearch by DeepLogic — Formatting and String Utilities
Provides human-readable byte sizes, date formatting, and path helper utilities.
"""

from __future__ import annotations
import os
import datetime
from typing import Optional


def format_bytes(num_bytes: Optional[int]) -> str:
    """Convert an integer byte count into a human-readable string (e.g. 2.4 MB, 14 KB)."""
    if num_bytes is None or num_bytes < 0:
        return "—"
    if num_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(num_bytes)
    unit_idx = 0
    while size >= 1024.0 and unit_idx < len(units) - 1:
        size /= 1024.0
        unit_idx += 1

    if unit_idx == 0:
        return f"{int(size)} B"
    elif size < 10.0:
        return f"{size:.1f} {units[unit_idx]}"
    else:
        return f"{size:.0f} {units[unit_idx]}"


def format_timestamp(timestamp: Optional[float]) -> str:
    """Format Unix epoch timestamp to standard user-friendly string (e.g., '15 Oct 2026 10:24 AM')."""
    if timestamp is None or timestamp <= 0:
        return "—"
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%d %b %Y %I:%M %p")
    except Exception:
        return "—"


def get_relative_date(timestamp: Optional[float]) -> str:
    """Format relative date such as Today, Yesterday, or exact date if older."""
    if timestamp is None or timestamp <= 0:
        return "—"
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
        now = datetime.datetime.now()
        diff = now - dt

        if diff.days == 0 and dt.date() == now.date():
            return f"Today, {dt.strftime('%I:%M %p')}"
        elif diff.days == 1 or (diff.days == 0 and dt.date() == (now - datetime.timedelta(days=1)).date()):
            return f"Yesterday, {dt.strftime('%I:%M %p')}"
        elif diff.days < 7:
            return dt.strftime("%a, %I:%M %p")
        else:
            return dt.strftime("%d %b %Y")
    except Exception:
        return "—"


def normalize_path(path: str) -> str:
    """Normalize path string with standard Windows backslashes and case preservation."""
    return os.path.normpath(path)
