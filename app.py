"""
OpenSearch by DeepLogic — Application Entrypoint
Ultra-fast Windows desktop file and folder search utility.
"""

from __future__ import annotations
import sys
import os
import ctypes

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import db_manager
from ui.main_window import MainWindow
from utils.logger import logger


_app_mutex = None


def ensure_single_instance() -> bool:
    """Ensure only one instance of OpenSearch runs concurrently on Windows."""
    global _app_mutex
    if os.name != "nt":
        return True
    mutex_name = "Local\\DeepLogic_OpenSearch_SingleInstance_Mutex"
    try:
        _app_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
        last_error = ctypes.windll.kernel32.GetLastError()
        # ERROR_ALREADY_EXISTS = 183
        if last_error == 183:
            logger.warning("Another instance of OpenSearch is already running.")
            return False
    except Exception as e:
        logger.debug(f"Mutex creation note: {e}")
    return True


def main() -> None:
    """Launch OpenSearch desktop application."""
    logger.info("Starting OpenSearch by DeepLogic...")

    # Enable High DPI awareness on Windows
    if os.name == "nt":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_SYSTEM_DPI_AWARE
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    if not ensure_single_instance():
        logger.info("Exiting: instance already active.")
        sys.exit(0)

    try:
        # Initialize Database connection & tables
        db_manager.init_database()

        # Launch UI Window
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        logger.critical(f"Unhandled application exception: {e}", exc_info=True)
        try:
            import tkinter.messagebox as mb
            mb.showerror("OpenSearch Error", f"Failed to start OpenSearch:\n\n{e}\n\nCheck logs at %LOCALAPPDATA%\\OpenSearch\\logs")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
