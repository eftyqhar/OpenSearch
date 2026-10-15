"""
OpenSearch by DeepLogic — Status Bar
Displays real-time result counts, search execution time in exact seconds/milliseconds,
indexing activity indicator, and view mode toggles.
"""

from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional
from ui.theme import get_theme


class StatusBar(ctk.CTkFrame):
    """Bottom status bar with performance metrics, result count, and view controls."""

    def __init__(
        self,
        master,
        on_view_mode_changed: Optional[Callable[[str], None]] = None,
        on_preview_toggled: Optional[Callable[[], None]] = None,
        theme_name: str = "dark",
        **kwargs,
    ) -> None:
        self.theme = get_theme(theme_name)
        super().__init__(
            master,
            fg_color=self.theme["sidebar_bg"],
            height=28,
            corner_radius=0,
            **kwargs,
        )
        self.on_view_mode_changed = on_view_mode_changed
        self.on_preview_toggled = on_preview_toggled

        self._build_ui()

    def _build_ui(self) -> None:
        """Create status labels and view buttons."""
        self.pack_propagate(False)

        # Left: Result count and execution latency
        self.metrics_label = ctk.CTkLabel(
            self,
            text="⚡ Ready",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.theme["text_secondary"],
            anchor="w",
        )
        self.metrics_label.pack(side="left", padx=16)

        # Indexing status indicator
        self.index_status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.theme["accent_blue"],
            anchor="w",
        )
        self.index_status_label.pack(side="left", padx=10)

        # Right: View mode toggles
        right_box = ctk.CTkFrame(self, fg_color="transparent")
        right_box.pack(side="right", padx=12)

        self.btn_preview = ctk.CTkButton(
            right_box,
            text="◫",
            width=24,
            height=20,
            corner_radius=4,
            fg_color="transparent",
            hover_color=self.theme["card_bg"],
            text_color=self.theme["text_secondary"],
            font=ctk.CTkFont(size=12),
            command=self._toggle_preview,
        )
        self.btn_preview.pack(side="right", padx=2)

        self.btn_grid = ctk.CTkButton(
            right_box,
            text="▦",
            width=24,
            height=20,
            corner_radius=4,
            fg_color="transparent",
            hover_color=self.theme["card_bg"],
            text_color=self.theme["text_secondary"],
            font=ctk.CTkFont(size=12),
            command=lambda: self._set_view_mode("grid"),
        )
        self.btn_grid.pack(side="right", padx=2)

        self.btn_list = ctk.CTkButton(
            right_box,
            text="☰",
            width=24,
            height=20,
            corner_radius=4,
            fg_color=self.theme["card_bg"],
            hover_color=self.theme["card_bg"],
            text_color=self.theme["text_primary"],
            font=ctk.CTkFont(size=12),
            command=lambda: self._set_view_mode("details"),
        )
        self.btn_list.pack(side="right", padx=2)

    def set_search_metrics(self, count: int, latency_ms: float) -> None:
        """Update metrics label with count and formatted seconds/ms."""
        seconds = latency_ms / 1000.0
        text = f"⚡ {count:,} results ({seconds:.2f} seconds)"
        self.metrics_label.configure(text=text)

    def set_indexing_info(self, text: str) -> None:
        """Update indexing progress text."""
        self.index_status_label.configure(text=text)

    def _set_view_mode(self, mode: str) -> None:
        if self.on_view_mode_changed:
            self.on_view_mode_changed(mode)

    def _toggle_preview(self) -> None:
        if self.on_preview_toggled:
            self.on_preview_toggled()
