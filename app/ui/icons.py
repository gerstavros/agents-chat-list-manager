"""Programmatic vector-style icons for the toolbar, drawn with Pillow's
ImageDraw at high resolution and downscaled by CTkImage (LANCZOS) for crisp
rendering on any display scale. No image files are shipped — the icons are
pure geometry, equivalent to simple SVG paths, so the PyInstaller bundle needs
no extra data files.

Icon color is a deep matrix green-black that matches the button text color
(buttons are bright green in both dark and light mode, so one color fits all).
"""

from __future__ import annotations

import math

import customtkinter as ctk
from PIL import Image, ImageDraw

_ICON_COLOR = "#001400"  # deep green-black, matches CTkButton text on green
_CANVAS = 128            # supersampled draw size; CTkImage scales down
_SIZE = (20, 20)


def _base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (_CANVAS, _CANVAS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _punch(img: Image.Image, box: tuple[int, int, int, int], radius: int = 0) -> None:
    """Make a transparent hole (rounded rect) in the icon — used for the trash
    slats and the gear centre, so the button color shows through."""
    mask = Image.new("L", (_CANVAS, _CANVAS), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    img.paste((0, 0, 0, 0), (0, 0), mask)


def _arrowhead(
    d: ImageDraw.ImageDraw, cx: float, radius: float, angle_deg: float, size: float
) -> None:
    """Triangle arrowhead on the ring at `angle_deg`, pointing along the
    clockwise direction of travel (screen coords, y down)."""
    a = math.radians(angle_deg)
    x = cx + radius * math.cos(a)
    y = cx + radius * math.sin(a)
    tx, ty = -math.sin(a), math.cos(a)  # tangent (clockwise travel)
    nx, ny = math.cos(a), math.sin(a)   # outward normal
    tip = (x + tx * size, y + ty * size)
    b1 = (x - tx * size * 0.45 + nx * size * 0.42, y - ty * size * 0.45 + ny * size * 0.42)
    b2 = (x - tx * size * 0.45 - nx * size * 0.42, y - ty * size * 0.45 - ny * size * 0.42)
    d.polygon([tip, b1, b2], fill=_ICON_COLOR)


def _to_ctk(img: Image.Image) -> ctk.CTkImage:
    # Buttons look identical in dark/light (both use the green accent), so the
    # same image is used for both appearance modes.
    return ctk.CTkImage(light_image=img, dark_image=img, size=_SIZE)


def refresh_icon() -> ctk.CTkImage:
    """Circular clockwise refresh arrow with a gap at the top."""
    img, d = _base()
    c = _CANVAS / 2
    r = _CANVAS * 0.34
    w = int(_CANVAS * 0.11)
    d.arc((c - r, c - r, c + r, c + r), start=315, end=225, fill=_ICON_COLOR, width=w)
    for angle in (225, 315):
        _arrowhead(d, c, r, angle, size=_CANVAS * 0.16)
    return _to_ctk(img)


def trash_icon() -> ctk.CTkImage:
    """Trash can: handle, lid, body with three cut-out slats."""
    img, d = _base()
    d.rounded_rectangle((44, 8, 84, 18), radius=4, fill=_ICON_COLOR)  # handle
    d.rounded_rectangle((20, 20, 108, 34), radius=4, fill=_ICON_COLOR)  # lid
    d.rounded_rectangle((30, 38, 98, 118), radius=8, fill=_ICON_COLOR)  # body
    _punch(img, (38, 54, 48, 102), radius=3)
    _punch(img, (55, 54, 65, 102), radius=3)
    _punch(img, (72, 54, 82, 102), radius=3)
    return _to_ctk(img)


def gear_icon() -> ctk.CTkImage:
    """Settings gear: ring with eight radial teeth and an open centre."""
    img, d = _base()
    c = _CANVAS / 2
    teeth_in = _CANVAS * 0.30
    teeth_out = _CANVAS * 0.44
    tooth_w = int(_CANVAS * 0.115)
    for i in range(8):
        a = math.radians(i * 45)
        x1 = c + teeth_in * math.cos(a)
        y1 = c + teeth_in * math.sin(a)
        x2 = c + teeth_out * math.cos(a)
        y2 = c + teeth_out * math.sin(a)
        d.line((x1, y1, x2, y2), fill=_ICON_COLOR, width=tooth_w)
    ring_r = _CANVAS * 0.325
    d.ellipse(
        (c - ring_r, c - ring_r, c + ring_r, c + ring_r),
        outline=_ICON_COLOR,
        width=int(_CANVAS * 0.115),
    )
    _punch(img, (int(c - _CANVAS * 0.13), int(c - _CANVAS * 0.13), int(c + _CANVAS * 0.13), int(c + _CANVAS * 0.13)), radius=0)
    return _to_ctk(img)


class Tooltip:
    """Minimal hover tooltip for icon-only buttons (CustomTkinter ships none).

    Shows a small dark-green label near the cursor after a short delay;
    hides on leave or click.
    """

    def __init__(self, widget, text: str, delay_ms: int = 400):
        self._widget = widget
        self._text = text
        self._delay_ms = delay_ms
        self._after_id: str | None = None
        self._tip: ctk.CTkToplevel | None = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, _event=None) -> None:
        self._cancel_pending()
        self._after_id = self._widget.after(self._delay_ms, self._show)

    def _show(self) -> None:
        if self._tip is not None:
            return
        x = self._widget.winfo_pointerx() + 14
        y = self._widget.winfo_pointery() + 12
        tip = ctk.CTkToplevel(self._widget)
        tip.overrideredirect(True)
        tip.attributes("-topmost", True)
        tip.geometry(f"+{x}+{y}")
        frame = ctk.CTkFrame(tip, fg_color="#003B00", corner_radius=4)
        frame.pack(padx=6, pady=4)
        ctk.CTkLabel(frame, text=self._text, text_color="#00FF00").pack()
        self._tip = tip

    def _hide(self, _event=None) -> None:
        self._cancel_pending()
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None

    def _cancel_pending(self) -> None:
        if self._after_id is not None:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
