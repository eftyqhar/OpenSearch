"""
OpenSearch by DeepLogic — File Metadata and Category Mapping
Maps file extensions to high-level search categories (Documents, Images, etc.)
and descriptive type strings (e.g. 'PDF Document', 'Python File', 'File folder').
"""

from __future__ import annotations
from typing import Dict, Set

# Extension to high-level category mapping
CATEGORIES: Dict[str, Set[str]] = {
    "document": {
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "rtf",
        "odt", "ods", "odp", "csv", "tsv", "md", "markdown", "epub", "log"
    },
    "image": {
        "jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico", "tiff",
        "tif", "psd", "ai", "raw", "cr2", "nef", "heic", "avif"
    },
    "video": {
        "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v", "mpg",
        "mpeg", "3gp", "ts", "vob"
    },
    "audio": {
        "mp3", "wav", "flac", "aac", "ogg", "wma", "m4a", "opus", "mid",
        "midi", "alac", "aiff"
    },
    "archive": {
        "zip", "rar", "7z", "tar", "gz", "bz2", "xz", "iso", "cab", "dmg",
        "tgz", "zst"
    },
    "executable": {
        "exe", "msi", "bat", "cmd", "ps1", "vbs", "com", "scr", "jar", "appx"
    },
    "code": {
        "py", "js", "ts", "html", "css", "c", "cpp", "h", "hpp", "cs", "java",
        "go", "rs", "php", "rb", "swift", "kt", "sql", "json", "xml", "yaml",
        "yml", "sh", "lua", "dart", "vue", "jsx", "tsx", "scala"
    },
}

# User-friendly descriptions for common extensions
EXTENSION_DESCRIPTIONS: Dict[str, str] = {
    "": "File",
    "pdf": "PDF Document",
    "doc": "DOC Document",
    "docx": "DOCX Document",
    "xls": "Excel Spreadsheet",
    "xlsx": "Excel Spreadsheet",
    "ppt": "PowerPoint Presentation",
    "pptx": "PowerPoint Presentation",
    "txt": "Text Document",
    "rtf": "Rich Text Document",
    "csv": "CSV File",
    "json": "JSON File",
    "xml": "XML File",
    "yaml": "YAML File",
    "yml": "YAML File",
    "md": "Markdown Document",
    "markdown": "Markdown Document",
    "log": "Log File",
    "jpg": "JPEG Image",
    "jpeg": "JPEG Image",
    "png": "PNG Image",
    "gif": "GIF Image",
    "bmp": "Bitmap Image",
    "webp": "WebP Image",
    "svg": "Vector Image",
    "ico": "Icon File",
    "mp4": "MP4 Video",
    "mkv": "MKV Video",
    "avi": "AVI Video",
    "mov": "QuickTime Video",
    "wmv": "Windows Media Video",
    "webm": "WebM Video",
    "mp3": "MP3 Audio",
    "wav": "WAV Audio",
    "flac": "FLAC Audio",
    "m4a": "M4A Audio",
    "zip": "ZIP Archive",
    "rar": "RAR Archive",
    "7z": "7-Zip Archive",
    "tar": "TAR Archive",
    "gz": "GZ Archive",
    "iso": "Disk Image",
    "exe": "Application",
    "msi": "Windows Installer",
    "bat": "Batch Script",
    "cmd": "Command Script",
    "ps1": "PowerShell Script",
    "py": "Python File",
    "js": "JavaScript File",
    "ts": "TypeScript File",
    "html": "HTML Document",
    "css": "CSS Stylesheet",
    "c": "C Source File",
    "cpp": "C++ Source File",
    "h": "Header File",
    "hpp": "C++ Header File",
    "cs": "C# Source File",
    "java": "Java Source File",
    "go": "Go Source File",
    "rs": "Rust Source File",
    "sql": "SQL Script",
    "db": "Database File",
    "sqlite": "SQLite Database",
    "sqlite3": "SQLite Database",
    "dll": "Dynamic Link Library",
    "sys": "System File",
    "ini": "Configuration File",
    "cfg": "Configuration File",
}


def get_file_category(extension: str, is_dir: bool = False) -> str:
    """Determine the high-level category of a file by extension."""
    if is_dir:
        return "folder"
    ext = extension.lower().lstrip(".")
    for category, ext_set in CATEGORIES.items():
        if ext in ext_set:
            return category
    return "other"


def get_type_description(extension: str, is_dir: bool = False) -> str:
    """Get a clean Windows-style type description (e.g., 'File folder', 'PDF Document')."""
    if is_dir:
        return "File folder"
    ext = extension.lower().lstrip(".")
    if ext in EXTENSION_DESCRIPTIONS:
        return EXTENSION_DESCRIPTIONS[ext]
    if ext:
        return f"{ext.upper()} File"
    return "File"
