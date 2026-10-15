"""
OpenSearch by DeepLogic — Query Parser & Tokenizer
Transforms user search input into a structured query AST supporting
operators, filters (type:, size:, modified:, drive:, path:), wildcards, and quotes.
"""

from __future__ import annotations
import re
import time
import datetime
from dataclasses import dataclass, field
from typing import List, Set, Optional
from core.metadata import CATEGORIES


@dataclass
class SearchQuery:
    """Structured representation of a parsed search query."""
    raw: str = ""
    terms: List[str] = field(default_factory=list)
    phrases: List[str] = field(default_factory=list)
    exclude_terms: List[str] = field(default_factory=list)
    extensions: Set[str] = field(default_factory=set)
    categories: Set[str] = field(default_factory=set)
    is_directory: Optional[bool] = None
    drive: Optional[str] = None
    path_contains: Optional[str] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    min_modified: Optional[float] = None
    max_modified: Optional[float] = None
    wildcard_pattern: Optional[str] = None

    def is_empty(self) -> bool:
        """Check if query contains no constraints or search terms."""
        return not (
            self.terms
            or self.phrases
            or self.exclude_terms
            or self.extensions
            or self.categories
            or self.is_directory is not None
            or self.drive
            or self.path_contains
            or self.min_size is not None
            or self.max_size is not None
            or self.min_modified is not None
            or self.wildcard_pattern
        )


class QueryParser:
    """Parses search query strings into SearchQuery AST objects."""

    _SIZE_MULTIPLIERS = {
        "b": 1,
        "k": 1024,
        "kb": 1024,
        "m": 1024 * 1024,
        "mb": 1024 * 1024,
        "g": 1024 * 1024 * 1024,
        "gb": 1024 * 1024 * 1024,
        "t": 1024 * 1024 * 1024 * 1024,
        "tb": 1024 * 1024 * 1024 * 1024,
    }

    @classmethod
    def parse(cls, query_str: str) -> SearchQuery:
        """Parse raw query string into SearchQuery."""
        query = SearchQuery(raw=query_str.strip())
        if not query_str.strip():
            return query

        # Extract quoted phrases
        raw = query_str
        quotes_pattern = r'"([^"]+)"'
        phrases = re.findall(quotes_pattern, raw)
        query.phrases = [p.strip() for p in phrases if p.strip()]
        # Remove quoted phrases from remainder
        raw = re.sub(quotes_pattern, " ", raw)

        # Tokenize by whitespace
        tokens = [t.strip() for t in raw.split() if t.strip()]

        for token in tokens:
            lower_token = token.lower()

            # Negation: -term or !term
            if (token.startswith("-") or token.startswith("!")) and len(token) > 1 and ":" not in token:
                query.exclude_terms.append(token[1:].lower())
                continue

            # Type filter: type:pdf or type:document
            if lower_token.startswith("type:"):
                val = lower_token[5:].strip()
                cls._handle_type_filter(query, val)
                continue

            # Extension filter: ext:pdf or *.pdf
            if lower_token.startswith("ext:"):
                val = lower_token[4:].strip().lstrip(".")
                if val:
                    query.extensions.add(val)
                continue

            if lower_token.startswith("*."):
                val = lower_token[2:].strip()
                if val and "*" not in val and "?" not in val:
                    query.extensions.add(val)
                else:
                    query.wildcard_pattern = lower_token
                continue

            # Drive filter: drive:C or drive:D:
            if lower_token.startswith("drive:"):
                val = lower_token[6:].strip().upper()
                if val:
                    query.drive = val[0] + ":"
                continue

            # Path filter: path:D:\Projects or path:Development
            if lower_token.startswith("path:"):
                val = token[5:].strip()
                if val:
                    query.path_contains = val
                continue

            # Size filter: size:>1GB or size:<10MB or size:1MB..50MB
            if lower_token.startswith("size:"):
                val = lower_token[5:].strip()
                cls._handle_size_filter(query, val)
                continue

            # Modified date filter: modified:today or modified:week
            if lower_token.startswith("modified:") or lower_token.startswith("date:"):
                val = lower_token.split(":", 1)[1].strip()
                cls._handle_modified_filter(query, val)
                continue

            # Wildcard token (* or ?)
            if "*" in token or "?" in token:
                query.wildcard_pattern = token
                continue

            # Regular search term
            query.terms.append(token)

        return query

    @classmethod
    def _handle_type_filter(cls, query: SearchQuery, val: str) -> None:
        """Handle type: filter values."""
        if val in ("folder", "folders", "dir", "directory"):
            query.is_directory = True
        elif val in ("file", "files"):
            query.is_directory = False
        elif val in CATEGORIES:
            query.categories.add(val)
        else:
            # Check if value is a known extension like type:pdf
            query.extensions.add(val.lstrip("."))

    @classmethod
    def _parse_size_value(cls, val_str: str) -> Optional[int]:
        """Convert a size string like '1.5GB' or '500KB' into integer bytes."""
        m = re.match(r"^(\d+(?:\.\d+)?)\s*([a-z]+)?$", val_str.lower())
        if not m:
            return None
        num = float(m.group(1))
        unit = m.group(2) or "b"
        multiplier = cls._SIZE_MULTIPLIERS.get(unit, 1)
        return int(num * multiplier)

    @classmethod
    def _handle_size_filter(cls, query: SearchQuery, val: str) -> None:
        """Handle size:>10MB, size:<1GB, or size:10MB..50MB."""
        if ".." in val:
            parts = val.split("..", 1)
            min_s = cls._parse_size_value(parts[0])
            max_s = cls._parse_size_value(parts[1])
            if min_s is not None:
                query.min_size = min_s
            if max_s is not None:
                query.max_size = max_s
        elif val.startswith(">="):
            query.min_size = cls._parse_size_value(val[2:])
        elif val.startswith(">"):
            query.min_size = cls._parse_size_value(val[1:])
        elif val.startswith("<="):
            query.max_size = cls._parse_size_value(val[2:])
        elif val.startswith("<"):
            query.max_size = cls._parse_size_value(val[1:])
        else:
            sz = cls._parse_size_value(val)
            if sz is not None:
                query.min_size = sz

    @classmethod
    def _handle_modified_filter(cls, query: SearchQuery, val: str) -> None:
        """Handle date filters such as today, yesterday, week, month, year."""
        now = datetime.datetime.now()
        start_of_today = datetime.datetime(now.year, now.month, now.day)

        if val in ("today", "now"):
            query.min_modified = start_of_today.timestamp()
        elif val == "yesterday":
            start_of_yesterday = start_of_today - datetime.timedelta(days=1)
            query.min_modified = start_of_yesterday.timestamp()
            query.max_modified = start_of_today.timestamp()
        elif val in ("week", "7days", "past_week"):
            start_of_week = start_of_today - datetime.timedelta(days=7)
            query.min_modified = start_of_week.timestamp()
        elif val in ("month", "30days", "past_month"):
            start_of_month = start_of_today - datetime.timedelta(days=30)
            query.min_modified = start_of_month.timestamp()
        elif val in ("year", "365days", "past_year"):
            start_of_year = start_of_today - datetime.timedelta(days=365)
            query.min_modified = start_of_year.timestamp()
