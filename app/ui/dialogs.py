"""Themed modal dialogs. CustomTkinter ships no messagebox replacement, so the
native `tkinter.messagebox` (old-style) is replaced here with CTk dialogs that
follow the matrix theme. The native file dialogs (`filedialog`) stay system-
provided, since theming those is not possible.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ..i18n import _


class _Dialog(ctk.CTkToplevel):
    """Modal themed dialog: title + wrapping message + a button row."""

    def __init__(self, parent, title: str, message: str, buttons: list[tuple[str, object]]):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result: object | None = None
        self.transient(parent)

        self._build(message, buttons)
        self._center_over(parent)
        self.grab_set()

    def _build(self, message: str, buttons: list[tuple[str, object]]) -> None:
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(frame, text=self.title(), font=("TkDefaultFont", 13, "bold")).pack(
            anchor="w", pady=(0, 8)
        )
        ctk.CTkLabel(frame, text=message, wraplength=380, justify="left", anchor="w").pack(
            fill="x", pady=(0, 14)
        )

        button_row = ctk.CTkFrame(frame, fg_color="transparent")
        button_row.pack(fill="x")
        for i, (label, value) in enumerate(buttons):
            if i > 0:
                # Non-primary buttons render as a muted outline style.
                btn = ctk.CTkButton(
                    button_row,
                    text=label,
                    width=100,
                    fg_color="transparent",
                    border_width=2,
                    border_color="#008F11",
                    text_color="#00FF00",
                    hover_color="#003B00",
                    command=lambda v=value: self._finish(v),
                )
            else:
                btn = ctk.CTkButton(
                    button_row, text=label, width=100, command=lambda v=value: self._finish(v)
                )
            btn.pack(side="right", padx=(6, 0) if i > 0 else (0, 0))

    def _center_over(self, parent) -> None:
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _finish(self, value: object) -> None:
        self.result = value
        self.destroy()


def ask_yes_no(parent, title: str, message: str) -> bool:
    """Themed Yes/No confirmation (blocks like tkinter.messagebox)."""
    dialog = _Dialog(parent, title, message, [(_("dialog.yes"), True), (_("dialog.no"), False)])
    parent.wait_window(dialog)
    return bool(dialog.result)


def show_info(parent, title: str, message: str) -> None:
    """Themed info box with a single OK button."""
    dialog = _Dialog(parent, title, message, [(_("dialog.ok"), True)])
    parent.wait_window(dialog)


def show_error(parent, title: str, message: str) -> None:
    """Themed error box with a single OK button."""
    dialog = _Dialog(parent, title, message, [(_("dialog.ok"), True)])
    parent.wait_window(dialog)
