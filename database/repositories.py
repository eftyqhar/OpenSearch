"""
OpenSearch by DeepLogic — Database Repositories
High-performance batch operations, path mutations, stats queries, and deletions.
"""

from __future__ import annotations
import os
import time
from typing import List, Tuple, Dict, Any, Optional
from database.database import db_manager
from utils.logger import logger


class FileRepository:
    """Handles all data access, batched writes, and queries for indexed files."""

    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db or db_manager

    def insert_batch(self, records: List[Tuple]) -> int:
        """
        Batch insert file records.
        Record tuple structure:
        (name, path, parent_path, extension, size, created_time, modified_time,
         accessed_time, is_directory, is_hidden, is_system, drive)
        """
        if not records:
            return 0
        conn = self.db.get_connection()
        sql = """
        INSERT OR REPLACE INTO files (
            name, path, parent_path, extension, size,
            created_time, modified_time, accessed_time,
            is_directory, is_hidden, is_system, drive
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.executemany(sql, records)
            conn.execute("COMMIT;")
            return len(records)
        except Exception as e:
            conn.execute("ROLLBACK;")
            logger.error(f"Error inserting batch of {len(records)} records: {e}")
            raise

    def delete_by_path(self, path: str) -> None:
        """Delete an exact file or folder path."""
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute("DELETE FROM files WHERE path = ?", (path,))
            conn.execute("COMMIT;")
        except Exception as e:
            conn.execute("ROLLBACK;")
            logger.error(f"Error deleting path '{path}': {e}")

    def delete_by_prefix(self, prefix: str) -> None:
        """Delete a directory and all of its recursive child items."""
        norm_prefix = prefix.rstrip("\\")
        pattern = norm_prefix + "\\%"
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute("DELETE FROM files WHERE path = ? OR path LIKE ?", (norm_prefix, pattern))
            conn.execute("COMMIT;")
        except Exception as e:
            conn.execute("ROLLBACK;")
            logger.error(f"Error deleting by prefix '{prefix}': {e}")

    def rename_file(self, old_path: str, new_path: str, name: str, parent: str, ext: str) -> None:
        """Rename or move a single file."""
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute(
                """
                UPDATE files
                SET path = ?, name = ?, parent_path = ?, extension = ?
                WHERE path = ?
                """,
                (new_path, name, parent, ext, old_path),
            )
            conn.execute("COMMIT;")
        except Exception as e:
            conn.execute("ROLLBACK;")
            logger.error(f"Error renaming file '{old_path}' to '{new_path}': {e}")

    def rename_directory(self, old_path: str, new_path: str, name: str, parent: str) -> None:
        """Rename a directory and recursively update paths of all nested items."""
        old_norm = old_path.rstrip("\\")
        new_norm = new_path.rstrip("\\")
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            # Update directory record itself
            conn.execute(
                """
                UPDATE files
                SET path = ?, name = ?, parent_path = ?
                WHERE path = ?
                """,
                (new_norm, name, parent, old_norm),
            )
            # Update child items (replace path prefix)
            old_prefix = old_norm + "\\"
            old_len = len(old_prefix)
            new_prefix = new_norm + "\\"

            cursor = conn.cursor()
            cursor.execute("SELECT id, path, parent_path FROM files WHERE path LIKE ?", (old_prefix + "%",))
            rows = cursor.fetchall()

            updates = []
            for row in rows:
                child_id = row["id"]
                child_path = row["path"]
                child_parent = row["parent_path"]

                rel_path = child_path[old_len:]
                updated_path = new_prefix + rel_path
                updated_parent = (
                    new_norm if child_parent == old_norm else new_prefix + child_parent[old_len:]
                )
                updates.append((updated_path, updated_parent, child_id))

            if updates:
                conn.executemany("UPDATE files SET path = ?, parent_path = ? WHERE id = ?", updates)

            conn.execute("COMMIT;")
        except Exception as e:
            conn.execute("ROLLBACK;")
            logger.error(f"Error renaming directory '{old_path}' to '{new_path}': {e}")

    def update_file_metadata(
        self, path: str, size: int, modified_time: float, accessed_time: float
    ) -> None:
        """Update size and timestamp attributes when a file is modified."""
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute(
                """
                UPDATE files
                SET size = ?, modified_time = ?, accessed_time = ?
                WHERE path = ?
                """,
                (size, modified_time, accessed_time, path),
            )
            conn.execute("COMMIT;")
        except Exception as e:
            conn.execute("ROLLBACK;")
            logger.error(f"Error updating metadata for '{path}': {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Retrieve total files, folders, and cumulative size."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(CASE WHEN is_directory = 0 THEN 1 END) as total_files,
                COUNT(CASE WHEN is_directory = 1 THEN 1 END) as total_folders,
                COALESCE(SUM(CASE WHEN is_directory = 0 THEN size ELSE 0 END), 0) as total_size
            FROM files;
            """
        )
        row = cursor.fetchone()
        return {
            "total_files": row["total_files"] if row else 0,
            "total_folders": row["total_folders"] if row else 0,
            "total_size": row["total_size"] if row else 0,
            "total_items": (row["total_files"] + row["total_folders"]) if row else 0,
        }

    def update_location_meta(
        self, location: str, drive: str, total_files: int, total_folders: int, total_size: int, status: str
    ) -> None:
        """Update indexed location tracking metadata."""
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute(
                """
                INSERT OR REPLACE INTO locations_meta (
                    location, drive, total_files, total_folders, total_size, status, last_scanned
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (location, drive, total_files, total_folders, total_size, status, time.time()),
            )
            conn.execute("COMMIT;")
        except Exception as e:
            conn.execute("ROLLBACK;")
            logger.error(f"Error updating location meta for {location}: {e}")

    def get_locations(self) -> List[Dict[str, Any]]:
        """Retrieve all tracked locations and their indexing status."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM locations_meta ORDER BY location ASC;")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

    def clear_drive(self, drive: str) -> None:
        """Remove all indexed entries for a specific drive."""
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute("DELETE FROM files WHERE drive = ?", (drive,))
            conn.execute("DELETE FROM locations_meta WHERE drive = ?", (drive,))
            conn.execute("COMMIT;")
        except Exception as e:
            conn.execute("ROLLBACK;")
            logger.error(f"Error clearing drive {drive}: {e}")

    def clear_all(self) -> None:
        """Clear the entire database for full reindexing."""
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute("DELETE FROM files;")
            conn.execute("DELETE FROM locations_meta;")
            conn.execute("COMMIT;")
        except Exception as e:
            conn.execute("ROLLBACK;")
            logger.error(f"Error clearing all index data: {e}")


file_repo = FileRepository()
