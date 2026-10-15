"""
OpenSearch by DeepLogic — Settings View
Implements the comprehensive multi-tab settings window matching the mockup:
General (Startup, Tray, Theme, Language), Search, Indexing (Drives, Exclusions), Shortcuts, and About.
"""

from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, Callable, Optional
from ui.theme import get_theme
from config.settings import settings
from indexing.drive_manager import drive_manager


class SettingsView(ctk.CTkFrame):
    """Settings view with sub-category tabs and configuration controls."""

    def __init__(
        self,
        master,
        on_theme_changed: Optional[Callable[[str], None]] = None,
        theme_name: str = "dark",
        **kwargs,
    ) -> None:
        self.theme = get_theme(theme_name)
        super().__init__(master, fg_color=self.theme["bg"], corner_radius=0, **kwargs)

        self.on_theme_changed = on_theme_changed
        self.active_tab = "general"
        self._tab_buttons = {}
        self._tab_frames = {}

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the settings sub-navigation and tab containers."""
        # Left Sub-Sidebar for Settings
        sub_sidebar = ctk.CTkFrame(
            self,
            fg_color=self.theme["sidebar_bg"],
            width=160,
            corner_radius=0,
        )
        sub_sidebar.pack(side="left", fill="y")
        sub_sidebar.pack_propagate(False)

        # Settings Title
        ctk.CTkLabel(
            sub_sidebar,
            text="Settings",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 12))

        # Tabs List
        tabs = [
            ("general", "General", "⚙️"),
            ("search", "Search", "🔍"),
            ("indexing", "Indexing", "📁"),
            ("appearance", "Appearance", "🎨"),
            ("shortcuts", "Shortcuts", "⌨️"),
            ("advanced", "Advanced", "🔧"),
            ("about", "About", "ℹ️"),
        ]

        for key, label, icon in tabs:
            is_active = (key == self.active_tab)
            btn = ctk.CTkButton(
                sub_sidebar,
                text=f"  {icon}  {label}",
                anchor="w",
                height=32,
                corner_radius=6,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold" if is_active else "normal"),
                fg_color=self.theme["accent_blue"] if is_active else "transparent",
                text_color="#FFFFFF" if is_active else self.theme["text_secondary"],
                hover_color=self.theme["accent_blue_hover"] if is_active else self.theme["card_bg"],
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._tab_buttons[key] = btn

        # Main Content Container
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(side="left", fill="both", expand=True, padx=24, pady=20)

        # Build individual tab frames
        self._build_general_tab()
        self._build_search_tab()
        self._build_indexing_tab()
        self._build_appearance_tab()
        self._build_shortcuts_tab()
        self._build_about_tab()

        # Show initial tab
        self._switch_tab("general")

    def _switch_tab(self, key: str) -> None:
        """Switch visible settings tab."""
        self.active_tab = key
        for k, btn in self._tab_buttons.items():
            is_active = (k == key)
            btn.configure(
                fg_color=self.theme["accent_blue"] if is_active else "transparent",
                text_color="#FFFFFF" if is_active else self.theme["text_secondary"],
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold" if is_active else "normal"),
            )

        for k, frame in self._tab_frames.items():
            if k == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    # 1. General Tab
    def _build_general_tab(self) -> None:
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self._tab_frames["general"] = frame

        ctk.CTkLabel(
            frame,
            text="General",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 16))

        # Card container
        card = ctk.CTkFrame(
            frame,
            fg_color=self.theme["card_bg"],
            border_color=self.theme["card_border"],
            border_width=1,
            corner_radius=8,
        )
        card.pack(fill="x", pady=(0, 16))

        # Start with Windows switch
        self._add_switch_row(
            card,
            "Start OpenSearch with Windows",
            "Launch automatically on system startup",
            initial_val=settings.get("startup", False),
            on_toggle=lambda v: settings.set("startup", v),
        )

        # Minimize to system tray switch
        self._add_switch_row(
            card,
            "Minimize to system tray",
            "Keep running in notification area when closed",
            initial_val=settings.get("minimize_to_tray", True),
            on_toggle=lambda v: settings.set("minimize_to_tray", v),
        )

        # Check for updates switch
        self._add_switch_row(
            card,
            "Check for updates",
            "Periodically verify application version",
            initial_val=settings.get("check_updates", True),
            on_toggle=lambda v: settings.set("check_updates", v),
        )

        # Theme Selector Row
        theme_row = ctk.CTkFrame(card, fg_color="transparent")
        theme_row.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            theme_row,
            text="Theme",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.theme["text_primary"],
        ).pack(side="left")

        theme_dropdown = ctk.CTkOptionMenu(
            theme_row,
            values=["Dark", "Light"],
            command=self._handle_theme_change,
            fg_color=self.theme["chip_bg"],
            button_color=self.theme["card_bg"],
            text_color=self.theme["text_primary"],
            width=120,
            height=28,
        )
        current_theme = settings.get("theme", "dark").capitalize()
        theme_dropdown.set(current_theme)
        theme_dropdown.pack(side="right")

        # Language Selector Row
        lang_row = ctk.CTkFrame(card, fg_color="transparent")
        lang_row.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            lang_row,
            text="Language",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.theme["text_primary"],
        ).pack(side="left")

        lang_dropdown = ctk.CTkOptionMenu(
            lang_row,
            values=["English"],
            fg_color=self.theme["chip_bg"],
            button_color=self.theme["card_bg"],
            text_color=self.theme["text_primary"],
            width=120,
            height=28,
        )
        lang_dropdown.set("English")
        lang_dropdown.pack(side="right")

    # 2. Search Tab
    def _build_search_tab(self) -> None:
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self._tab_frames["search"] = frame

        ctk.CTkLabel(
            frame,
            text="Search Preferences",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 16))

        card = ctk.CTkFrame(
            frame,
            fg_color=self.theme["card_bg"],
            border_color=self.theme["card_border"],
            border_width=1,
            corner_radius=8,
        )
        card.pack(fill="x", pady=(0, 16))

        self._add_switch_row(
            card,
            "Fuzzy Subsequence Matching",
            "Match characters even when separated (e.g. reqtxt -> requirements.txt)",
            initial_val=settings.get("fuzzy_search", True),
            on_toggle=lambda v: settings.set("fuzzy_search", v),
        )

        self._add_switch_row(
            card,
            "Match Case",
            "Make searches case-sensitive by default",
            initial_val=settings.get("match_case", False),
            on_toggle=lambda v: settings.set("match_case", v),
        )

    # 3. Indexing Tab
    def _build_indexing_tab(self) -> None:
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self._tab_frames["indexing"] = frame

        ctk.CTkLabel(
            frame,
            text="Drive & Indexing Rules",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 16))

        card = ctk.CTkFrame(
            frame,
            fg_color=self.theme["card_bg"],
            border_color=self.theme["card_border"],
            border_width=1,
            corner_radius=8,
        )
        card.pack(fill="x", pady=(0, 16))

        # Checkboxes for detected drives
        drives_header = ctk.CTkLabel(
            card,
            text="Drives to Index:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        )
        drives_header.pack(fill="x", padx=16, pady=(12, 6))

        drives = drive_manager.get_available_drives()
        configured_drives = set(settings.get("indexed_drives", ["C:"]))

        for d in drives:
            cb = ctk.CTkCheckBox(
                card,
                text=f"{d.letter}  ({d.label} - {d.filesystem})",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                command=lambda drv=d.letter: self._toggle_drive(drv),
            )
            if d.letter in configured_drives:
                cb.select()
            cb.pack(anchor="w", padx=24, pady=3)

        self._add_switch_row(
            card,
            "Index Hidden Files",
            "Include files beginning with a dot or hidden attribute",
            initial_val=settings.get("index_hidden_files", True),
            on_toggle=lambda v: settings.set("index_hidden_files", v),
        )

        self._add_switch_row(
            card,
            "Index Removable Drives",
            "Automatically index USB thumb drives and portable disks",
            initial_val=settings.get("index_removable_drives", False),
            on_toggle=lambda v: settings.set("index_removable_drives", v),
        )

    # 4. Appearance Tab
    def _build_appearance_tab(self) -> None:
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self._tab_frames["appearance"] = frame

        ctk.CTkLabel(
            frame,
            text="Appearance",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 16))

        card = ctk.CTkFrame(
            frame,
            fg_color=self.theme["card_bg"],
            border_color=self.theme["card_border"],
            border_width=1,
            corner_radius=8,
        )
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            card,
            text="OpenSearch uses a restrained Windows 11 Fluent dark palette with subtle contrast.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_secondary"],
            anchor="w",
        ).pack(fill="x", padx=16, pady=16)

    # 5. Shortcuts Tab
    def _build_shortcuts_tab(self) -> None:
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self._tab_frames["shortcuts"] = frame

        ctk.CTkLabel(
            frame,
            text="Keyboard Shortcuts",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 16))

        card = ctk.CTkFrame(
            frame,
            fg_color=self.theme["card_bg"],
            border_color=self.theme["card_border"],
            border_width=1,
            corner_radius=8,
        )
        card.pack(fill="x", pady=(0, 16))

        shortcuts_list = [
            ("Ctrl + L / Ctrl + K", "Focus search input"),
            ("Enter", "Open selected file/folder"),
            ("Ctrl + Enter", "Reveal file in Windows Explorer"),
            ("Ctrl + C", "Copy absolute file path"),
            ("F2", "Rename file/folder"),
            ("Delete", "Move to Windows Recycle Bin"),
            ("Alt + Enter", "Open native Windows Properties"),
            ("Ctrl + Shift + Space", "Global hotkey to summon OpenSearch"),
        ]

        for keys, desc in shortcuts_list:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(
                row,
                text=keys,
                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                text_color=self.theme["accent_blue"],
                width=180,
                anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=desc,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=self.theme["text_secondary"],
                anchor="w",
            ).pack(side="left")

    # 6. About Tab
    def _build_about_tab(self) -> None:
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self._tab_frames["about"] = frame

        card = ctk.CTkFrame(
            frame,
            fg_color=self.theme["card_bg"],
            border_color=self.theme["card_border"],
            border_width=1,
            corner_radius=8,
        )
        card.pack(fill="x", pady=20)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", padx=24, pady=24)

        ctk.CTkLabel(
            inner,
            text="OpenSearch by DeepLogic",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner,
            text="Ultra-fast local file and folder search utility for Windows.\nVersion 1.0.0 (x64 Production)",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.theme["text_secondary"],
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(6, 16))

        privacy_box = ctk.CTkFrame(inner, fg_color=self.theme["table_bg"], corner_radius=6)
        privacy_box.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            privacy_box,
            text="🔒 Privacy & Local-First Guarantee:\n"
                 "• Operates 100% locally on your machine.\n"
                 "• No telemetry, analytics, or cloud connections.\n"
                 "• Never sends filenames, paths, or queries outside your computer.\n"
                 "• No account, registration, or API keys required.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.theme["text_primary"],
            justify="left",
            anchor="w",
        ).pack(padx=16, pady=12)

        ctk.CTkLabel(
            inner,
            text="© DeepLogic. All rights reserved.",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.theme["text_muted"],
            anchor="w",
        ).pack(anchor="w")

    def _add_switch_row(
        self, parent, title: str, subtitle: str, initial_val: bool, on_toggle: Callable[[bool], None]
    ) -> None:
        """Create a toggle switch row with title and subtitle."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=10)

        info_box = ctk.CTkFrame(row, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            info_box,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_box,
            text=subtitle,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.theme["text_secondary"],
            anchor="w",
        ).pack(anchor="w")

        switch = ctk.CTkSwitch(
            row,
            text="",
            width=42,
            progress_color=self.theme["accent_blue"],
            command=lambda: on_toggle(switch.get() == 1),
        )
        if initial_val:
            switch.select()
        switch.pack(side="right")

    def _handle_theme_change(self, choice: str) -> None:
        """Update theme setting."""
        theme_key = choice.lower()
        settings.set("theme", theme_key)
        if self.on_theme_changed:
            self.on_theme_changed(theme_key)

    def _toggle_drive(self, drive_letter: str) -> None:
        """Toggle drive letter in indexed_drives setting."""
        drives = list(settings.get("indexed_drives", ["C:"]))
        if drive_letter in drives:
            drives.remove(drive_letter)
        else:
            drives.append(drive_letter)
        settings.set("indexed_drives", drives)
