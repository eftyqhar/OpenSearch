"""
OpenSearch by DeepLogic — Clipboard Service
Provides text and file path copying for Windows clipboard.
"""

from __future__ import annotations
import tkinter as tk
from typing import List
from utils.logger import logger


class ClipboardService:
    """Manages clipboard interactions."""

    @staticmethod
    def copy_text(text: str, root_widget: Optional[tk.Widget] = None) -> bool:
        """Copy a plain text string to the system clipboard."""
        try:
            if root_widget is not None:
                root_widget.clipboard_clear()
                root_widget.clipboard_append(text)
                root_widget.update()  # Finalize clipboard update
                return True
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
        return False

    @staticmethod
    def copy_paths(paths: List[str], root_widget: Optional[tk.Widget] = None) -> bool:
        """Copy one or multiple file paths separated by newlines."""
        if not paths:
            return False
        text = "\n".join(paths)
        return ClipboardService.copy_text(text, root_widget)


clipboard_service = ClipboardService()
