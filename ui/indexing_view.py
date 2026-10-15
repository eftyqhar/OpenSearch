"""
OpenSearch by DeepLogic — Indexing Status & Location Manager
Faithfully implements the indexing dashboard view from the UI mockup:
status banner, metrics cards, indexed locations table, pause/resume, and rebuild index.
"""

from __future__ import annotations
import time
import tkinter as tk
from tkinter import ttk, filedialog
import customtkinter as ctk
from typing import Dict, Any, List, Optional
from ui.theme import get_theme
from utils.helpers import format_bytes, format_timestamp
from indexing.index_worker import index_worker
from indexing.drive_manager import drive_manager
from database.repositories import file_repo
from config.settings import settings


class IndexingView(ctk.CTkFrame):
    """Indexing management view displaying active locations, stats, and crawl controls."""

    def __init__(self, master, theme_name: str = "dark", **kwargs) -> None:
        self.theme = get_theme(theme_name)
        super().__init__(master, fg_color=self.theme["bg"], corner_radius=0, **kwargs)

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Construct the indexing view."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        # Header Title
        title_lbl = ctk.CTkLabel(
            container,
            text="Indexing Status",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        )
        title_lbl.pack(fill="x", pady=(0, 16))

        # Status Banner Card
        self.banner_card = ctk.CTkFrame(
            container,
            fg_color=self.theme["card_bg"],
            border_color=self.theme["card_border"],
            border_width=1,
            corner_radius=10,
        )
        self.banner_card.pack(fill="x", pady=(0, 16))

        banner_inner = ctk.CTkFrame(self.banner_card, fg_color="transparent")
        banner_inner.pack(fill="x", padx=16, pady=16)

        # Status Icon & Title
        status_left = ctk.CTkFrame(banner_inner, fg_color="transparent")
        status_left.pack(side="left", fill="both")

        self.status_icon = ctk.CTkLabel(
            status_left,
            text="✔",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#FFFFFF",
            fg_color=self.theme["status_green"],
            corner_radius=16,
            width=36,
            height=36,
        )
        self.status_icon.pack(side="left", padx=(0, 12))

        status_text_box = ctk.CTkFrame(status_left, fg_color="transparent")
        status_text_box.pack(side="left")

        self.status_title = ctk.CTkLabel(
            status_text_box,
            text="Indexing Complete",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        )
        self.status_title.pack(anchor="w")

        self.status_subtitle = ctk.CTkLabel(
            status_text_box,
            text="All configured locations are indexed and synchronized",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_secondary"],
            anchor="w",
        )
        self.status_subtitle.pack(anchor="w")

        # Pause / Resume Button
        self.btn_pause = ctk.CTkButton(
            banner_inner,
            text="Pause",
            width=80,
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=self.theme["chip_bg"],
            text_color=self.theme["text_primary"],
            hover_color=self.theme["table_hover_bg"],
            border_width=1,
            border_color=self.theme["card_border"],
            command=self._handle_toggle_pause,
        )
        self.btn_pause.pack(side="right")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.banner_card,
            progress_color=self.theme["accent_blue"],
            fg_color=self.theme["table_border"],
            height=4,
            corner_radius=2,
        )
        self.progress_bar.pack(fill="x", padx=16, pady=(0, 14))
        self.progress_bar.set(1.0)

        # 4 Metrics Cards Row
        metrics_row = ctk.CTkFrame(container, fg_color="transparent")
        metrics_row.pack(fill="x", pady=(0, 18))

        self.metric_files = self._create_metric_card(metrics_row, "Files", "0", "📄")
        self.metric_folders = self._create_metric_card(metrics_row, "Folders", "0", "📁")
        self.metric_size = self._create_metric_card(metrics_row, "Total Size", "0 B", "💾")
        self.metric_updated = self._create_metric_card(metrics_row, "Last Updated", "—", "🕒")

        # Indexed Locations Header
        loc_header = ctk.CTkLabel(
            container,
            text="Indexed Locations",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        )
        loc_header.pack(fill="x", pady=(4, 8))

        # Locations Treeview Container
        table_container = ctk.CTkFrame(
            container,
            fg_color=self.theme["card_bg"],
            border_color=self.theme["card_border"],
            border_width=1,
            corner_radius=8,
        )
        table_container.pack(fill="both", expand=True, pady=(0, 16))

        columns = ("location", "items", "status")
        self.loc_tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="OpenSearch.Treeview",
            height=6,
        )
        self.loc_tree.heading("location", text="Location")
        self.loc_tree.heading("items", text="Indexed Items")
        self.loc_tree.heading("status", text="Status")

        self.loc_tree.column("location", width=380, anchor="w")
        self.loc_tree.column("items", width=120, anchor="e")
        self.loc_tree.column("status", width=120, anchor="center")

        self.loc_tree.pack(fill="both", expand=True, padx=2, pady=2)

        # Bottom Action Bar (+ Add Location, Rebuild Index)
        action_bar = ctk.CTkFrame(container, fg_color="transparent")
        action_bar.pack(fill="x")

        self.btn_add_loc = ctk.CTkButton(
            action_bar,
            text="+ Add Location",
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=self.theme["chip_bg"],
            text_color=self.theme["text_primary"],
            hover_color=self.theme["table_hover_bg"],
            border_width=1,
            border_color=self.theme["card_border"],
            command=self._handle_add_location,
        )
        self.btn_add_loc.pack(side="left")

        self.btn_rebuild = ctk.CTkButton(
            action_bar,
            text="🔄 Rebuild Index",
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="transparent",
            text_color=self.theme["text_secondary"],
            hover_color=self.theme["card_bg"],
            border_width=1,
            border_color=self.theme["card_border"],
            command=self._handle_rebuild,
        )
        self.btn_rebuild.pack(side="right")

    def _create_metric_card(self, parent, title: str, value: str, icon: str) -> ctk.CTkLabel:
        """Create a summary card."""
        card = ctk.CTkFrame(
            parent,
            fg_color=self.theme["card_bg"],
            border_color=self.theme["card_border"],
            border_width=1,
            corner_radius=8,
            height=64,
        )
        card.pack(side="left", fill="both", expand=True, padx=4)
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        # Icon and title
        top_box = ctk.CTkFrame(inner, fg_color="transparent")
        top_box.pack(fill="x")

        ctk.CTkLabel(
            top_box,
            text=f"{icon} {title}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.theme["text_secondary"],
            anchor="w",
        ).pack(side="left")

        val_lbl = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        )
        val_lbl.pack(fill="x", pady=(2, 0))
        return val_lbl

    def refresh(self) -> None:
        """Update metrics and locations table with live data."""
        stats = file_repo.get_stats()
        self.metric_files.configure(text=f"{stats['total_files']:,}")
        self.metric_folders.configure(text=f"{stats['total_folders']:,}")
        self.metric_size.configure(text=format_bytes(stats["total_size"]))
        self.metric_updated.configure(text=format_timestamp(time.time() if stats['total_items'] > 0 else 0))

        # Update banner state
        if index_worker.is_indexing:
            self.status_icon.configure(text="⏳", fg_color=self.theme["accent_blue"])
            self.status_title.configure(text="Indexing in Progress...")
            self.status_subtitle.configure(
                text=f"Currently indexing: {index_worker.current_folder or 'Local drives'}"
            )
            self.btn_pause.configure(text="Pause")
            self.progress_bar.set(0.6)
        elif index_worker.is_paused:
            self.status_icon.configure(text="⏸", fg_color=self.theme["status_amber"])
            self.status_title.configure(text="Indexing Paused")
            self.status_subtitle.configure(text="Indexing paused by user")
            self.btn_pause.configure(text="Resume")
        else:
            self.status_icon.configure(text="✔", fg_color=self.theme["status_green"])
            self.status_title.configure(text="Indexing Complete")
            self.status_subtitle.configure(
                text=f"{stats['total_items']:,} items indexed and monitored in real time"
            )
            self.btn_pause.configure(text="Pause")
            self.progress_bar.set(1.0)

        # Populate locations
        for iid in self.loc_tree.get_children():
            self.loc_tree.delete(iid)

        locations = file_repo.get_locations()
        if not locations:
            # Query drives
            drives = drive_manager.get_available_drives()
            for d in drives:
                self.loc_tree.insert(
                    "",
                    "end",
                    values=(d.root, f"{stats['total_items']:,} items", "● Indexed"),
                )
        else:
            for loc in locations:
                total_items = loc.get("total_files", 0) + loc.get("total_folders", 0)
                status_str = "● Indexed" if loc.get("status") == "Indexed" else loc.get("status", "Pending")
                self.loc_tree.insert(
                    "",
                    "end",
                    values=(loc.get("location"), f"{total_items:,} items", status_str),
                )

    def _handle_toggle_pause(self) -> None:
        index_worker.toggle_pause()
        self.refresh()

    def _handle_rebuild(self) -> None:
        from tkinter import messagebox
        if messagebox.askyesno("Rebuild Index", "Are you sure you want to rebuild the entire index? This will clear current records and rescan all drives."):
            index_worker.rebuild_index()
            self.refresh()

    def _handle_add_location(self) -> None:
        folder = filedialog.askdirectory(title="Select Folder to Index")
        if folder:
            custom_locs = settings.get("indexed_locations", [])
            if folder not in custom_locs:
                custom_locs.append(folder)
                settings.set("indexed_locations", custom_locs)
                index_worker.start_indexing([folder])
                self.refresh()
