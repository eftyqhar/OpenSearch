"""
OpenSearch by DeepLogic — SQLite Database Connection & Transaction Manager
Configures WAL mode, aggressive memory caching, and thread-local connections.
"""

from __future__ import annotations
import sqlite3
import threading
from pathlib import Path
from typing import Optional
from database.schema import SCHEMA_SQL
from utils.paths import get_database_path
from utils.logger import logger


class DatabaseManager:
    """Thread-safe SQLite connection manager with WAL mode and high-performance PRAGMAs."""

    _instance: Optional[DatabaseManager] = None
    _init_lock = threading.Lock()

    def __new__(cls, db_path: Optional[Path] = None) -> DatabaseManager:
        if db_path is not None:
            # Custom instance for testing or dedicated isolated database
            inst = super().__new__(cls)
            inst._initialized = False
            return inst

        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if getattr(self, "_initialized", False):
            return
        self.db_path = db_path or get_database_path()
        self._local = threading.local()
        self.init_database()
        self._initialized = True

    def get_connection(self) -> sqlite3.Connection:
        """Retrieve or create thread-local database connection."""
        conn = getattr(self._local, "connection", None)
        if conn is None:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False,
                isolation_level=None,  # Autocommit mode; transactions managed explicitly
            )
            conn.row_factory = sqlite3.Row
            # Configure high-performance SQLite PRAGMAs
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA synchronous = NORMAL;")
            cursor.execute("PRAGMA cache_size = -64000;")  # 64 MB cache
            cursor.execute("PRAGMA temp_store = MEMORY;")
            cursor.execute("PRAGMA mmap_size = 268435456;")  # 256 MB memory-mapped I/O
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.close()
            self._local.connection = conn
        return conn

    def init_database(self) -> None:
        """Initialize schema, tables, indexes, and triggers."""
        try:
            conn = self.get_connection()
            conn.executescript(SCHEMA_SQL)
            logger.info(f"Database initialized successfully at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def checkpoint_wal(self) -> None:
        """Execute a passive WAL checkpoint to truncate wal log file."""
        try:
            conn = self.get_connection()
            conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
        except Exception as e:
            logger.warning(f"WAL checkpoint warning: {e}")

    def close(self) -> None:
        """Close current thread connection."""
        conn = getattr(self._local, "connection", None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
            self._local.connection = None


db_manager = DatabaseManager()
