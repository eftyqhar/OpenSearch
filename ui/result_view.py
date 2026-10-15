"""
OpenSearch by DeepLogic — Result Table View
High-performance virtualized ttk.Treeview with custom dark/light theme,
icons, column sorting, keyboard shortcuts, and right-click context menu.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Callable, Optional
from ui.theme import get_theme
from ui.context_menu import ResultContextMenu
from utils.helpers import format_bytes, format_timestamp
from utils.icons import get_tk_file_icon, map_ext_to_icon_type
from services.file_service import file_service
from services.clipboard_service import clipboard_service
from services.shell_service import shell_service


class ResultView(tk.Frame):
    """Virtualized results table with keyboard navigation, icons, and shell operations."""

    def __init__(
        self,
        master,
        on_selection_changed: Optional[Callable[[Optional[Dict[str, Any]]], None]] = None,
        on_sort_changed: Optional[Callable[[str, bool], None]] = None,
        theme_name: str = "dark",
        **kwargs,
    ) -> None:
        self.theme = get_theme(theme_name)
        super().__init__(master, bg=self.theme["bg"], **kwargs)

        self.on_selection_changed = on_selection_changed
        self.on_sort_changed = on_sort_changed
        self.theme_name = theme_name

        self._items: List[Dict[str, Any]] = []
        self._item_map: Dict[str, Dict[str, Any]] = {}
        self.sort_col = "name"
        self.sort_asc = True

        self._configure_ttk_style()
        self._build_ui()

        # Context menu
        self.context_menu = ResultContextMenu(
            master=self,
            on_rename_request=self._handle_rename_request,
            on_delete_request=self._handle_delete_request,
            theme_name=theme_name,
        )

    def _configure_ttk_style(self) -> None:
        """Apply custom dark/light styling to ttk.Treeview and Scrollbar."""
        style = ttk.Style()
        style.theme_use("clam")

        # Treeview styling
        style.configure(
            "OpenSearch.Treeview",
            background=self.theme["table_bg"],
            foreground=self.theme["table_row_fg"],
            fieldbackground=self.theme["table_bg"],
            rowheight=28,
            font=("Segoe UI", 9),
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "OpenSearch.Treeview",
            background=[("selected", self.theme["table_selected_bg"])],
            foreground=[("selected", self.theme["table_selected_fg"])],
        )

        # Header styling
        style.configure(
            "OpenSearch.Treeview.Heading",
            background=self.theme["table_header_bg"],
            foreground=self.theme["table_header_fg"],
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            borderwidth=0,
            padding=(6, 4),
        )
        style.map(
            "OpenSearch.Treeview.Heading",
            background=[("active", self.theme["card_bg"])],
            foreground=[("active", self.theme["text_primary"])],
        )

        # Scrollbar styling
        style.configure(
            "OpenSearch.Vertical.TScrollbar",
            background=self.theme["sidebar_bg"],
            troughcolor=self.theme["bg"],
            bordercolor=self.theme["border"],
            arrowcolor=self.theme["text_muted"],
            relief="flat",
            width=10,
        )

    def _build_ui(self) -> None:
        """Create the Treeview and vertical scrollbar."""
        columns = ("name", "path", "size", "type", "modified")

        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="OpenSearch.Treeview",
        )

        # Column configuration
        self.tree.heading("name", text="Name ↑", command=lambda: self._sort_by("name"))
        self.tree.heading("path", text="Path", command=lambda: self._sort_by("path"))
        self.tree.heading("size", text="Size", command=lambda: self._sort_by("size"))
        self.tree.heading("type", text="Type", command=lambda: self._sort_by("type"))
        self.tree.heading("modified", text="Date Modified", command=lambda: self._sort_by("modified"))

        self.tree.column("name", width=220, minwidth=120, anchor="w")
        self.tree.column("path", width=340, minwidth=150, anchor="w")
        self.tree.column("size", width=80, minwidth=60, anchor="e")
        self.tree.column("type", width=110, minwidth=80, anchor="w")
        self.tree.column("modified", width=140, minwidth=100, anchor="w")

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.tree.yview,
            style="OpenSearch.Vertical.TScrollbar",
        )
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Configure alternate row tags
        self.tree.tag_configure("even", background=self.theme["table_bg"])
        self.tree.tag_configure("odd", background=self.theme["table_alt_bg"])

        # Bind events
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Return>", self._on_return_pressed)
        self.tree.bind("<Control-Return>", self._on_ctrl_return_pressed)
        self.tree.bind("<Control-c>", self._on_copy_pressed)
        self.tree.bind("<Delete>", self._on_delete_pressed)
        self.tree.bind("<F2>", self._on_f2_pressed)
        self.tree.bind("<Alt-Return>", self._on_alt_return_pressed)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_selection)

    def set_results(self, items: List[Dict[str, Any]]) -> None:
        """Populate results in Treeview efficiently."""
        self._items = items
        self._item_map.clear()

        # Detach/delete existing rows
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        # Batch insert
        for idx, item in enumerate(items):
            row_id = str(item.get("id", idx))
            self._item_map[row_id] = item

            tag = "even" if (idx % 2 == 0) else "odd"
            is_dir = item.get("is_directory", False)
            ext = item.get("extension", "")

            # Format values
            size_str = "—" if is_dir else format_bytes(item.get("size"))
            modified_str = format_timestamp(item.get("modified_time"))
            type_str = item.get("type_desc", "File folder" if is_dir else "File")

            icon_key = map_ext_to_icon_type(ext, is_dir)
            icon = get_tk_file_icon(icon_key, size=16)

            self.tree.insert(
                "",
                "end",
                iid=row_id,
                image=icon,
                values=(item.get("name", ""), item.get("path", ""), size_str, type_str, modified_str),
                tags=(tag,),
            )

        # If items exist, select first item
        children = self.tree.get_children()
        if children:
            first_id = children[0]
            self.tree.selection_set(first_id)
            self.tree.focus(first_id)

    def get_selected_item(self) -> Optional[Dict[str, Any]]:
        """Return the dictionary of the currently focused or first selected item."""
        sel = self.tree.selection()
        if sel:
            return self._item_map.get(sel[0])
        return None

    def get_all_selected_items(self) -> List[Dict[str, Any]]:
        """Return dictionaries of all multi-selected items."""
        return [self._item_map[iid] for iid in self.tree.selection() if iid in self._item_map]

    def _sort_by(self, col: str) -> None:
        """Toggle column sort order and notify listener."""
        if self.sort_col == col:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_col = col
            self.sort_asc = True

        arrow = "↑" if self.sort_asc else "↓"
        col_names = {
            "name": "Name",
            "path": "Path",
            "size": "Size",
            "type": "Type",
            "modified": "Date Modified",
        }
        for c, text in col_names.items():
            header_text = f"{text} {arrow}" if c == col else text
            self.tree.heading(c, text=header_text)

        if self.on_sort_changed:
            self.on_sort_changed(self.sort_col, self.sort_asc)

    def _on_selection(self, event) -> None:
        """Handle row selection change."""
        if self.on_selection_changed:
            item = self.get_selected_item()
            self.on_selection_changed(item)

    def _on_double_click(self, event) -> None:
        """Open item on double click."""
        item = self.get_selected_item()
        if item and "path" in item:
            file_service.open_item(item["path"])

    def _on_return_pressed(self, event) -> str:
        """Open item on Enter."""
        item = self.get_selected_item()
        if item and "path" in item:
            file_service.open_item(item["path"])
        return "break"

    def _on_ctrl_return_pressed(self, event) -> str:
        """Reveal in Explorer on Ctrl+Enter."""
        item = self.get_selected_item()
        if item and "path" in item:
            file_service.reveal_in_explorer(item["path"])
        return "break"

    def _on_copy_pressed(self, event) -> str:
        """Copy path on Ctrl+C."""
        selected = self.get_all_selected_items()
        if selected:
            paths = [s["path"] for s in selected if "path" in s]
            clipboard_service.copy_paths(paths, self)
        return "break"

    def _on_delete_pressed(self, event) -> str:
        """Delete selected items on Delete key."""
        item = self.get_selected_item()
        if item:
            self._handle_delete_request(item)
        return "break"

    def _on_f2_pressed(self, event) -> str:
        """Trigger rename on F2."""
        item = self.get_selected_item()
        if item:
            self._handle_rename_request(item)
        return "break"

    def _on_alt_return_pressed(self, event) -> str:
        """Show properties on Alt+Enter."""
        item = self.get_selected_item()
        if item and "path" in item:
            shell_service.show_file_properties(item["path"])
        return "break"

    def _on_right_click(self, event) -> None:
        """Open context menu at mouse position."""
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self.tree.focus(row_id)
            item = self._item_map.get(row_id)
            if item:
                self.context_menu.show(event, item)

    def _handle_delete_request(self, item: Dict[str, Any]) -> None:
        """Move item to Recycle Bin and remove row from view."""
        path = item.get("path")
        if path and file_service.delete_to_recycle_bin(path):
            row_id = str(item.get("id"))
            if row_id in self.tree.get_children():
                self.tree.delete(row_id)
            if row_id in self._item_map:
                del self._item_map[row_id]

    def _handle_rename_request(self, item: Dict[str, Any]) -> None:
        """Show inline or dialog prompt to rename file."""
        from tkinter import simpledialog
        old_name = item.get("name", "")
        old_path = item.get("path", "")
        new_name = simpledialog.askstring("Rename", f"Enter new name for '{old_name}':", initialvalue=old_name)
        if new_name and new_name != old_name:
            new_path = file_service.rename_item(old_path, new_name)
            if new_path:
                item["name"] = new_name
                item["path"] = new_path
                row_id = str(item.get("id"))
                if row_id in self.tree.get_children():
                    self.tree.item(row_id, values=(new_name, new_path, self.tree.item(row_id)["values"][2], item.get("type_desc"), self.tree.item(row_id)["values"][4]))
