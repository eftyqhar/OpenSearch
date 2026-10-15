"""
OpenSearch by DeepLogic — Right-Click Context Menu
Provides clean, native-styled context menu for search results with standard Windows operations.
"""

from __future__ import annotations
import tkinter as tk
from typing import List, Dict, Any, Callable, Optional
from services.file_service import file_service
from services.clipboard_service import clipboard_service
from services.shell_service import shell_service
from ui.theme import get_theme


class ResultContextMenu:
    """Popup context menu for search results."""

    def __init__(
        self,
        master: tk.Widget,
        on_rename_request: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_delete_request: Optional[Callable[[Dict[str, Any]], None]] = None,
        theme_name: str = "dark",
    ) -> None:
        self.master = master
        self.on_rename_request = on_rename_request
        self.on_delete_request = on_delete_request
        self.theme = get_theme(theme_name)
        self.current_item: Optional[Dict[str, Any]] = None

        self.menu = tk.Menu(
            self.master,
            tearoff=0,
            bg=self.theme["card_bg"],
            fg=self.theme["text_primary"],
            activebackground=self.theme["accent_blue"],
            activeforeground="#FFFFFF",
            bd=1,
            relief="solid",
            font=("Segoe UI", 9),
        )

        self._build_menu()

    def _build_menu(self) -> None:
        """Construct menu items."""
        self.menu.add_command(label="Open", command=self._open_item)
        self.menu.add_command(label="Open Containing Folder", command=self._reveal_item)
        self.menu.add_separator()
        self.menu.add_command(label="Copy", command=self._copy_file)
        self.menu.add_command(label="Copy Path", command=self._copy_path)
        self.menu.add_separator()
        self.menu.add_command(label="Rename", command=self._rename_item)
        self.menu.add_command(label="Delete", command=self._delete_item)
        self.menu.add_separator()
        self.menu.add_command(label="Properties", command=self._show_properties)

    def show(self, event, item: Dict[str, Any]) -> None:
        """Display the context menu at mouse event position."""
        self.current_item = item
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _open_item(self) -> None:
        if self.current_item and "path" in self.current_item:
            file_service.open_item(self.current_item["path"])

    def _reveal_item(self) -> None:
        if self.current_item and "path" in self.current_item:
            file_service.reveal_in_explorer(self.current_item["path"])

    def _copy_file(self) -> None:
        if self.current_item and "path" in self.current_item:
            clipboard_service.copy_paths([self.current_item["path"]], self.master)

    def _copy_path(self) -> None:
        if self.current_item and "path" in self.current_item:
            clipboard_service.copy_text(self.current_item["path"], self.master)

    def _rename_item(self) -> None:
        if self.current_item and self.on_rename_request:
            self.on_rename_request(self.current_item)

    def _delete_item(self) -> None:
        if self.current_item:
            if self.on_delete_request:
                self.on_delete_request(self.current_item)
            else:
                file_service.delete_to_recycle_bin(self.current_item["path"])

    def _show_properties(self) -> None:
        if self.current_item and "path" in self.current_item:
            shell_service.show_file_properties(self.current_item["path"])
