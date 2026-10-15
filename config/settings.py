"""
OpenSearch by DeepLogic — Persistent Settings Manager
Loads, modifies, and saves application settings safely in JSON format.
"""

from __future__ import annotations
import json
import threading
from typing import Any, Dict
from config.defaults import DEFAULT_CONFIG
from utils.paths import get_config_path
from utils.logger import logger


class SettingsManager:
    """Thread-safe configuration manager."""

    _instance: Optional[SettingsManager] = None
    _lock = threading.Lock()

    def __new__(cls) -> SettingsManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._config_file = get_config_path()
        self._data: Dict[str, Any] = {}
        self._mutex = threading.RLock()
        self.load()
        self._initialized = True

    def load(self) -> None:
        """Load configuration from disk, applying defaults for missing keys."""
        with self._mutex:
            self._data = dict(DEFAULT_CONFIG)
            if self._config_file.is_file():
                try:
                    with open(self._config_file, "r", encoding="utf-8") as f:
                        disk_data = json.load(f)
                    if isinstance(disk_data, dict):
                        self._data.update(disk_data)
                except Exception as e:
                    logger.error(f"Failed to load config from {self._config_file}: {e}")
            else:
                self.save()

    def save(self) -> None:
        """Persist current configuration to disk safely."""
        with self._mutex:
            try:
                temp_file = self._config_file.with_suffix(".tmp")
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=4)
                temp_file.replace(self._config_file)
            except Exception as e:
                logger.error(f"Failed to save config to {self._config_file}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        with self._mutex:
            return self._data.get(key, DEFAULT_CONFIG.get(key, default))

    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        """Update a configuration value."""
        with self._mutex:
            self._data[key] = value
            if auto_save:
                self.save()

    def get_all(self) -> Dict[str, Any]:
        """Return a copy of all configuration settings."""
        with self._mutex:
            return dict(self._data)


settings = SettingsManager()
