"""
OpenSearch by DeepLogic — Primary Search Bar
Features debounced text input, clear action, keyboard focus shortcuts (Ctrl+L / Ctrl+K),
and right-side scope dropdown matching the design mockup.
"""

from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional
from ui.theme import get_theme


class SearchBar(ctk.CTkFrame):
    """Top search bar with debounced query dispatch, clear button, and scope selector."""

    def __init__(
        self,
        master,
        on_query_change: Callable[[str], None],
        on_scope_change: Optional[Callable[[str], None]] = None,
        debounce_ms: int = 150,
        theme_name: str = "dark",
        **kwargs,
    ) -> None:
        self.theme = get_theme(theme_name)
        super().__init__(master, fg_color="transparent", **kwargs)

        self.on_query_change = on_query_change
        self.on_scope_change = on_scope_change
        self.debounce_ms = debounce_ms
        self._debounce_timer: Optional[str] = None
        self._current_scope = "All Files"

        self._build_ui()

    def _build_ui(self) -> None:
        """Create search bar controls."""
        # Main search box container
        search_box = ctk.CTkFrame(
            self,
            fg_color=self.theme["search_bg"],
            border_color=self.theme["search_border"],
            border_width=1,
            corner_radius=8,
            height=40,
        )
        search_box.pack(side="left", fill="x", expand=True, padx=(0, 10))
        search_box.pack_propagate(False)

        # Search Icon (Magnifying glass)
        icon_lbl = ctk.CTkLabel(
            search_box,
            text="🔍",
            font=ctk.CTkFont(size=14),
            text_color=self.theme["text_muted"],
            width=32,
        )
        icon_lbl.pack(side="left", padx=(8, 2))

        # Entry Field
        self.entry_var = tk.StringVar()
        self.entry_var.trace_add("write", self._on_text_modified)

        self.entry = ctk.CTkEntry(
            search_box,
            textvariable=self.entry_var,
            placeholder_text="Search files and folders...",
            placeholder_text_color=self.theme["text_muted"],
            text_color=self.theme["text_primary"],
            fg_color="transparent",
            border_width=0,
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=2)

        # Clear Button (✕)
        self.clear_btn = ctk.CTkButton(
            search_box,
            text="✕",
            width=26,
            height=26,
            corner_radius=13,
            fg_color="transparent",
            hover_color=self.theme["table_hover_bg"],
            text_color=self.theme["text_muted"],
            font=ctk.CTkFont(size=11),
            command=self.clear,
        )
        self.clear_btn.pack(side="right", padx=6)

        # Scope Dropdown / Button (All Files ⌵)
        self.scope_menu = ctk.CTkOptionMenu(
            self,
            values=["All Files", "C: Only", "D: Only", "Folders Only", "Documents", "Images", "Executables"],
            command=self._handle_scope_select,
            fg_color=self.theme["card_bg"],
            button_color=self.theme["card_bg"],
            button_hover_color=self.theme["chip_bg"],
            text_color=self.theme["text_primary"],
            dropdown_fg_color=self.theme["card_bg"],
            dropdown_text_color=self.theme["text_primary"],
            dropdown_hover_color=self.theme["accent_blue"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            width=115,
            height=38,
            corner_radius=8,
        )
        self.scope_menu.set(self._current_scope)
        self.scope_menu.pack(side="right")

    def _on_text_modified(self, *args) -> None:
        """Handle entry keystroke with debounce timer."""
        # Cancel pending debounce timer
        if self._debounce_timer:
            self.after_cancel(self._debounce_timer)
            self._debounce_timer = None

        text = self.entry_var.get()
        # Toggle clear button visibility / appearance
        if text:
            self.clear_btn.configure(text_color=self.theme["text_secondary"])
        else:
            self.clear_btn.configure(text_color=self.theme["text_muted"])

        # Schedule debounced dispatch
        self._debounce_timer = self.after(self.debounce_ms, self._dispatch_query)

    def _dispatch_query(self) -> None:
        """Send current query text to callback."""
        self._debounce_timer = None
        self.on_query_change(self.entry_var.get())

    def _handle_scope_select(self, choice: str) -> None:
        """Handle scope selection dropdown."""
        self._current_scope = choice
        if self.on_scope_change:
            self.on_scope_change(choice)

    def focus(self) -> None:
        """Focus input and select all text."""
        self.entry.focus_set()
        self.entry.select_range(0, "end")

    def clear(self) -> None:
        """Clear query text and trigger search refresh."""
        self.entry_var.set("")
        self.entry.focus_set()
        self.on_query_change("")

    def get_text(self) -> str:
        """Return the current query text."""
        return self.entry_var.get()

    def set_text(self, text: str) -> None:
        """Set query text directly."""
        self.entry_var.set(text)
