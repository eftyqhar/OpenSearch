"""
OpenSearch by DeepLogic — Fast Filesystem Scanner
Uses os.scandir() with stat caching, exclusion matching, and chunk batching.
"""

from __future__ import annotations
import os
import time
from typing import Generator, List, Tuple, Callable, Optional, Set
from utils.logger import logger


class FilesystemScanner:
    """Recursively crawls directories using os.scandir() with chunked batching."""

    def __init__(
        self,
        batch_size: int = 5000,
        excluded_patterns: Optional[List[str]] = None,
        index_hidden: bool = True,
        index_system: bool = False,
    ) -> None:
        self.batch_size = batch_size
        self.excluded_patterns = [p.lower() for p in (excluded_patterns or [])]
        self.index_hidden = index_hidden
        self.index_system = index_system

    def is_excluded(self, path: str) -> bool:
        """Check if path matches any exclusion rule."""
        p_lower = path.lower()
        for pattern in self.excluded_patterns:
            if pattern in p_lower:
                return True
        return False

    def scan_directory(
        self,
        root_path: str,
        drive_letter: str,
        should_pause: Optional[Callable[[], bool]] = None,
        should_stop: Optional[Callable[[], bool]] = None,
        on_folder_change: Optional[Callable[[str], None]] = None,
    ) -> Generator[List[Tuple], None, None]:
        """
        Scan a root directory yielding chunks of file tuples.
        Tuple format:
        (name, path, parent_path, extension, size, created_time, modified_time,
         accessed_time, is_directory, is_hidden, is_system, drive)
        """
        stack = [root_path]
        batch: List[Tuple] = []

        while stack:
            if should_stop and should_stop():
                break

            # Handle pause state
            while should_pause and should_pause():
                if should_stop and should_stop():
                    return
                time.sleep(0.2)

            current_dir = stack.pop()
            if self.is_excluded(current_dir):
                continue

            if on_folder_change:
                on_folder_change(current_dir)

            try:
                with os.scandir(current_dir) as entries:
                    for entry in entries:
                        if should_stop and should_stop():
                            break

                        entry_name = entry.name
                        # Check hidden files
                        is_hidden = entry_name.startswith(".")
                        if is_hidden and not self.index_hidden:
                            continue

                        entry_path = entry.path

                        try:
                            # Use follow_symlinks=False to avoid loops and re-use WIN32_FIND_DATA
                            is_dir = entry.is_dir(follow_symlinks=False)
                            stat_res = entry.stat(follow_symlinks=False)
                            size = stat_res.st_size if not is_dir else 0
                            ctime = stat_res.st_ctime
                            mtime = stat_res.st_mtime
                            atime = stat_res.st_atime
                        except (PermissionError, FileNotFoundError, OSError):
                            continue

                        # Extract extension (empty for folders)
                        if is_dir:
                            ext = ""
                        else:
                            dot_pos = entry_name.rfind(".")
                            ext = entry_name[dot_pos + 1 :].lower() if dot_pos > 0 else ""

                        is_system = False  # By default standard file

                        batch.append(
                            (
                                entry_name,
                                entry_path,
                                current_dir,
                                ext,
                                size,
                                ctime,
                                mtime,
                                atime,
                                1 if is_dir else 0,
                                1 if is_hidden else 0,
                                1 if is_system else 0,
                                drive_letter,
                            )
                        )

                        if len(batch) >= self.batch_size:
                            yield batch
                            batch = []

                        # If directory, add to stack for recursive exploration
                        if is_dir and not self.is_excluded(entry_path):
                            stack.append(entry_path)

            except (PermissionError, FileNotFoundError, OSError) as e:
                # Log and continue scanning remaining directories
                continue

        # Yield any remaining items in final batch
        if batch:
            yield batch
