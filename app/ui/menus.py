"""Themed popup (context) menu. CustomTkinter has no menu widget, and the
classic `tk.Menu` cannot do rounded corners or per-item padding — so the
context menu is a small `overrideredirect` CTk window: rounded frame, padded
themed buttons, grab-based dismissal.

Behavior notes:
- Items only activate on an explicit left-click (posting on ButtonPress means
  releasing the right button never triggers the first item).
- Clicking anywhere outside the menu (or pressing Escape) closes it without
  activating anything.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

_RADIUS = 2
_BG = "#001400"
_HOVER = "#003B00"
_BORDER = "#005C00"
_TEXT = "#00FF00"


class ContextMenu(ctk.CTkToplevel):
    def __init__(self, parent, items: list[tuple[str, Callable[[], None]]]):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        frame = ctk.CTkFrame(
            self, corner_radius=_RADIUS, fg_color=_BG, border_width=1, border_color=_BORDER
        )
        frame.pack(padx=6, pady=6)
        for i, (label, command) in enumerate(items):
            btn = ctk.CTkButton(
                frame,
                text=label,
                corner_radius=_RADIUS,
                fg_color="transparent",
                hover_color=_HOVER,
                text_color=_TEXT,
                anchor="w",
                width=180,
                height=34,
                command=lambda c=command: self._choose(c),
            )
            btn.pack(fill="x", padx=4, pady=2)

        # Click anywhere on the menu but not on an item, or Escape, closes it.
        # (Item clicks fire the item command first; the guard handles the
        # toplevel binding that also fires afterwards.)
        self.bind("<Button-1>", lambda _e: self.close())
        self.bind("<Escape>", lambda _e: self.close())

    def show(self, x: int, y: int) -> None:
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        x = min(max(x, 0), self.winfo_screenwidth() - w - 4)
        y = min(max(y, 0), self.winfo_screenheight() - h - 4)
        self.geometry(f"+{x}+{y}")
        self.grab_set()
        self.lift()

    def _choose(self, command: Callable[[], None]) -> None:
        self.close()
        command()

    def close(self) -> None:
        try:
            if self.winfo_exists():
                self.grab_release()
                self.destroy()
        except Exception:
            pass
