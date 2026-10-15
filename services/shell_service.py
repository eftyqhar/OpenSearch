"""
OpenSearch by DeepLogic — Windows Shell Integration
Invokes native Windows Explorer dialogs such as the genuine File Properties window.
"""

from __future__ import annotations
import os
import ctypes
from ctypes import wintypes
from utils.logger import logger

SEE_MASK_INVOKEIDLIST = 0x0000000C
SW_SHOW = 5


class SHELLEXECUTEINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("fMask", wintypes.ULONG),
        ("hwnd", wintypes.HWND),
        ("lpVerb", wintypes.LPCWSTR),
        ("lpFile", wintypes.LPCWSTR),
        ("lpParameters", wintypes.LPCWSTR),
        ("lpDirectory", wintypes.LPCWSTR),
        ("nShow", ctypes.c_int),
        ("hInstApp", wintypes.HINSTANCE),
        ("lpIDList", wintypes.LPVOID),
        ("lpClass", wintypes.LPCWSTR),
        ("hkeyClass", wintypes.HKEY),
        ("dwHotKey", wintypes.DWORD),
        ("hIconOrMonitor", wintypes.HANDLE),
        ("hProcess", wintypes.HANDLE),
    ]


class ShellService:
    """Invokes Win32 Shell APIs."""

    @staticmethod
    def show_file_properties(path: str) -> bool:
        """Launch the authentic Windows Properties dialog for the specified path."""
        if os.name != "nt" or not os.path.exists(path):
            return False

        try:
            norm_path = os.path.normpath(path)
            sei = SHELLEXECUTEINFO()
            sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
            sei.fMask = SEE_MASK_INVOKEIDLIST
            sei.hwnd = None
            sei.lpVerb = "properties"
            sei.lpFile = norm_path
            sei.lpParameters = None
            sei.lpDirectory = None
            sei.nShow = SW_SHOW

            ret = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
            return bool(ret)
        except Exception as e:
            logger.error(f"Error launching file properties dialog for '{path}': {e}")
            return False


shell_service = ShellService()
