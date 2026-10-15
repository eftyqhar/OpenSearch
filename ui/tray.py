"""
OpenSearch by DeepLogic — System Tray Integration
Manages Windows notification area tray icon and menu (Open, Pause/Resume, Settings, Exit).
"""

from __future__ import annotations
import threading
from typing import Callable, Optional
from PIL import Image
import pystray
from utils.icons import draw_app_logo
from utils.logger import logger
from indexing.index_worker import index_worker


class SystemTrayManager:
    """Manages pystray system tray icon in a dedicated background thread."""

    def __init__(
        self,
        on_open_clicked: Callable[[], None],
        on_settings_clicked: Callable[[], None],
        on_exit_clicked: Callable[[], None],
    ) -> None:
        self.on_open_clicked = on_open_clicked
        self.on_settings_clicked = on_settings_clicked
        self.on_exit_clicked = on_exit_clicked
        self.icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the system tray icon in a background thread."""
        if self.icon is not None:
            return
        image = draw_app_logo(32)
        menu = pystray.Menu(
            pystray.MenuItem("Open OpenSearch", lambda: self.on_open_clicked(), default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Pause Indexing",
                lambda: index_worker.pause(),
                visible=lambda item: index_worker.is_indexing,
            ),
            pystray.MenuItem(
                "Resume Indexing",
                lambda: index_worker.resume(),
                visible=lambda item: index_worker.is_paused,
            ),
            pystray.MenuItem("Settings", lambda: self.on_settings_clicked()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", lambda: self.on_exit_clicked()),
        )

        self.icon = pystray.Icon(
            name="OpenSearch",
            icon=image,
            title="OpenSearch by DeepLogic",
            menu=menu,
        )

        self._thread = threading.Thread(target=self.icon.run, name="TrayThread", daemon=True)
        self._thread.start()
        logger.info("System tray initialized.")

    def stop(self) -> None:
        """Remove tray icon."""
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
