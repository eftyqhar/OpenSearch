"""
OpenSearch by DeepLogic — Search Engine Execution
Executes structured SQL / FTS queries, applies filters, coordinates query IDs for cancellation,
and measures search latency with microsecond accuracy.
"""

from __future__ import annotations
import time
import fnmatch
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
from database.database import db_manager
from core.query_parser import QueryParser, SearchQuery
from core.ranking import rank_search_results
from core.metadata import CATEGORIES, get_type_description
from utils.logger import logger


@dataclass
class SearchResult:
    """Encapsulates the response of a search operation."""
    query_id: int
    items: List[Dict[str, Any]]
    total_count: int
    execution_time_ms: float
    is_cancelled: bool = False


class SearchEngine:
    """Core search coordinator with query cancellation and index querying."""

    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db or db_manager
        self._current_query_id = 0

    def next_query_id(self) -> int:
        """Increment and return the next generation query ID."""
        self._current_query_id += 1
        return self._current_query_id

    @property
    def current_query_id(self) -> int:
        return self._current_query_id

    def search(
        self,
        query_str: str,
        query_id: Optional[int] = None,
        max_results: int = 1000,
        sort_by: str = "score",
        sort_asc: bool = True,
        category_filter: Optional[str] = None,  # From quick filter / tabs
    ) -> SearchResult:
        """
        Execute an ultra-fast search against the SQLite index.
        """
        start_time = time.perf_counter()
        if query_id is None:
            query_id = self.next_query_id()

        parsed_query = QueryParser.parse(query_str)
        if category_filter and category_filter != "all":
            if category_filter in ("files", "file"):
                parsed_query.is_directory = False
            elif category_filter in ("folders", "folder"):
                parsed_query.is_directory = True
            elif category_filter in CATEGORIES:
                parsed_query.categories.add(category_filter)

        # Build SQL Query & Parameters
        where_clauses: List[str] = []
        params: List[Any] = []

        # 1. Drive filter
        if parsed_query.drive:
            where_clauses.append("drive = ?")
            params.append(parsed_query.drive)

        # 2. Directory or File filter
        if parsed_query.is_directory is not None:
            where_clauses.append("is_directory = ?")
            params.append(1 if parsed_query.is_directory else 0)

        # 3. Path contains filter
        if parsed_query.path_contains:
            where_clauses.append("path LIKE ?")
            params.append(f"%{parsed_query.path_contains}%")

        # 4. Size bounds
        if parsed_query.min_size is not None:
            where_clauses.append("size >= ?")
            params.append(parsed_query.min_size)
        if parsed_query.max_size is not None:
            where_clauses.append("size <= ?")
            params.append(parsed_query.max_size)

        # 5. Modified date bounds
        if parsed_query.min_modified is not None:
            where_clauses.append("modified_time >= ?")
            params.append(parsed_query.min_modified)
        if parsed_query.max_modified is not None:
            where_clauses.append("modified_time <= ?")
            params.append(parsed_query.max_modified)

        # 6. Extensions and categories
        all_extensions: Set[str] = set(parsed_query.extensions)
        for cat in parsed_query.categories:
            if cat in CATEGORIES:
                all_extensions.update(CATEGORIES[cat])

        if all_extensions:
            placeholders = ",".join("?" for _ in all_extensions)
            where_clauses.append(f"extension IN ({placeholders})")
            params.extend(list(all_extensions))

        # 7. Wildcard pattern (* or ?)
        if parsed_query.wildcard_pattern:
            sql_wildcard = parsed_query.wildcard_pattern.replace("*", "%").replace("?", "_")
            where_clauses.append("name LIKE ?")
            params.append(sql_wildcard)

        # 8. Text search terms
        for term in parsed_query.terms:
            where_clauses.append("name LIKE ?")
            params.append(f"%{term}%")

        for phrase in parsed_query.phrases:
            where_clauses.append("name LIKE ?")
            params.append(f"%{phrase}%")

        # 9. Exclude terms
        for ex in parsed_query.exclude_terms:
            where_clauses.append("name NOT LIKE ?")
            params.append(f"%{ex}%")

        # Construct WHERE statement
        where_stmt = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Check cancellation before database query
        if query_id < self._current_query_id:
            return SearchResult(query_id, [], 0, 0.0, is_cancelled=True)

        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Count total matching records
        count_sql = f"SELECT COUNT(*) FROM files {where_stmt};"
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]

        # Fetch records
        order_by = "is_directory DESC, name COLLATE NOCASE ASC"
        if sort_by == "size":
            order_by = f"size {'ASC' if sort_asc else 'DESC'}"
        elif sort_by == "modified":
            order_by = f"modified_time {'ASC' if sort_asc else 'DESC'}"
        elif sort_by == "name":
            order_by = f"name COLLATE NOCASE {'ASC' if sort_asc else 'DESC'}"

        select_sql = f"""
        SELECT id, name, path, parent_path, extension, size,
               created_time, modified_time, is_directory, drive
        FROM files
        {where_stmt}
        ORDER BY {order_by}
        LIMIT ?;
        """
        cursor.execute(select_sql, params + [max_results])
        rows = cursor.fetchall()

        # Check cancellation after database query
        if query_id < self._current_query_id:
            return SearchResult(query_id, [], 0, 0.0, is_cancelled=True)

        items: List[Dict[str, Any]] = []
        for r in rows:
            is_dir = bool(r["is_directory"])
            ext = r["extension"]
            item_dict = {
                "id": r["id"],
                "name": r["name"],
                "path": r["path"],
                "parent_path": r["parent_path"],
                "extension": ext,
                "size": r["size"],
                "created_time": r["created_time"],
                "modified_time": r["modified_time"],
                "is_directory": is_dir,
                "drive": r["drive"],
                "type_desc": get_type_description(ext, is_dir),
            }
            items.append(item_dict)

        # Rank results if sorted by relevance and terms were supplied
        if sort_by == "score" and parsed_query.terms:
            items = rank_search_results(items, parsed_query.terms)

        execution_time_ms = (time.perf_counter() - start_time) * 1000.0

        return SearchResult(
            query_id=query_id,
            items=items,
            total_count=total_count,
            execution_time_ms=execution_time_ms,
            is_cancelled=(query_id < self._current_query_id),
        )


search_engine = SearchEngine()
