"""
OpenSearch by DeepLogic — Navigation Sidebar
Implements the left-hand navigation pane with branding, view selectors, and Quick Filters.
"""

from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional
from ui.theme import get_theme
from utils.icons import get_ctk_icon


class Sidebar(ctk.CTkFrame):
    """Left navigation panel containing application branding, views, and quick filters."""

    def __init__(
        self,
        master,
        on_navigate: Callable[[str], None],
        on_quick_filter: Callable[[str], None],
        theme_name: str = "dark",
        **kwargs,
    ) -> None:
        self.theme = get_theme(theme_name)
        super().__init__(
            master,
            fg_color=self.theme["sidebar_bg"],
            corner_radius=0,
            width=210,
            **kwargs,
        )
        self.on_navigate = on_navigate
        self.on_quick_filter = on_quick_filter
        self.active_view = "search"
        self.active_quick_filter = ""

        self._nav_buttons = {}
        self._filter_buttons = {}

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the sidebar layout."""
        self.grid_propagate(False)

        # Branding Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(16, 20))

        # Logo Icon
        logo_label = ctk.CTkLabel(
            header_frame,
            text="🔍",
            font=ctk.CTkFont(size=18),
            text_color=self.theme["accent_blue"],
            width=26,
        )
        logo_label.pack(side="left", padx=(0, 6))

        # Brand Title
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", fill="both")

        name_label = ctk.CTkLabel(
            title_box,
            text="OpenSearch",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self.theme["text_primary"],
        )
        name_label.pack(anchor="w")

        sub_label = ctk.CTkLabel(
            title_box,
            text="by DeepLogic",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.theme["text_secondary"],
        )
        sub_label.pack(anchor="w")

        # Main Navigation Section
        nav_container = ctk.CTkFrame(self, fg_color="transparent")
        nav_container.pack(fill="x", padx=10, pady=(0, 16))

        self._create_nav_button(nav_container, "search", "Search", "🔍")
        self._create_nav_button(nav_container, "indexing", "Indexing", "📁")
        self._create_nav_button(nav_container, "settings", "Settings", "⚙️")

        # Quick Filters Header
        qf_header = ctk.CTkLabel(
            self,
            text="Quick Filters",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.theme["text_muted"],
            anchor="w",
        )
        qf_header.pack(fill="x", padx=18, pady=(8, 6))

        # Quick Filters Buttons
        qf_container = ctk.CTkFrame(self, fg_color="transparent")
        qf_container.pack(fill="x", padx=10, pady=(0, 10))

        self._create_filter_button(qf_container, "recent", "Recent Files", "🕒")
        self._create_filter_button(qf_container, "large", "Large Files", "💾")
        self._create_filter_button(qf_container, "documents", "Documents", "📄")
        self._create_filter_button(qf_container, "images", "Images", "🖼️")
        self._create_filter_button(qf_container, "videos", "Videos", "🎬")
        self._create_filter_button(qf_container, "archives", "Archives", "📦")
        self._create_filter_button(qf_container, "executables", "Executables", "⚡")

    def _create_nav_button(self, parent, key: str, label: str, icon: str) -> None:
        """Create a primary navigation button."""
        is_active = (key == self.active_view)
        btn = ctk.CTkButton(
            parent,
            text=f"  {icon}   {label}",
            anchor="w",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold" if is_active else "normal"),
            fg_color=self.theme["accent_blue"] if is_active else "transparent",
            text_color="#FFFFFF" if is_active else self.theme["text_secondary"],
            hover_color=self.theme["accent_blue_hover"] if is_active else self.theme["card_bg"],
            command=lambda k=key: self._handle_nav_click(k),
        )
        btn.pack(fill="x", pady=2)
        self._nav_buttons[key] = btn

    def _create_filter_button(self, parent, key: str, label: str, icon: str) -> None:
        """Create a quick filter button."""
        btn = ctk.CTkButton(
            parent,
            text=f"  {icon}   {label}",
            anchor="w",
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="transparent",
            text_color=self.theme["text_secondary"],
            hover_color=self.theme["card_bg"],
            command=lambda k=key: self._handle_filter_click(k),
        )
        btn.pack(fill="x", pady=1)
        self._filter_buttons[key] = btn

    def _handle_nav_click(self, view_key: str) -> None:
        """Switch active view and update button styles."""
        self.active_view = view_key
        for key, btn in self._nav_buttons.items():
            is_active = (key == view_key)
            btn.configure(
                fg_color=self.theme["accent_blue"] if is_active else "transparent",
                text_color="#FFFFFF" if is_active else self.theme["text_secondary"],
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold" if is_active else "normal"),
                hover_color=self.theme["accent_blue_hover"] if is_active else self.theme["card_bg"],
            )
        self.on_navigate(view_key)

    def _handle_filter_click(self, filter_key: str) -> None:
        """Toggle quick filter state and notify listener."""
        # Also switch view to search if not already
        if self.active_view != "search":
            self._handle_nav_click("search")

        if self.active_quick_filter == filter_key:
            self.active_quick_filter = ""
        else:
            self.active_quick_filter = filter_key

        for key, btn in self._filter_buttons.items():
            is_active = (key == self.active_quick_filter)
            btn.configure(
                fg_color=self.theme["card_bg"] if is_active else "transparent",
                text_color=self.theme["accent_blue"] if is_active else self.theme["text_secondary"],
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold" if is_active else "normal"),
            )
        self.on_quick_filter(self.active_quick_filter)
