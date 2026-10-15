"""
OpenSearch by DeepLogic — Filter Chips Bar
Displays horizontal category pills (All, Files, Folders, Documents, Images, Videos, Audio, Archives, Executables, Others)
and the Filters toggle button above the result table.
"""

from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional, Dict
from ui.theme import get_theme


CHIPS = [
    ("all", "All", ""),
    ("files", "Files", "📄"),
    ("folders", "Folders", "📁"),
    ("document", "Documents", "📑"),
    ("image", "Images", "🖼️"),
    ("video", "Videos", "🎬"),
    ("audio", "Audio", "🎵"),
    ("archive", "Archives", "📦"),
    ("executable", "Executables", "⚡"),
    ("other", "Others", "⋯"),
]


class FilterChipsBar(ctk.CTkFrame):
    """Horizontal filter pill bar above the search result table."""

    def __init__(
        self,
        master,
        on_chip_selected: Callable[[str], None],
        on_filter_btn_clicked: Optional[Callable[[], None]] = None,
        theme_name: str = "dark",
        **kwargs,
    ) -> None:
        self.theme = get_theme(theme_name)
        super().__init__(master, fg_color="transparent", height=36, **kwargs)

        self.on_chip_selected = on_chip_selected
        self.on_filter_btn_clicked = on_filter_btn_clicked
        self.active_chip = "all"
        self._chip_buttons: Dict[str, ctk.CTkButton] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        """Create scrollable or wrapped chip buttons."""
        self.pack_propagate(False)

        # Chips container
        chips_frame = ctk.CTkFrame(self, fg_color="transparent")
        chips_frame.pack(side="left", fill="both", expand=True)

        for key, label, icon in CHIPS:
            display_text = f"{icon} {label}".strip()
            is_active = (key == self.active_chip)

            btn = ctk.CTkButton(
                chips_frame,
                text=display_text,
                height=28,
                corner_radius=14,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold" if is_active else "normal"),
                fg_color=self.theme["accent_blue"] if is_active else self.theme["chip_bg"],
                text_color="#FFFFFF" if is_active else self.theme["text_secondary"],
                hover_color=self.theme["accent_blue_hover"] if is_active else self.theme["card_bg"],
                border_width=0 if is_active else 1,
                border_color=self.theme["chip_border"],
                command=lambda k=key: self._handle_chip_click(k),
            )
            btn.pack(side="left", padx=(0, 6))
            self._chip_buttons[key] = btn

        # Right-side 'Filters' button
        filters_btn = ctk.CTkButton(
            self,
            text="🎛️ Filters",
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="transparent",
            text_color=self.theme["text_secondary"],
            hover_color=self.theme["card_bg"],
            border_width=1,
            border_color=self.theme["card_border"],
            command=self._handle_filter_button,
        )
        filters_btn.pack(side="right")

    def _handle_chip_click(self, chip_key: str) -> None:
        """Select category chip."""
        self.active_chip = chip_key
        for key, btn in self._chip_buttons.items():
            is_active = (key == chip_key)
            btn.configure(
                fg_color=self.theme["accent_blue"] if is_active else self.theme["chip_bg"],
                text_color="#FFFFFF" if is_active else self.theme["text_secondary"],
                border_width=0 if is_active else 1,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold" if is_active else "normal"),
            )
        self.on_chip_selected(chip_key)

    def set_active_chip(self, chip_key: str) -> None:
        """Set chip from external source."""
        if chip_key in self._chip_buttons:
            self._handle_chip_click(chip_key)

    def _handle_filter_button(self) -> None:
        if self.on_filter_btn_clicked:
            self.on_filter_btn_clicked()
