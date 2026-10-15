"""
OpenSearch by DeepLogic — File Operations Service
Provides native Windows operations: Open, Reveal in File Explorer, Delete to Recycle Bin, and Rename.
"""

from __future__ import annotations
import os
import subprocess
from typing import Optional
from send2trash import send2trash
from database.repositories import file_repo
from utils.logger import logger


class FileService:
    """Manages filesystem interactions and standard shell operations."""

    @staticmethod
    def open_item(path: str) -> bool:
        """Launch file or directory using the default Windows association."""
        if not os.path.exists(path):
            logger.warning(f"Cannot open missing path: {path}")
            return False
        try:
            os.startfile(path)
            return True
        except Exception as e:
            logger.error(f"Error opening item '{path}': {e}")
            return False

    @staticmethod
    def reveal_in_explorer(path: str) -> bool:
        """Open Windows Explorer and highlight the specific file or directory."""
        if not os.path.exists(path):
            logger.warning(f"Cannot reveal missing path: {path}")
            return False
        try:
            norm_path = os.path.normpath(path)
            subprocess.Popen(["explorer.exe", f"/select,{norm_path}"])
            return True
        except Exception as e:
            logger.error(f"Error revealing item '{path}' in Explorer: {e}")
            return False

    @staticmethod
    def delete_to_recycle_bin(path: str) -> bool:
        """Move file or directory safely to Windows Recycle Bin."""
        if not os.path.exists(path):
            logger.warning(f"Cannot recycle missing path: {path}")
            return False
        try:
            send2trash(path)
            # Update index
            if os.path.isdir(path):
                file_repo.delete_by_prefix(path)
            else:
                file_repo.delete_by_path(path)
            logger.info(f"Sent to Recycle Bin: {path}")
            return True
        except Exception as e:
            logger.error(f"Error sending '{path}' to Recycle Bin: {e}")
            return False

    @staticmethod
    def rename_item(old_path: str, new_name: str) -> Optional[str]:
        """Rename file or folder and sync the database record."""
        if not os.path.exists(old_path):
            return None
        parent = os.path.dirname(old_path)
        new_path = os.path.join(parent, new_name)
        if os.path.exists(new_path):
            logger.warning(f"Cannot rename: destination '{new_path}' already exists.")
            return None

        try:
            is_dir = os.path.isdir(old_path)
            os.rename(old_path, new_path)
            if is_dir:
                file_repo.rename_directory(old_path, new_path, new_name, parent)
            else:
                ext = new_name.rsplit(".", 1)[-1].lower() if "." in new_name else ""
                file_repo.rename_file(old_path, new_path, new_name, parent, ext)
            logger.info(f"Renamed '{old_path}' to '{new_path}'")
            return new_path
        except Exception as e:
            logger.error(f"Error renaming '{old_path}' to '{new_path}': {e}")
            return None


file_service = FileService()
