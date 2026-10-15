"""
OpenSearch by DeepLogic — Real-time Filesystem Watcher
Uses watchdog to observe filesystem mutations (created, deleted, modified, moved)
and continuously keep the database synchronized.
"""

from __future__ import annotations
import os
import time
import queue
import threading
from typing import Dict, Any, Optional, Set
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    DirMovedEvent,
)
from database.repositories import file_repo
from utils.logger import logger


class IndexChangeHandler(FileSystemEventHandler):
    """Translates watchdog filesystem events into queue items."""

    def __init__(self, event_queue: queue.Queue) -> None:
        super().__init__()
        self.event_queue = event_queue

    def on_created(self, event) -> None:
        self.event_queue.put(("created", event.src_path, event.is_directory, None))

    def on_deleted(self, event) -> None:
        self.event_queue.put(("deleted", event.src_path, event.is_directory, None))

    def on_modified(self, event) -> None:
        if not event.is_directory:
            self.event_queue.put(("modified", event.src_path, False, None))

    def on_moved(self, event) -> None:
        self.event_queue.put(("moved", event.src_path, event.is_directory, event.dest_path))


class FilesystemWatcher:
    """Manages active filesystem observer watches across indexed drives."""

    def __init__(self, repo=None) -> None:
        self.repo = repo or file_repo
        self.observer: Optional[Observer] = None
        self.event_queue: queue.Queue = queue.Queue()
        self.watched_paths: Set[str] = set()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the observer and event processing worker thread."""
        if self._running:
            return
        self._running = True
        self.observer = Observer()
        self._worker_thread = threading.Thread(
            target=self._process_event_queue, name="WatcherWorker", daemon=True
        )
        self._worker_thread.start()
        self.observer.start()
        logger.info("FilesystemWatcher started.")

    def stop(self) -> None:
        """Stop watching and flush worker."""
        if not self._running:
            return
        self._running = False
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=2.0)
            except Exception:
                pass
        self.watched_paths.clear()
        logger.info("FilesystemWatcher stopped.")

    def watch_path(self, path: str) -> None:
        """Add a directory or drive root to active watches."""
        if not os.path.exists(path) or path in self.watched_paths:
            return
        if not self.observer:
            self.start()
        try:
            handler = IndexChangeHandler(self.event_queue)
            self.observer.schedule(handler, path, recursive=True)
            self.watched_paths.add(path)
            logger.info(f"Watching location for changes: {path}")
        except Exception as e:
            logger.warning(f"Could not watch path '{path}': {e}")

    def unwatch_all(self) -> None:
        """Remove all watches."""
        if self.observer:
            self.observer.unschedule_all()
        self.watched_paths.clear()

    def _process_event_queue(self) -> None:
        """Background loop consuming debounced filesystem change events."""
        while self._running:
            try:
                event_type, src_path, is_dir, dest_path = self.event_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                if event_type == "created":
                    self._handle_created(src_path, is_dir)
                elif event_type == "deleted":
                    self._handle_deleted(src_path, is_dir)
                elif event_type == "modified":
                    self._handle_modified(src_path)
                elif event_type == "moved":
                    self._handle_moved(src_path, dest_path, is_dir)
            except Exception as e:
                logger.debug(f"Error handling watcher event ({event_type}, {src_path}): {e}")
            finally:
                self.event_queue.task_done()

    def _handle_created(self, path: str, is_dir: bool) -> None:
        """Insert newly created file or directory."""
        if not os.path.exists(path):
            return
        try:
            stat_res = os.stat(path, follow_symlinks=False)
            name = os.path.basename(path)
            parent = os.path.dirname(path)
            ext = "" if is_dir else (name.rsplit(".", 1)[-1].lower() if "." in name else "")
            size = stat_res.st_size if not is_dir else 0
            drive = os.path.splitdrive(path)[0].upper()

            record = (
                name,
                path,
                parent,
                ext,
                size,
                stat_res.st_ctime,
                stat_res.st_mtime,
                stat_res.st_atime,
                1 if is_dir else 0,
                1 if name.startswith(".") else 0,
                0,
                drive,
            )
            self.repo.insert_batch([record])
        except (PermissionError, FileNotFoundError, OSError):
            pass

    def _handle_deleted(self, path: str, is_dir: bool) -> None:
        """Remove deleted file or directory subtree from index."""
        if is_dir:
            self.repo.delete_by_prefix(path)
        else:
            self.repo.delete_by_path(path)

    def _handle_modified(self, path: str) -> None:
        """Update file size and timestamps."""
        if not os.path.isfile(path):
            return
        try:
            stat_res = os.stat(path, follow_symlinks=False)
            self.repo.update_file_metadata(
                path=path,
                size=stat_res.st_size,
                modified_time=stat_res.st_mtime,
                accessed_time=stat_res.st_atime,
            )
        except (PermissionError, FileNotFoundError, OSError):
            pass

    def _handle_moved(self, old_path: str, new_path: Optional[str], is_dir: bool) -> None:
        """Handle file or folder rename / move."""
        if not new_path:
            return
        name = os.path.basename(new_path)
        parent = os.path.dirname(new_path)
        if is_dir:
            self.repo.rename_directory(old_path, new_path, name, parent)
        else:
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            self.repo.rename_file(old_path, new_path, name, parent, ext)


filesystem_watcher = FilesystemWatcher()
