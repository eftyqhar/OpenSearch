"""
OpenSearch by DeepLogic — Global Windows Hotkey Service
Uses RegisterHotKey Win32 API in a dedicated background message loop thread to summon OpenSearch.
"""

from __future__ import annotations
import os
import ctypes
from ctypes import wintypes
import threading
from typing import Callable, Optional
from utils.logger import logger

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
VK_SPACE = 0x20
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012


class HotkeyService:
    """Manages system-wide global hotkeys."""

    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._callback: Optional[Callable[[], None]] = None
        self._running = False
        self._hotkey_id = 1001

    def start(self, callback: Callable[[], None]) -> None:
        """Start listening for Ctrl+Shift+Space in background thread."""
        if os.name != "nt" or self._running:
            return
        self._callback = callback
        self._running = True
        self._thread = threading.Thread(target=self._hotkey_loop, name="GlobalHotkeyThread", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop hotkey listener and unregister."""
        if not self._running:
            return
        self._running = False
        if self._thread_id:
            try:
                ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            except Exception:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info("Global hotkey service stopped.")

    def _hotkey_loop(self) -> None:
        """Win32 message loop listening for WM_HOTKEY."""
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()

        # Register Ctrl + Shift + Space
        modifiers = MOD_CONTROL | MOD_SHIFT
        registered = ctypes.windll.user32.RegisterHotKey(None, self._hotkey_id, modifiers, VK_SPACE)
        if not registered:
            logger.warning("Could not register global hotkey Ctrl+Shift+Space (may be in use by another app).")
            return

        logger.info("Registered global hotkey Ctrl+Shift+Space.")
        msg = wintypes.MSG()
        try:
            while self._running:
                ret = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret == 0 or ret == -1:
                    break
                if msg.message == WM_HOTKEY and msg.wParam == self._hotkey_id:
                    if self._callback:
                        try:
                            self._callback()
                        except Exception as e:
                            logger.error(f"Error in hotkey callback: {e}")
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            ctypes.windll.user32.UnregisterHotKey(None, self._hotkey_id)


hotkey_service = HotkeyService()
