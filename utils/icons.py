"""
OpenSearch by DeepLogic — Icon Generation & Cache
Generates crisp, anti-aliased, modern Windows 11 style UI and file-type icons using PIL.
Ensures zero external asset dependencies, crisp DPI rendering, and high performance.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageTk
import customtkinter as ctk
from utils.paths import get_assets_dir, get_app_root
from utils.logger import logger

_ICON_CACHE: Dict[str, ctk.CTkImage] = {}
_TK_ICON_CACHE: Dict[str, ImageTk.PhotoImage] = {}


def create_rounded_rect(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], radius: int, fill: str, outline: Optional[str] = None):
    """Draw a smooth rounded rectangle."""
    x0, y0, x1, y1 = box
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline)


def draw_app_logo(size: int = 64) -> Image.Image:
    """Generate the official OpenSearch logo (stylized magnifying glass with deep blue accent)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Blue gradient circle background
    margin = size * 0.08
    center_x = size * 0.44
    center_y = size * 0.44
    radius = size * 0.30

    # Glass ring
    ring_color = (37, 99, 235, 255)  # #2563EB primary blue
    handle_color = (59, 130, 246, 255)  # #3B82F6 lighter blue

    # Lens outer
    width = max(2, int(size * 0.10))
    draw.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        outline=ring_color,
        width=width,
    )

    # Inner lens glow
    inner_r = radius * 0.70
    draw.ellipse(
        [center_x - inner_r, center_y - inner_r, center_x + inner_r, center_y + inner_r],
        fill=(30, 58, 138, 70),
    )

    # Handle (angled line)
    h_start_x = center_x + radius * 0.70
    h_start_y = center_y + radius * 0.70
    h_end_x = size * 0.88
    h_end_y = size * 0.88
    draw.line([h_start_x, h_start_y, h_end_x, h_end_y], fill=handle_color, width=int(width * 1.3))

    return img


def draw_file_icon(icon_type: str, size: int = 18) -> Image.Image:
    """Generate crisp modern file-type and folder icons."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    s = size
    if icon_type == "folder":
        # Amber/Yellow folder icon
        # Back tab
        draw.rectangle([s * 0.15, s * 0.20, s * 0.50, s * 0.45], fill=(217, 119, 6, 255))
        # Front folder
        create_rounded_rect(draw, (int(s * 0.10), int(s * 0.35), int(s * 0.90), int(s * 0.85)), radius=2, fill=(245, 158, 11, 255))
        return img

    # Standard document sheet shape
    sheet_left = int(s * 0.22)
    sheet_top = int(s * 0.12)
    sheet_right = int(s * 0.78)
    sheet_bottom = int(s * 0.88)
    fold_size = int(s * 0.22)

    # Determine badge color based on file type
    colors = {
        "pdf": ((239, 68, 68, 255), "PDF"),       # Red
        "docx": ((37, 99, 235, 255), "DOC"),      # Blue
        "doc": ((37, 99, 235, 255), "DOC"),
        "txt": ((148, 163, 184, 255), "TXT"),     # Gray
        "mp4": ((168, 85, 247, 255), "VID"),      # Purple
        "image": ((6, 182, 212, 255), "IMG"),     # Cyan
        "archive": ((245, 158, 11, 255), "ZIP"),  # Amber
        "code": ((16, 185, 129, 255), "</>"),     # Green
        "python": ((59, 130, 246, 255), "PY"),    # Python Blue
        "exe": ((14, 165, 233, 255), "APP"),      # Application Teal
        "db": ((99, 102, 241, 255), "DB"),        # Database Indigo
        "file": ((100, 116, 139, 255), ""),
    }

    fill_color, text_code = colors.get(icon_type, ((100, 116, 139, 255), ""))

    # White page base
    create_rounded_rect(draw, (sheet_left, sheet_top, sheet_right, sheet_bottom), radius=2, fill=(241, 245, 249, 255))
    # Fold corner
    draw.polygon(
        [(sheet_right - fold_size, sheet_top), (sheet_right, sheet_top + fold_size), (sheet_right - fold_size, sheet_top + fold_size)],
        fill=(203, 213, 225, 255),
    )
    # Colored accent badge on lower half
    draw.rectangle([sheet_left, int(s * 0.52), sheet_right, sheet_bottom], fill=fill_color)

    return img


def get_tk_file_icon(icon_type: str, size: int = 18) -> ImageTk.PhotoImage:
    """Retrieve or cache Tkinter PhotoImage for Treeview rows."""
    key = f"tk_{icon_type}_{size}"
    if key not in _TK_ICON_CACHE:
        img = draw_file_icon(icon_type, size)
        _TK_ICON_CACHE[key] = ImageTk.PhotoImage(img)
    return _TK_ICON_CACHE[key]


def get_ctk_icon(icon_type: str, size: int = 20) -> ctk.CTkImage:
    """Retrieve or cache CustomTkinter CTkImage."""
    key = f"ctk_{icon_type}_{size}"
    if key not in _ICON_CACHE:
        if icon_type == "logo":
            img = draw_app_logo(size * 2)
        else:
            img = draw_file_icon(icon_type, size * 2)
        _ICON_CACHE[key] = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    return _ICON_CACHE[key]


def map_ext_to_icon_type(ext: str, is_dir: bool) -> str:
    """Map extension and is_dir flag to icon key."""
    if is_dir:
        return "folder"
    ext_clean = ext.lower().lstrip(".")
    if ext_clean == "pdf":
        return "pdf"
    if ext_clean in ("doc", "docx"):
        return "docx"
    if ext_clean in ("txt", "rtf", "md", "log"):
        return "txt"
    if ext_clean in ("mp4", "mkv", "avi", "mov", "webm"):
        return "mp4"
    if ext_clean in ("png", "jpg", "jpeg", "gif", "webp", "svg", "bmp"):
        return "image"
    if ext_clean in ("zip", "rar", "7z", "tar", "gz"):
        return "archive"
    if ext_clean in ("py", "pyw"):
        return "python"
    if ext_clean in ("json", "js", "ts", "html", "css", "c", "cpp", "java", "rs"):
        return "code"
    if ext_clean in ("exe", "msi", "bat", "cmd"):
        return "exe"
    if ext_clean in ("db", "sqlite", "sqlite3", "sql"):
        return "db"
    return "file"


def ensure_ico_asset() -> Path:
    """Generate and save Windows .ico file for executable and window title bar."""
    assets_dir = get_assets_dir() / "icons"
    assets_dir.mkdir(parents=True, exist_ok=True)
    ico_path = assets_dir / "opensearch.ico"
    if not ico_path.exists():
        try:
            # Generate multi-size ICO
            sizes = [16, 32, 48, 64, 128, 256]
            images = [draw_app_logo(s) for s in sizes]
            images[0].save(ico_path, format="ICO", sizes=[(s, s) for s in sizes])
            logger.info(f"Saved application icon to {ico_path}")
        except Exception as e:
            logger.warning(f"Could not write .ico file: {e}")
    return ico_path
