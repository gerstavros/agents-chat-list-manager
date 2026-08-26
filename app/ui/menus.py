"""Themed popup (context) menu. CustomTkinter has no menu widget, and the
classic `tk.Menu` cannot do rounded corners or per-item padding — so the
context menu is a small `overrideredirect` CTk window: rounded frame, padded
themed buttons, grab-based dismissal.

Behavior notes:
- Items only activate on an explicit left-click (posting on ButtonPress means
  releasing the right button never triggers the first item).
- The palette follows the active CTk appearance mode (light/dark) — resolved
  from the custom theme's `DropdownMenu` section at open time.
- The menu closes when the pointer leaves its bounds. This is what makes
  "click outside" work reliably on every platform: on Wayland (KDE), a global
  X grab never sees clicks on native windows or on the window-manager title
  bar, so a grab alone leaves the menu stuck open. A lightweight pointer poll
  covers those cases — wherever the click lands, the pointer ends up outside
  the menu rectangle. A local grab is kept for in-app behavior: clicks
  inside the app are absorbed (they never leak into the widget below) and
  Escape is routed to the menu while it is open. There is no <Button-1>
  binding on the toplevel — CTkButton items fire on release, and a press
  binding would destroy the menu before the release reaches the button.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

_RADIUS = 2
_POLL_MS = 80
_LEAVE_MARGIN = 4  # px of slack so an open menu does not close on a wobble


def _palette() -> dict[str, str]:
    """Resolve the active appearance mode's menu colors from the theme JSON."""
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
        "bg": pick("DropdownMenu", "fg_color", "#001400"),
        "hover": pick("DropdownMenu", "hover_color", "#003B00"),
        "text": pick("DropdownMenu", "text_color", "#00FF00"),
        "border": pick("CTkFrame", "border_color", "#005C00"),
    }


class ContextMenu(ctk.CTkToplevel):
    def __init__(self, parent, items: list[tuple[str, Callable[[], None]]]):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._poll_after_id: str | None = None

        palette = _palette()
        frame = ctk.CTkFrame(
            self,
            corner_radius=_RADIUS,
            fg_color=palette["bg"],
            border_width=1,
            border_color=palette["border"],
        )
        frame.pack(padx=6, pady=6)
        for label, command in items:
            btn = ctk.CTkButton(
                frame,
                text=label,
                corner_radius=_RADIUS,
                fg_color="transparent",
                hover_color=palette["hover"],
                text_color=palette["text"],
                anchor="w",
                width=180,
                height=34,
                command=lambda c=command: self._choose(c),
            )
            btn.pack(fill="x", padx=4, pady=2)

        # Escape closes the menu without activating anything. Note: there is
        # deliberately NO <Button-1> binding here — CustomTkinter buttons fire
        # their command on <ButtonRelease-1>, so a toplevel press binding would
        # destroy the menu before the release ever reaches the button, making
        # every item dead. All “click outside” dismissal is handled by the
        # pointer poll in `_check_pointer`, which also catches clicks on other
        # windows and on the WM title bar.
        for seq in ("<Button-2>", "<Button-3>"):
            self.bind(seq, lambda _e: self.close())
        self.bind("<Escape>", lambda _e: self.close())

    def show(self, x: int, y: int) -> None:
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        x = min(max(x, 0), self.winfo_screenwidth() - w - 4)
        y = min(max(y, 0), self.winfo_screenheight() - h - 4)
        self.geometry(f"+{x}+{y}")
        try:
            # Local grab: in-app events (clicks anywhere in the app, Escape)
            # are routed to the menu while it is open. Not global — clicks on
            # other applications must reach those applications untouched.
            self.grab_set()
        except Exception:
            pass
        self.lift()
        self._poll_after_id = self.after(_POLL_MS, self._check_pointer)

    def _check_pointer(self) -> None:
        """Close when the pointer leaves the menu rectangle. This catches
        clicks on other windows and on the WM title bar that never reach us
        as X events (especially under Wayland)."""
        try:
            if not self.winfo_exists():
                return
            px, py = self.winfo_pointerxy()
            if px < 0 or py < 0:  # off-screen / unknown — keep polling
                self._poll_after_id = self.after(_POLL_MS, self._check_pointer)
                return
            x0, y0 = self.winfo_rootx(), self.winfo_rooty()
            w, h = self.winfo_width(), self.winfo_height()
            inside = (
                x0 - _LEAVE_MARGIN <= px <= x0 + w + _LEAVE_MARGIN
                and y0 - _LEAVE_MARGIN <= py <= y0 + h + _LEAVE_MARGIN
            )
            if not inside:
                self.close()
                return
            self._poll_after_id = self.after(_POLL_MS, self._check_pointer)
        except Exception:
            pass

    def _choose(self, command: Callable[[], None]) -> None:
        self.close()
        command()

    def close(self) -> None:
        if self._poll_after_id is not None:
            try:
                self.after_cancel(self._poll_after_id)
            except Exception:
                pass
            self._poll_after_id = None
        try:
            if self.winfo_exists():
                self.grab_release()
                self.destroy()
        except Exception:
            pass
