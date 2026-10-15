"""
OpenSearch by DeepLogic — Primary Application Window
Integrates the sidebar, search bar, filter chips, result table, details panel,
indexing manager, settings view, and status bar into a unified, high-performance desktop utility.
"""

from __future__ import annotations
import os
import time
import tkinter as tk
import customtkinter as ctk
from typing import Optional, Dict, Any

from ui.theme import get_theme
from ui.sidebar import Sidebar
from ui.search_bar import SearchBar
from ui.filter_chips import FilterChipsBar
from ui.result_view import ResultView
from ui.details_panel import DetailsPanel
from ui.indexing_view import IndexingView
from ui.settings_view import SettingsView
from ui.status_bar import StatusBar
from ui.tray import SystemTrayManager

from core.search_engine import search_engine
from indexing.index_worker import index_worker
from indexing.watcher import filesystem_watcher
from services.hotkey_service import hotkey_service
from config.settings import settings
from utils.icons import ensure_ico_asset
from utils.logger import logger


class MainWindow(ctk.CTk):
    """Main application window for OpenSearch by DeepLogic."""

    def __init__(self) -> None:
        # Load theme setting
        self.theme_name = settings.get("theme", "dark")
        ctk.set_appearance_mode(self.theme_name)
        self.theme = get_theme(self.theme_name)

        super().__init__()

        # Configure window properties
        self.title("OpenSearch by DeepLogic")
        self.geometry("1100x700")
        self.minsize(860, 520)
        self.configure(fg_color=self.theme["bg"])

        # Set application icon
        try:
            ico_path = ensure_ico_asset()
            if ico_path.exists():
                self.iconbitmap(str(ico_path))
        except Exception as e:
            logger.debug(f"Could not set window icon: {e}")

        # Active state tracking
        self.current_view = "search"
        self.active_category_filter = "all"
        self.active_scope = "All Files"
        self.show_details_panel = True
        self.current_sort_col = "score"
        self.current_sort_asc = True

        self._build_layout()
        self._setup_bindings()
        self._setup_services()

        # Initial search query execution
        self.after(100, lambda: self.execute_search(""))
        # Focus search bar on startup
        self.after(200, self.search_bar.focus)

    def _build_layout(self) -> None:
        """Create primary window structure."""
        # Main Horizontal Layout
        self.main_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # 1. Left Sidebar
        self.sidebar = Sidebar(
            self.main_container,
            on_navigate=self._handle_navigation,
            on_quick_filter=self._handle_quick_filter,
            theme_name=self.theme_name,
        )
        self.sidebar.pack(side="left", fill="y")

        # 2. Right Content Wrapper
        self.content_wrapper = ctk.CTkFrame(self.main_container, fg_color="transparent", corner_radius=0)
        self.content_wrapper.pack(side="left", fill="both", expand=True)

        # Top Search Bar
        self.search_bar = SearchBar(
            self.content_wrapper,
            on_query_change=self._on_search_input,
            on_scope_change=self._on_scope_change,
            debounce_ms=settings.get("search_debounce_ms", 150),
            theme_name=self.theme_name,
        )
        self.search_bar.pack(fill="x", padx=16, pady=(16, 12))

        # View Containers (Search View, Indexing View, Settings View)
        self.view_stack = ctk.CTkFrame(self.content_wrapper, fg_color="transparent", corner_radius=0)
        self.view_stack.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        # --- View 1: Search View ---
        self.search_view_frame = ctk.CTkFrame(self.view_stack, fg_color="transparent", corner_radius=0)
        self.search_view_frame.pack(fill="both", expand=True)

        # Filter Chips Bar
        self.filter_chips = FilterChipsBar(
            self.search_view_frame,
            on_chip_selected=self._handle_chip_selected,
            on_filter_btn_clicked=self._toggle_details_panel,
            theme_name=self.theme_name,
        )
        self.filter_chips.pack(fill="x", pady=(0, 10))

        # Results area (Table + Collapsible Details Panel)
        self.results_area = ctk.CTkFrame(self.search_view_frame, fg_color="transparent", corner_radius=0)
        self.results_area.pack(fill="both", expand=True)

        self.result_view = ResultView(
            self.results_area,
            on_selection_changed=self._handle_result_selection,
            on_sort_changed=self._handle_sort_change,
            theme_name=self.theme_name,
        )
        self.result_view.pack(side="left", fill="both", expand=True)

        self.details_panel = DetailsPanel(
            self.results_area,
            theme_name=self.theme_name,
        )
        self.details_panel.pack(side="right", fill="y", padx=(10, 0))

        # --- View 2: Indexing View ---
        self.indexing_view = IndexingView(self.view_stack, theme_name=self.theme_name)

        # --- View 3: Settings View ---
        self.settings_view = SettingsView(
            self.view_stack,
            on_theme_changed=self._handle_theme_change,
            theme_name=self.theme_name,
        )

        # Bottom Status Bar
        self.status_bar = StatusBar(
            self,
            on_view_mode_changed=self._handle_view_mode_changed,
            on_preview_toggled=self._toggle_details_panel,
            theme_name=self.theme_name,
        )
        self.status_bar.pack(side="bottom", fill="x")

    def _setup_bindings(self) -> None:
        """Register application-wide keyboard shortcuts and window events."""
        self.bind("<Control-l>", lambda e: self._focus_search())
        self.bind("<Control-k>", lambda e: self._focus_search())
        self.bind("<F5>", lambda e: self.refresh_search())
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _setup_services(self) -> None:
        """Initialize background worker, indexing callbacks, system tray, and hotkey."""
        # Progress callback from indexing worker
        def on_index_progress(data: Dict[str, Any]) -> None:
            # Safely schedule update on UI main thread
            self.after(0, lambda: self._update_index_progress(data))

        index_worker.on_progress = on_index_progress

        # Start Indexing Worker in background
        index_worker.start_indexing()

        # Initialize System Tray
        self.tray = SystemTrayManager(
            on_open_clicked=self.show_window,
            on_settings_clicked=lambda: self._handle_navigation("settings"),
            on_exit_clicked=self.exit_app,
        )
        self.tray.start()

        # Initialize Global Hotkey (Ctrl+Shift+Space)
        if settings.get("enable_global_hotkey", True):
            hotkey_service.start(callback=lambda: self.after(0, self.show_window))

    def _focus_search(self) -> str:
        if self.current_view != "search":
            self._handle_navigation("search")
        self.search_bar.focus()
        return "break"

    def _handle_navigation(self, view_key: str) -> None:
        """Switch active main content view."""
        self.current_view = view_key

        # Hide all views
        self.search_view_frame.pack_forget()
        self.indexing_view.pack_forget()
        self.settings_view.pack_forget()

        # Show target view
        if view_key == "search":
            self.search_view_frame.pack(fill="both", expand=True)
            self.search_bar.focus()
        elif view_key == "indexing":
            self.indexing_view.pack(fill="both", expand=True)
            self.indexing_view.refresh()
        elif view_key == "settings":
            self.settings_view.pack(fill="both", expand=True)

    def _handle_quick_filter(self, filter_key: str) -> None:
        """Apply a quick filter from the sidebar."""
        if filter_key == "recent":
            self.search_bar.set_text("modified:today")
        elif filter_key == "large":
            self.search_bar.set_text("size:>100MB")
        elif filter_key in ("documents", "document"):
            self.filter_chips.set_active_chip("document")
        elif filter_key in ("images", "image"):
            self.filter_chips.set_active_chip("image")
        elif filter_key in ("videos", "video"):
            self.filter_chips.set_active_chip("video")
        elif filter_key in ("archives", "archive"):
            self.filter_chips.set_active_chip("archive")
        elif filter_key in ("executables", "executable"):
            self.filter_chips.set_active_chip("executable")
        else:
            self.filter_chips.set_active_chip("all")

        self.execute_search(self.search_bar.get_text())

    def _handle_chip_selected(self, chip_key: str) -> None:
        """Apply category filter chip."""
        self.active_category_filter = chip_key
        self.execute_search(self.search_bar.get_text())

    def _on_search_input(self, text: str) -> None:
        """Triggered when search entry text changes (debounced)."""
        self.execute_search(text)

    def _on_scope_change(self, choice: str) -> None:
        """Handle dropdown scope change."""
        self.active_scope = choice
        self.execute_search(self.search_bar.get_text())

    def execute_search(self, query_text: str) -> None:
        """Run non-blocking search against SQLite index."""
        # Prepend scope filters if applicable
        full_query = query_text.strip()
        if self.active_scope == "C: Only" and "drive:" not in full_query:
            full_query = f"drive:C {full_query}".strip()
        elif self.active_scope == "D: Only" and "drive:" not in full_query:
            full_query = f"drive:D {full_query}".strip()
        elif self.active_scope == "Folders Only" and "type:" not in full_query:
            full_query = f"type:folder {full_query}".strip()

        # Query ID for cancellation of obsolete searches
        query_id = search_engine.next_query_id()

        # Execute search
        res = search_engine.search(
            query_str=full_query,
            query_id=query_id,
            max_results=settings.get("max_results", 1000),
            sort_by=self.current_sort_col,
            sort_asc=self.current_sort_asc,
            category_filter=self.active_category_filter,
        )

        # Ignore cancelled/obsolete query results
        if res.is_cancelled:
            return

        # Update table and metrics
        self.result_view.set_results(res.items)
        self.status_bar.set_search_metrics(res.total_count, res.execution_time_ms)

        # Update details inspector with first item if present
        if res.items:
            self.details_panel.set_item(res.items[0])
        else:
            self.details_panel.set_item(None)

    def refresh_search(self) -> None:
        """Re-run the current search."""
        self.execute_search(self.search_bar.get_text())

    def _handle_result_selection(self, item: Optional[Dict[str, Any]]) -> None:
        """Update inspector when a table row is selected."""
        self.details_panel.set_item(item)

    def _handle_sort_change(self, col: str, asc: bool) -> None:
        """Re-query index with updated sort order."""
        self.current_sort_col = col
        self.current_sort_asc = asc
        self.execute_search(self.search_bar.get_text())

    def _toggle_details_panel(self) -> None:
        """Toggle preview inspector panel visibility."""
        if self.show_details_panel:
            self.details_panel.pack_forget()
            self.show_details_panel = False
        else:
            self.details_panel.pack(side="right", fill="y", padx=(10, 0))
            self.show_details_panel = True

    def _handle_view_mode_changed(self, mode: str) -> None:
        """Switch between list, grid, and details view."""
        settings.set("view_mode", mode)
        # Refresh results
        self.refresh_search()

    def _handle_theme_change(self, theme_key: str) -> None:
        """Update theme mode dynamically."""
        self.theme_name = theme_key
        ctk.set_appearance_mode(theme_key)
        self.theme = get_theme(theme_key)
        self.configure(fg_color=self.theme["bg"])
        self.refresh_search()

    def _update_index_progress(self, data: Dict[str, Any]) -> None:
        """Update status bar and indexing view with live crawl progress."""
        status = data.get("status", "idle")
        total = data.get("total_items", 0)

        if status == "indexing":
            folder = data.get("current_folder", "")
            short_folder = folder[-35:] if len(folder) > 35 else folder
            self.status_bar.set_indexing_info(f"⏳ Indexing: ...{short_folder}")
        elif status == "paused":
            self.status_bar.set_indexing_info("⏸ Indexing paused")
        else:
            self.status_bar.set_indexing_info(f"✔ {total:,} items indexed")

        if self.current_view == "indexing":
            self.indexing_view.refresh()

    def show_window(self) -> None:
        """Restore window from minimized or hidden state and bring to foreground."""
        self.deiconify()
        self.state("normal")
        self.lift()
        self.focus_force()
        self.search_bar.focus()

    def _on_window_close(self) -> None:
        """Handle window close event: minimize to tray or terminate."""
        if settings.get("minimize_to_tray", True):
            self.withdraw()
        else:
            self.exit_app()

    def exit_app(self) -> None:
        """Gracefully terminate background workers, watcher, tray, and destroy window."""
        logger.info("Exiting OpenSearch...")
        hotkey_service.stop()
        index_worker.stop()
        filesystem_watcher.stop()
        self.tray.stop()
        self.destroy()
