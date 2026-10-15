"""
OpenSearch by DeepLogic — Default Configuration Values
Defines application defaults, exclusion patterns, and default theme palettes.
"""

from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    # General
    "theme": "dark",
    "language": "English",
    "startup": False,
    "minimize_to_tray": True,
    "close_to_tray": False,
    "check_updates": True,

    # Search
    "search_debounce_ms": 150,
    "max_results": 1000,
    "match_case": False,
    "fuzzy_search": True,
    "default_sort_col": "name",
    "default_sort_asc": True,
    "view_mode": "details",  # 'details', 'list', 'preview'

    # Indexing
    "indexed_drives": ["C:"],
    "indexed_locations": [],
    "excluded_paths": [
        r"$Recycle.Bin",
        r"System Volume Information",
        r"Windows\WinSxS",
        r"AppData\Local\Temp",
        r"node_modules",
        r".git",
    ],
    "index_hidden_files": True,
    "index_system_files": False,
    "index_removable_drives": False,
    "worker_threads": 0,  # 0 = auto

    # Shortcuts
    "global_hotkey": "<Control-Shift-space>",
    "enable_global_hotkey": True,
}
