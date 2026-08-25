"""Bridge CustomTkinter's active theme colors into the ttk widgets the app
still needs. CustomTkinter has no table widget, so the conversation list keeps
ttk.Treeview, and the split layout keeps ttk.PanedWindow — this module styles
both to visually match the active CTk appearance mode (light/dark).

Theme colors are read from CustomTkinter's ThemeManager (list values are
[light, dark] pairs) rather than hardcoded, so the ttk pieces track the same
palette as the CTk widgets.
"""

from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk

TREEVIEW_STYLE = "AgentChat.Treeview"
TREEVIEW_HEADING_STYLE = "AgentChat.Treeview.Heading"
# ttk.PanedWindow's widget class is TPanedwindow (capital T) — a style must
# match "<prefix>.<class>", otherwise Tk fails with "Layout ... not found".
PANED_STYLE = "AgentChat.TPanedwindow"


def active_ctk_colors() -> dict[str, str]:
    """Resolve the current appearance mode's palette into plain hex strings."""
    theme = ctk.ThemeManager.theme
    idx = 0 if ctk.get_appearance_mode() == "Light" else 1

    def pick(table: str, key: str, fallback: str) -> str:
        val = theme.get(table, {}).get(key)
        if isinstance(val, list) and len(val) == 2:
            return str(val[idx])
        if isinstance(val, str):
            return val
        return fallback

    return {
        "bg": pick("CTkFrame", "fg_color", "#EBEBEB"),
        "panel": pick("CTkEntry", "fg_color", "#F9F9FA"),
        "text": pick("CTkTextbox", "text_color", "#1A1A1A"),
        "accent": pick("CTkButton", "fg_color", "#3B8ED0"),
        "accent_text": pick("CTkButton", "text_color", "#FFFFFF"),
        "border": pick("CTkEntry", "border_color", "#979DA2"),
    }


def apply_ttk_theme(root) -> None:
    """Style the ttk.Treeview to match the active CTk palette."""
    colors = active_ctk_colors()
    style = ttk.Style(root)
    style.theme_use("clam")  # fully themeable across platforms

    style.configure(
        TREEVIEW_STYLE,
        background=colors["panel"],
        fieldbackground=colors["panel"],
        foreground=colors["text"],
        borderwidth=0,
        rowheight=26,
        font=("TkDefaultFont", 10),
    )
    style.map(
        TREEVIEW_STYLE,
        background=[("selected", colors["accent"])],
        foreground=[("selected", colors["accent_text"])],
    )
    style.configure(
        TREEVIEW_HEADING_STYLE,
        background=colors["bg"],
        foreground=colors["text"],
        relief="flat",
        padding=(6, 5),
        font=("TkDefaultFont", 10, "bold"),
    )
    style.map(TREEVIEW_HEADING_STYLE, background=[("active", colors["border"])])


def apply_paned_theme(paned: ttk.PanedWindow) -> None:
    """Style the PanedWindow sash to blend with the CTk background."""
    colors = active_ctk_colors()
    style = ttk.Style(paned)
    style.configure(PANED_STYLE, background=colors["bg"], sashwidth=6)
    paned.configure(style=PANED_STYLE)
