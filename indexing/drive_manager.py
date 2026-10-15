"""
OpenSearch by DeepLogic — Windows Drive Detection & Management
Uses native Win32 ctypes APIs to detect drives, volume labels, drive types, and capacities.
"""

from __future__ import annotations
import ctypes
import os
import string
from dataclasses import dataclass
from typing import List, Optional
from utils.logger import logger

# Win32 Drive Type Constants
DRIVE_UNKNOWN = 0
DRIVE_NO_ROOT_DIR = 1
DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3
DRIVE_REMOTE = 4
DRIVE_CDROM = 5
DRIVE_RAMDISK = 6

DRIVE_TYPE_NAMES = {
    DRIVE_UNKNOWN: "Unknown",
    DRIVE_NO_ROOT_DIR: "Invalid",
    DRIVE_REMOVABLE: "Removable",
    DRIVE_FIXED: "Local Disk",
    DRIVE_REMOTE: "Network Drive",
    DRIVE_CDROM: "Optical Drive",
    DRIVE_RAMDISK: "RAM Disk",
}


@dataclass
class DriveInfo:
    """Represents a Windows storage drive."""
    letter: str  # e.g., 'C:'
    root: str    # e.g., 'C:\\'
    drive_type_id: int
    drive_type_name: str
    label: str
    filesystem: str
    total_bytes: int
    free_bytes: int

    @property
    def is_fixed(self) -> bool:
        return self.drive_type_id == DRIVE_FIXED

    @property
    def is_removable(self) -> bool:
        return self.drive_type_id == DRIVE_REMOVABLE

    @property
    def is_accessible(self) -> bool:
        return self.drive_type_id not in (DRIVE_UNKNOWN, DRIVE_NO_ROOT_DIR)


class DriveManager:
    """Detects and inspects Windows logical drives."""

    @staticmethod
    def get_available_drives() -> List[DriveInfo]:
        """Query Windows kernel32 for all logical drives."""
        drives: List[DriveInfo] = []
        if os.name != "nt":
            # Fallback for non-Windows development
            return [
                DriveInfo(
                    letter="C:",
                    root="C:\\",
                    drive_type_id=DRIVE_FIXED,
                    drive_type_name="Local Disk",
                    label="OS",
                    filesystem="NTFS",
                    total_bytes=512 * 1024 * 1024 * 1024,
                    free_bytes=256 * 1024 * 1024 * 1024,
                )
            ]

        try:
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for idx, char in enumerate(string.ascii_uppercase):
                if bitmask & (1 << idx):
                    letter = f"{char}:"
                    root = f"{char}:\\"
                    drive_type = ctypes.windll.kernel32.GetDriveTypeW(root)

                    volume_name = ctypes.create_unicode_buffer(261)
                    fs_name = ctypes.create_unicode_buffer(261)
                    ctypes.windll.kernel32.GetVolumeInformationW(
                        root,
                        volume_name,
                        ctypes.sizeof(volume_name),
                        None,
                        None,
                        None,
                        fs_name,
                        ctypes.sizeof(fs_name),
                    )

                    free_bytes = ctypes.c_ulonglong(0)
                    total_bytes = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        root,
                        None,
                        ctypes.byref(total_bytes),
                        ctypes.byref(free_bytes),
                    )

                    label = volume_name.value or (
                        "Local Disk" if drive_type == DRIVE_FIXED else "Removable Disk"
                    )

                    info = DriveInfo(
                        letter=letter,
                        root=root,
                        drive_type_id=drive_type,
                        drive_type_name=DRIVE_TYPE_NAMES.get(drive_type, "Unknown"),
                        label=label,
                        filesystem=fs_name.value or "NTFS",
                        total_bytes=total_bytes.value,
                        free_bytes=free_bytes.value,
                    )
                    drives.append(info)
        except Exception as e:
            logger.error(f"Error querying Windows logical drives: {e}")

        return drives


drive_manager = DriveManager()
