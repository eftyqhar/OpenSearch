"""
OpenSearch by DeepLogic — Indexing Worker & Orchestration
Coordinates background filesystem scanning, state management (idle, indexing, paused, complete),
progress notification, and watcher lifecycle.
"""

from __future__ import annotations
import os
import time
import threading
from typing import List, Callable, Optional, Dict, Any
from indexing.scanner import FilesystemScanner
from indexing.watcher import filesystem_watcher
from indexing.drive_manager import drive_manager
from database.repositories import file_repo
from config.settings import settings
from utils.logger import logger


class IndexWorker:
    """Manages background directory traversal and indexing tasks."""

    def __init__(self, repo=None, watcher=None) -> None:
        self.repo = repo or file_repo
        self.watcher = watcher or filesystem_watcher
        self._thread: Optional[threading.Thread] = None
        self._pause_event = threading.Event()
        self._pause_event.set()  # Unpaused initially
        self._stop_event = threading.Event()

        self.status = "idle"  # idle, indexing, paused, complete
        self.current_folder = ""
        self.items_indexed_this_session = 0
        self.on_progress: Optional[Callable[[Dict[str, Any]], None]] = None

    @property
    def is_indexing(self) -> bool:
        return self.status == "indexing"

    @property
    def is_paused(self) -> bool:
        return self.status == "paused"

    def pause(self) -> None:
        """Pause ongoing indexing."""
        if self.status == "indexing":
            self._pause_event.clear()
            self.status = "paused"
            logger.info("Indexing paused by user.")
            self._notify_progress()

    def resume(self) -> None:
        """Resume paused indexing."""
        if self.status == "paused":
            self._pause_event.set()
            self.status = "indexing"
            logger.info("Indexing resumed by user.")
            self._notify_progress()

    def toggle_pause(self) -> None:
        """Toggle pause/resume state."""
        if self.is_paused:
            self.resume()
        elif self.is_indexing:
            self.pause()

    def stop(self) -> None:
        """Signal worker thread to terminate immediately."""
        self._stop_event.set()
        self._pause_event.set()  # Unblock if paused
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self.status = "idle"

    def start_indexing(self, locations: Optional[List[str]] = None) -> None:
        """Initiate background indexing for specified or configured locations."""
        if self._thread and self._thread.is_alive():
            logger.warning("Indexing already running.")
            return

        self._stop_event.clear()
        self._pause_event.set()
        self.status = "indexing"
        self.items_indexed_this_session = 0

        target_locations = locations or self._get_target_locations()
        self._thread = threading.Thread(
            target=self._run_indexing,
            args=(target_locations,),
            name="OpenSearchIndexWorker",
            daemon=True,
        )
        self._thread.start()

    def rebuild_index(self) -> None:
        """Stop watcher, wipe database records, and run a fresh crawl."""
        logger.info("Starting complete index rebuild...")
        self.stop()
        self.watcher.stop()
        self.repo.clear_all()
        self.start_indexing()

    def _get_target_locations(self) -> List[str]:
        """Determine locations to index based on settings and available drives."""
        configured_drives = settings.get("indexed_drives", ["C:"])
        available_drives = drive_manager.get_available_drives()
        avail_letters = {d.letter.upper(): d for d in available_drives}

        locations: List[str] = []
        for drv in configured_drives:
            drv_upper = drv.upper()
            if drv_upper in avail_letters:
                locations.append(avail_letters[drv_upper].root)

        # Append custom configured locations
        custom_locations = settings.get("indexed_locations", [])
        for loc in custom_locations:
            if os.path.exists(loc) and loc not in locations:
                locations.append(loc)

        # Fallback to C:\ if empty
        if not locations:
            locations = ["C:\\"]

        return locations

    def _run_indexing(self, locations: List[str]) -> None:
        """Main indexing execution thread."""
        logger.info(f"Background indexing started for: {locations}")
        scanner = FilesystemScanner(
            batch_size=4000,
            excluded_patterns=settings.get("excluded_paths", []),
            index_hidden=settings.get("index_hidden_files", True),
            index_system=settings.get("index_system_files", False),
        )

        for loc in locations:
            if self._stop_event.is_set():
                break

            drive_letter = os.path.splitdrive(loc)[0].upper()
            logger.info(f"Crawling location: {loc}")

            def on_folder_change(folder: str) -> None:
                self.current_folder = folder
                self._notify_progress()

            try:
                for batch in scanner.scan_directory(
                    root_path=loc,
                    drive_letter=drive_letter,
                    should_pause=lambda: not self._pause_event.is_set(),
                    should_stop=lambda: self._stop_event.is_set(),
                    on_folder_change=on_folder_change,
                ):
                    inserted = self.repo.insert_batch(batch)
                    self.items_indexed_this_session += inserted
                    self._notify_progress()

                # Register path with watcher for continuous real-time synchronization
                if not self._stop_event.is_set():
                    self.watcher.watch_path(loc)

                    # Update location meta
                    stats = self.repo.get_stats()
                    self.repo.update_location_meta(
                        location=loc,
                        drive=drive_letter,
                        total_files=stats["total_files"],
                        total_folders=stats["total_folders"],
                        total_size=stats["total_size"],
                        status="Indexed",
                    )
            except Exception as e:
                logger.error(f"Error during crawl of {loc}: {e}")

        # Indexing completed
        if not self._stop_event.is_set():
            self.status = "complete"
            self.current_folder = ""
            logger.info(f"Indexing complete. Indexed {self.items_indexed_this_session} items.")
            self._notify_progress()

    def _notify_progress(self) -> None:
        """Invoke progress callback if registered."""
        if not self.on_progress:
            return
        stats = self.repo.get_stats()
        progress_data = {
            "status": self.status,
            "current_folder": self.current_folder,
            "session_items": self.items_indexed_this_session,
            "total_items": stats["total_items"],
            "total_files": stats["total_files"],
            "total_folders": stats["total_folders"],
            "total_size": stats["total_size"],
        }
        try:
            self.on_progress(progress_data)
        except Exception as e:
            logger.debug(f"Progress callback error: {e}")


index_worker = IndexWorker()
