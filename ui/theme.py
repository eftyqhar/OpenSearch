"""
OpenSearch by DeepLogic — Theme and Design System
Faithfully defines the exact typography, color palettes, spacing, and widget styles
matching the modern Windows 11 OpenSearch desktop interface.
"""

from __future__ import annotations
from typing import Dict, Any

THEMES: Dict[str, Dict[str, Any]] = {
    "dark": {
        "bg": "#0B0E14",
        "sidebar_bg": "#0F131C",
        "card_bg": "#131822",
        "card_border": "#1F2633",
        "search_bg": "#131822",
        "search_border": "#242C3D",
        "search_focus_border": "#2563EB",

        "text_primary": "#F8FAFC",
        "text_secondary": "#8E95A5",
        "text_muted": "#64748B",

        "accent_blue": "#1668E8",
        "accent_blue_hover": "#2563EB",
        "accent_blue_light": "#1E3A8A",

        "chip_bg": "#161B26",
        "chip_border": "#242C3D",
        "chip_active_bg": "#1668E8",
        "chip_active_text": "#FFFFFF",

        "table_bg": "#0B0E14",
        "table_alt_bg": "#0E121A",
        "table_header_bg": "#11151F",
        "table_header_fg": "#8E95A5",
        "table_row_fg": "#E2E8F0",
        "table_selected_bg": "#1E3A8A",
        "table_selected_fg": "#FFFFFF",
        "table_hover_bg": "#161D2B",
        "border": "#1F2633",
        "table_border": "#1F2633",

        "status_green": "#10B981",
        "status_amber": "#F59E0B",
        "status_red": "#EF4444",
    },
    "light": {
        "bg": "#F8FAFC",
        "sidebar_bg": "#F1F5F9",
        "card_bg": "#FFFFFF",
        "card_border": "#E2E8F0",
        "search_bg": "#FFFFFF",
        "search_border": "#CBD5E1",
        "search_focus_border": "#2563EB",

        "text_primary": "#0F172A",
        "text_secondary": "#64748B",
        "text_muted": "#94A3B8",

        "accent_blue": "#2563EB",
        "accent_blue_hover": "#1D4ED8",
        "accent_blue_light": "#DBEAFE",

        "chip_bg": "#F1F5F9",
        "chip_border": "#E2E8F0",
        "chip_active_bg": "#2563EB",
        "chip_active_text": "#FFFFFF",

        "table_bg": "#FFFFFF",
        "table_alt_bg": "#F8FAFC",
        "table_header_bg": "#F1F5F9",
        "table_header_fg": "#475569",
        "table_row_fg": "#0F172A",
        "table_selected_bg": "#DBEAFE",
        "table_selected_fg": "#1E3A8A",
        "table_hover_bg": "#F1F5F9",
        "table_border": "#E2E8F0",

        "status_green": "#059669",
        "status_amber": "#D97706",
        "status_red": "#DC2626",
    },
}


class ThemeDict(dict):
    def __missing__(self, key: str) -> str:
        return "#1F2633"


def get_theme(theme_name: str = "dark") -> Dict[str, Any]:
    """Retrieve color dictionary for specified theme."""
    base = dict(THEMES.get(theme_name.lower(), THEMES["dark"]))
    return ThemeDict(base)
