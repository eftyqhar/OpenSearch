"""
OpenSearch by DeepLogic — Path & Directory Management
Handles portable mode detection, local appdata resolution, logs, cache, and database locations.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Check if the application is running as a compiled PyInstaller executable."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_app_root() -> Path:
    """Return the application installation or source root directory."""
    if is_frozen():
        return Path(sys.executable).parent.resolve()
    return Path(__file__).resolve().parent.parent


def is_portable_mode() -> bool:
    """Check if portable mode is active (flag file or local data folder present)."""
    app_root = get_app_root()
    portable_flag = app_root / "portable.flag"
    local_data_dir = app_root / "data"
    return portable_flag.exists() or local_data_dir.is_dir()


def get_data_dir() -> Path:
    """
    Get the persistent storage directory for OpenSearch.
    - If portable mode: <AppRoot>/data/
    - Otherwise: %LOCALAPPDATA%/OpenSearch/
    """
    if is_portable_mode():
        data_dir = get_app_root() / "data"
    else:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            local_app_data = str(Path.home() / "AppData" / "Local")
        data_dir = Path(local_app_data) / "OpenSearch"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_database_path() -> Path:
    """Get the SQLite database file path."""
    return get_data_dir() / "index.db"


def get_config_path() -> Path:
    """Get the config.json file path."""
    return get_data_dir() / "config.json"


def get_logs_dir() -> Path:
    """Get the logs directory."""
    logs_dir = get_data_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_cache_dir() -> Path:
    """Get the cache directory for thumbnails and temporary data."""
    cache_dir = get_data_dir() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_assets_dir() -> Path:
    """Get the assets directory containing icons and images."""
    if is_frozen():
        base_path = Path(getattr(sys, "_MEIPASS", sys.executable))
        assets_path = base_path / "assets"
        if assets_path.exists():
            return assets_path
    return get_app_root() / "assets"
