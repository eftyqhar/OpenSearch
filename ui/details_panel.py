"""
OpenSearch by DeepLogic — Details & Preview Panel
Displays selected file details, metadata (Location, Size in bytes, Type, Dates),
action buttons (Open, Reveal), and interactive tabs (Preview, Details, Related).
"""

from __future__ import annotations
import os
import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Optional
from PIL import Image, ImageTk
from ui.theme import get_theme
from utils.helpers import format_bytes, format_timestamp
from utils.icons import draw_file_icon, map_ext_to_icon_type
from services.file_service import file_service


class DetailsPanel(ctk.CTkFrame):
    """Side panel displaying file preview and detailed metadata."""

    def __init__(self, master, theme_name: str = "dark", **kwargs) -> None:
        self.theme = get_theme(theme_name)
        super().__init__(
            master,
            fg_color=self.theme["sidebar_bg"],
            corner_radius=0,
            width=280,
            **kwargs,
        )
        self.current_item: Optional[Dict[str, Any]] = None
        self.active_tab = "preview"
        self._thumbnail_photo: Optional[ImageTk.PhotoImage] = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct preview layout."""
        self.grid_propagate(False)

        # Header with icon and action
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=16, pady=(16, 10))

        # Icon Label
        self.icon_label = ctk.CTkLabel(self.header_frame, text="📄", font=ctk.CTkFont(size=28), width=36)
        self.icon_label.pack(side="left", padx=(0, 10))

        # Title & Subtitle box
        info_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True)

        self.name_label = ctk.CTkLabel(
            info_box,
            text="No item selected",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        )
        self.name_label.pack(fill="x")

        self.sub_label = ctk.CTkLabel(
            info_box,
            text="Select a file to inspect",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_secondary"],
            anchor="w",
        )
        self.sub_label.pack(fill="x")

        # Open Action Button
        self.open_btn = ctk.CTkButton(
            self,
            text="Open",
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=self.theme["accent_blue"],
            hover_color=self.theme["accent_blue_hover"],
            text_color="#FFFFFF",
            command=self._handle_open,
        )
        self.open_btn.pack(fill="x", padx=16, pady=(4, 12))

        # Metadata Grid
        self.meta_frame = ctk.CTkFrame(self, fg_color=self.theme["card_bg"], corner_radius=8)
        self.meta_frame.pack(fill="x", padx=16, pady=(0, 12))

        self.loc_val = self._add_meta_row(self.meta_frame, "Location", "—")
        self.size_val = self._add_meta_row(self.meta_frame, "Size", "—")
        self.type_val = self._add_meta_row(self.meta_frame, "Type", "—")
        self.mtime_val = self._add_meta_row(self.meta_frame, "Date modified", "—")
        self.ctime_val = self._add_meta_row(self.meta_frame, "Date created", "—")

        # Tabs Header (Preview, Details, Related)
        tab_bar = ctk.CTkFrame(self, fg_color="transparent", height=28)
        tab_bar.pack(fill="x", padx=16, pady=(4, 8))

        self.preview_tab_btn = self._create_tab_button(tab_bar, "preview", "Preview")
        self.details_tab_btn = self._create_tab_button(tab_bar, "details", "Details")
        self.related_tab_btn = self._create_tab_button(tab_bar, "related", "Related")

        # Preview Container
        self.preview_container = ctk.CTkFrame(
            self, fg_color=self.theme["card_bg"], corner_radius=8, height=180
        )
        self.preview_container.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.preview_text = ctk.CTkLabel(
            self.preview_container,
            text="File Preview\n\nSelect an image, code, or document",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_muted"],
        )
        self.preview_text.pack(expand=True)

    def _add_meta_row(self, parent, label: str, value: str) -> ctk.CTkLabel:
        """Create a metadata property key-value row."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=3)

        lbl = ctk.CTkLabel(
            row,
            text=label,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.theme["text_secondary"],
            width=80,
            anchor="w",
        )
        lbl.pack(side="left")

        val = ctk.CTkLabel(
            row,
            text=value,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        )
        val.pack(side="left", fill="x", expand=True)
        return val

    def _create_tab_button(self, parent, key: str, label: str) -> ctk.CTkButton:
        """Create tab selector button."""
        is_active = (key == self.active_tab)
        btn = ctk.CTkButton(
            parent,
            text=label,
            width=70,
            height=24,
            corner_radius=4,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold" if is_active else "normal"),
            fg_color=self.theme["accent_blue"] if is_active else "transparent",
            text_color="#FFFFFF" if is_active else self.theme["text_secondary"],
            command=lambda k=key: self._handle_tab_select(k),
        )
        btn.pack(side="left", padx=(0, 6))
        return btn

    def _handle_tab_select(self, key: str) -> None:
        """Switch active inspector tab."""
        self.active_tab = key
        for k, btn in [("preview", self.preview_tab_btn), ("details", self.details_tab_btn), ("related", self.related_tab_btn)]:
            is_active = (k == key)
            btn.configure(
                fg_color=self.theme["accent_blue"] if is_active else "transparent",
                text_color="#FFFFFF" if is_active else self.theme["text_secondary"],
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold" if is_active else "normal"),
            )

    def set_item(self, item: Optional[Dict[str, Any]]) -> None:
        """Update inspector with selected file information."""
        self.current_item = item
        if not item:
            self.name_label.configure(text="No item selected")
            self.sub_label.configure(text="Select a file to inspect")
            self.loc_val.configure(text="—")
            self.size_val.configure(text="—")
            self.type_val.configure(text="—")
            self.mtime_val.configure(text="—")
            self.ctime_val.configure(text="—")
            self.preview_text.configure(text="File Preview\n\nSelect an image, code, or document")
            return

        name = item.get("name", "")
        path = item.get("path", "")
        is_dir = item.get("is_directory", False)
        ext = item.get("extension", "")
        size = item.get("size", 0)
        mtime = item.get("modified_time", 0)
        ctime = item.get("created_time", 0)
        type_desc = item.get("type_desc", "File")

        self.name_label.configure(text=name[:30] + ("..." if len(name) > 30 else ""))
        size_display = "—" if is_dir else format_bytes(size)
        self.sub_label.configure(text=f"{type_desc} · {size_display}")

        self.loc_val.configure(text=path[:32] + ("..." if len(path) > 32 else ""))
        self.size_val.configure(text=f"{size_display} ({size:,} bytes)" if not is_dir else "—")
        self.type_val.configure(text=type_desc)
        self.mtime_val.configure(text=format_timestamp(mtime))
        self.ctime_val.configure(text=format_timestamp(ctime))

        # Check for image thumbnail preview
        ext_clean = ext.lower().lstrip(".")
        if ext_clean in ("png", "jpg", "jpeg", "bmp", "gif", "webp") and os.path.isfile(path):
            try:
                img = Image.open(path)
                img.thumbnail((220, 160))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                self.preview_text.configure(image=ctk_img, text="")
            except Exception:
                self.preview_text.configure(image=None, text="Image Preview Unavailable")
        elif ext_clean in ("txt", "py", "json", "md", "csv", "log") and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    preview_sample = "".join(f.readline() for _ in range(8))
                self.preview_text.configure(image=None, text=preview_sample[:250])
            except Exception:
                self.preview_text.configure(image=None, text="Text Preview Unavailable")
        else:
            self.preview_text.configure(image=None, text=f"{type_desc}\n\n{name}")

    def _handle_open(self) -> None:
        """Launch the current item."""
        if self.current_item and "path" in self.current_item:
            file_service.open_item(self.current_item["path"])
